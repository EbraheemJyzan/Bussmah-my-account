import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class Request(models.AbstractModel):
    _name = "request"
    _description = "Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _group_by_full = {"stage_id": lambda s, *a, **k: s._read_group_stage_ids(*a, **k)}

    @api.model
    def _default_employee_id(self):
        employees = self.env["hr.employee"].search(
            [("user_id", "=", self._uid)], limit=1
        )
        return employees and employees[0]

    #   _default_stage_id was added because onchange of
    #   'branch' was triggering the default value of stage_id.
    @api.model
    def _default_stage_id(self):
        return self._get_next_stage(stage_type="default")

    name = fields.Char(string="Number", readonly=True)
    stage_id = fields.Many2one(
        "request.stage",
        string="Stage",
        tracking=True,
        index=True,
        copy=False,
        domain=lambda self: ""
        "[('res_model_id.model', '=', '" + self._name + "'), ('state', '!=', 'cancel'),"
        "'|', ('request_type_ids', '=', False), ('request_type_ids', '=', request_type_id)]",
        group_expand="_read_group_stage_ids",
        default=_default_stage_id,
    )
    employee_id = fields.Many2one(
        "hr.employee",
        string="Applicant",
        index=True,
        default=_default_employee_id,
        tracking=True,
        readonly=True,
    )
    department_id = fields.Many2one("hr.department", string="Department", readonly=True)
    job_id = fields.Many2one("hr.job", string="Job", readonly=True)
    manager_id = fields.Many2one("hr.employee", string="Manager", readonly=True)
    kanban_color = fields.Integer(string="Kanban Color Index")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In progress"),
            ("cancel", "Cancel"),
            ("done", "Done"),
        ],
        copy=False,
        default="draft",
    )
    date = fields.Date(string="Request date", default=fields.Date.today, readonly=True)
    display_button_refuse = fields.Boolean(compute="_compute_display_button")
    display_button_send = fields.Boolean(compute="_compute_display_button")
    display_button_accept = fields.Boolean(compute="_compute_display_button")
    display_button_previous = fields.Boolean(compute="_compute_display_button")
    request_type_id = fields.Many2one(
        "request.type",
        string="Type",
        domain=lambda self: [("res_model", "=", self._name)],
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        readonly=True,
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)

    # ------------------------------------------------------------
    # Onchange methods
    # ------------------------------------------------------------
    @api.onchange("request_type_id")
    def _onchange_request_type(self):
        self.stage_id = self._get_next_stage(stage_type="default")
        self._onchange_stage_id()

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        self._sync_employee_details()

    def _sync_employee_details(self):
        for request in self:
            if request.employee_id:
                request.manager_id = request.employee_id.parent_id
                request.department_id = request.employee_id.department_id
                request.job_id = request.employee_id.job_id
                request.company_id = request.employee_id.company_id

    @api.onchange("stage_id")
    def _onchange_stage_id(self):
        if self.stage_id and self.stage_id.state:
            self.state = self.stage_id.state

    def add_follower(self, employee_id):
        employee = self.env["hr.employee"].browse(employee_id)
        if employee.user_id:
            self.message_subscribe(partner_ids=employee.user_id.partner_id.ids)

    # ------------------------------------------------------------
    # ORM Overrides methods
    # ------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        request = super().create(vals_list)
        for record in request:
            if record.employee_id:
                record.add_follower(record.employee_id.id)
                record._sync_employee_details()
        return request

    def write(self, vals):
        """Call sync_employee_details."""
        request = super(Request, self).write(vals)
        if "employee_id" in vals:
            for record in self:
                record.add_follower(record.employee_id.id)
                record._sync_employee_details()
        return request

    def _check_unlink_allowed(self):
        invalid_requests = self.filtered(
            lambda request: request.stage_id and request.stage_id.state not in ['draft']
        )
        if invalid_requests:
            raise UserError(
                _("You cannot delete a request which is in '%s' stage.") %
                invalid_requests[0].stage_id.name
            )

    def unlink(self):
        """Delete request only if state draft or cancel."""
        self._check_unlink_allowed()
        return super(Request, self).unlink()

    @api.depends('date', 'employee_id')
    def _compute_display_name(self):
        for request in self:
            res = [

                    str(request.id) if request.id else _("New"),
                    _("{} have an {} request on : {} ").format(
                        request.employee_id.name, self._description, request.date
                    ),

            ]

            request.display_name = ' / '.join(filter(None, res))

    # ------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------
    @api.depends("stage_id")
    def _compute_display_button(self):
        # todo: manager can create request for another employee  and send it to dm
        for rec in self:
            users = rec._get_approvers()
            rec.display_button_refuse = False
            rec.display_button_accept = False
            rec.display_button_send = False
            rec.display_button_previous = False
            if (
                rec.state == "draft"
                and rec.employee_id.user_id
                and rec.employee_id.user_id.id == rec.env.uid
            ):
                rec.display_button_send = True
            elif rec.state == "in_progress" and rec.env.uid in users:
                rec.display_button_accept = True
                rec.display_button_refuse = True
                rec.display_button_previous = rec.stage_id.move_previous_stage

    # ------------------------------------------------------------
    # Activity methods
    # ------------------------------------------------------------
    def _get_approvers(self):
        users = []
        # Notify users to approve or return feedback
        if self.stage_id.assign_type == "user":
            if self.stage_id.sudo().default_user_id:
                users.append(self.stage_id.sudo().default_user_id.id)
        elif self.stage_id.assign_type == "users":
            if self.stage_id.sudo().default_user_ids:
                users.extend(self.stage_id.sudo().default_user_ids.ids)
        elif self.stage_id.assign_type == "role":
            role_users = self.stage_id.sudo().default_role_ids.mapped("user_ids")
            if role_users:
                users.extend(role_users.ids)
        else:
            try:
                eval_dict = {"object": self.sudo(), "env": self.env, "result": None}
                code = self.stage_id.code.strip()
                safe_eval(code, eval_dict, mode="exec", nocopy=True)
                # the result of the evaluated code is put in the 'result' local variable
                # propagated to the context
                result = eval_dict.get("result")
                if (
                    result is not None
                    and isinstance(result, (object))
                    and result._name == "res.users"
                ):
                    if len(result) == 1:
                        users.append(result.sudo().id)
                    else:
                        for user in result:
                            users.append(user.id)
            except Exception:
                _logger.exception(_("Failed"))

        return users

    def action_feedback(self):
        """Return the feedback and marke done all activities."""
        self._make_done_activity()
        model_name = self._name.replace(".", "_")
        name = self._get_ir_model_data_name("mail_{}_".format(model_name) + "feedback")
        if name:
            for user in self._get_approvers():
                self.activity_schedule(name, user_id=user)
        return True

    def _get_ir_model_data_name(self, name):
        res_name = False
        model_data = (
            self.env["ir.model.data"].sudo().search([("name", "=", name)], limit=1)
        )
        if model_data:
            res_name = "{}.{}".format(model_data.module, name)
        return res_name

    def _action_schedule_activity(self, user):
        """Schedule activity for specific user."""
        model_name = self._name.replace(".", "_")
        name = self._get_ir_model_data_name("mail_{}_".format(model_name) + "approval")
        if name:
            self.activity_schedule(name, user_id=user)

    def activity_update(self):
        """Schedule the next activity."""
        self._make_done_activity()
        if self.state in ("draft", "in_progress"):
            for user in self._get_approvers():
                self._action_schedule_activity(user)
        return True

    def _make_done_activity(self):
        """Make done all activities of type validation."""
        activitys = self.env["mail.activity"].search(
            [
                ("activity_type_id.category", "=", "validation"),
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
            ]
        )
        for activity in activitys:
            activity.active = False

    def get_approvals_details(self, field="stage_id"):
        # filter messages per stage
        for request in self:
            track_obj = request.env["mail.tracking.value"]
            ir_model = self.env["ir.model"].search([("model", "=", request._name)])
            ir_model_field = request.env["ir.model.fields"].search(
                [("model_id", "=", ir_model.id), ("name", "=", field)]
            )
            tracking_lines = track_obj.sudo().search(
                [
                    ("mail_message_id.res_id", "=", request.id),
                    ("mail_message_id.model", "=", request._name),
                    ("field_id", "=", ir_model_field.id),
                    ("old_value_char", "!=", ""),
                ]
            )
            values = {}
            for track in tracking_lines:
                stage = request.env["request.stage"].browse(track.old_value_integer)
                if stage and stage.state != "cancel":
                    values.update(
                        {
                            track.old_value_char: {
                                "date": track.mail_message_id.date,
                                "approver": track.create_uid,
                                "stage_id": track.old_value_integer,
                            }
                        }
                    )
                else:
                    values.update(
                        {
                            track.new_value_char: {
                                "date": track.mail_message_id.date,
                                "approver": track.create_uid,
                                "stage_id": track.new_value_integer,
                            }
                        }
                    )
            return values

    # ------------------------------------------------------------
    # Business methods
    # ------------------------------------------------------------
    def _read_group_stage_ids(self, stages, domain):
        search_domain = [("res_model_id.model", "=", self._name)]
        search_domain = expression.AND([search_domain, self._get_extra_domain()])
        return stages.search(search_domain)

    def _get_extra_domain(self):
        search_domain = []
        # append the domain of type to general domain
        if self.request_type_id:
            search_domain = expression.AND(
                [
                    search_domain,
                    [
                        "|",
                        ("request_type_ids", "=", False),
                        ("request_type_ids", "in", [self.request_type_id.id]),
                    ],
                ]
            )
        else:
            search_domain = expression.AND(
                [search_domain, [("request_type_ids", "=", False)]]
            )
        return search_domain

    def _get_next_stage(self, stage_type="next"):
        """Return the next stage with specified the model state and next sequence."""
        # declared general domain it will be used for all requests
        search_domain = [("res_model", "=", self._name)]
        if stage_type == "default":
            search_domain = expression.AND([search_domain, [("state", "=", "draft")]])
        elif stage_type == "cancel":
            search_domain = expression.AND([search_domain, [("state", "=", "cancel")]])
        else:

            search_domain = expression.AND(
                [
                    search_domain,
                    [
                        ("state", "not in", ["cancel", "draft"]),
                        ("sequence", ">", self.stage_id.sequence),
                    ],
                ]
            )
        search_domain = expression.AND([search_domain, self._get_extra_domain()])
        next_stage = self.env["request.stage"].search(
            search_domain, order="sequence asc", limit=1
        )
        return next_stage

    def action_send(self):
        """Send the request to be approved by the right users."""
        for request in self:
            if request.stage_id and request.state == "draft":
                request.stage_id = request._get_next_stage()
                request._onchange_stage_id()
                request.activity_update()

    def action_accept(self):
        """Accept the request and Send it to be approved by the right users."""
        for request in self:
            if request.stage_id and request.state == "in_progress":
                request.stage_id = request._get_next_stage()
                request._onchange_stage_id()
                # Schedule the next activity
                if request.state != "done":
                    request.activity_update()
                # Send feedback to users
                else:
                    request.action_feedback()
            return True

    def action_refuse(self):
        """Refuse the request and return feedback to users."""
        for request in self:
            if request.stage_id and request.state == "in_progress":
                request.stage_id = request._get_next_stage(stage_type="cancel")
                request._onchange_stage_id()
                request.action_feedback()
            return True

    def _get_previous_stage(self):
        """Return the previous stage with specified the model state and next sequence."""
        # declared general domain it will be used for all requests
        search_domain = [
            ("res_model", "=", self._name),
            ("state", "in", ["draft", "in_progress"]),
            ("sequence", "<", self.stage_id.sequence),
        ]
        search_domain = expression.AND([search_domain, self._get_extra_domain()])
        previous_stage = self.env["request.stage"].search(
            search_domain, order="sequence desc", limit=1
        )
        return previous_stage

    def action_previous_stage(self):
        """Return the request to the previous stage."""
        for request in self:
            if request.stage_id and request.state == "in_progress":
                request.stage_id = request._get_previous_stage()
                request._onchange_stage_id()
                request.activity_update()

    # ------------------------------------------------------------
    # Messaging methods
    # ------------------------------------------------------------
    def _track_subtype(self, init_values):
        """Give the subtypes triggered by the changes on the record according
        to values that have been updated.

        :param init_values: the original values of the record; only modified fields
                            are present in the dict

        each module inherit  from request should define two mail.message.subtype :
        1- ('%s.mt_%s_approved') % (module_name, model_name),
            example hr_authorization.mt_hr_authorization_approved
        2- ('%s.mt_%s_refused') % (module_name, model_name),
            example hr_authorization.mt_hr_authorization_refused
        """
        if "stage_id" in init_values and self.stage_id.state in ("done", "cancel"):
            model_name = self._name.replace(".", "_")
            if self.stage_id.state == "done":
                name = self._get_ir_model_data_name(
                    "mt_{}_".format(model_name) + "approved"
                )
            elif self.stage_id.state == "cancel":
                name = self._get_ir_model_data_name(
                    "mt_{}_".format(model_name) + "refused"
                )
            if name:
                return self.env.ref(name)
        return super(Request, self)._track_subtype(init_values)


class RequestType(models.Model):
    _name = "request.type"
    _description = " Request Type"

    @api.model
    def _default_res_model_id(self):
        """Use when creating type from a tree view for another model."""
        if self.env.context.get("default_res_model"):
            return self.env["ir.model"]._get(self.env.context.get("default_res_model"))

    code = fields.Char()
    name = fields.Char(required=True, translate=True)
    res_model_id = fields.Many2one(
        "ir.model",
        required=True,
        index=True,
        string="Associated Model",
        domain=[("transient", "=", False)],
        default=_default_res_model_id,
        ondelete="cascade",
    )
    res_model = fields.Char("Related Document Model")
    active = fields.Boolean(default=True)
