from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class BussmaMarketingTask(models.Model):
    _name = 'bussma.marketing.task'
    _description = 'Marketing Tasks'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Task name', required=True, tracking=True)
    material_id = fields.Many2one('bussma.marketing.material', string='Marketing Material', ondelete='cascade', required=True, tracking=True)
    marketing_id = fields.Many2one('bussma.marketing', related='material_id.marketing_id', store=True, string='Marketing Record')
    department_id = fields.Many2one(
        'bussma.marketing.department',
        string='Department',
        tracking=True
    )
    allowed_department_ids = fields.Many2many('bussma.marketing.department', related='material_id.department_ids', string='Marketing Material Departments')
    department_member_ids = fields.Many2many(
        'res.users',
        string='Department Members',
        compute='_compute_department_member_ids'
    )
    user_ids = fields.Many2many(
        'res.users',
        string='Assignees',
        tracking=True,
        domain="[('id', 'in', department_member_ids)]"
    )
    state = fields.Selection([
        ('draft', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('approved', 'Approved'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    date_deadline = fields.Date(string='Deadline')
    request_notes = fields.Text(string='Request Notes', tracking=True)
    request_attachment_ids = fields.Many2many(
        'ir.attachment',
        'bussma_task_request_attachment_rel',
        'task_id',
        'attachment_id',
        string='Request Attachments'
    )
    result_notes = fields.Text(string='Result Notes', tracking=True)
    result_attachment_ids = fields.Many2many(
        'ir.attachment',
        'bussma_task_result_attachment_rel',
        'task_id',
        'attachment_id',
        string='Result Attachments'
    )
    is_authorized_supervisor = fields.Boolean(
        string='Is Authorized Supervisor',
        compute='_compute_is_authorized_supervisor'
    )
    is_task_assignee = fields.Boolean(
        string='Is Task Assignee',
        compute='_compute_is_task_assignee'
    )
    is_task_editor = fields.Boolean(
        string='Is Task Editor',
        compute='_compute_is_task_editor'
    )
    is_marketing_supervisor = fields.Boolean(
        string='Is Marketing Supervisor',
        compute='_compute_is_marketing_supervisor'
    )

    @api.depends_context('uid')
    def _compute_is_marketing_supervisor(self):
        is_sup = self.env.user.has_group('marketing_opportunity_management.group_marketing_supervisor')
        for rec in self:
            rec.is_marketing_supervisor = is_sup

    @api.depends('user_ids')
    @api.depends_context('uid')
    def _compute_is_task_assignee(self):
        user = self.env.user
        for rec in self:
            rec.is_task_assignee = (user in rec.user_ids)

    @api.depends('user_ids', 'department_id', 'department_id.manager_id')
    @api.depends_context('uid')
    def _compute_is_task_editor(self):
        for rec in self:
            rec.is_task_editor = rec._can_user_edit_task()

    @api.depends('department_id', 'department_id.member_ids')
    def _compute_department_member_ids(self):
        for rec in self:
            rec.department_member_ids = rec.department_id.member_ids if rec.department_id else self.env['res.users']

    @api.depends('department_id', 'department_id.manager_id', 'material_id', 'material_id.user_id', 'material_id.department_ids', 'material_id.department_ids.manager_id')
    @api.depends_context('uid')
    def _compute_is_authorized_supervisor(self):
        for rec in self:
            rec.is_authorized_supervisor = rec._is_user_authorized_supervisor()

    def _is_user_authorized_supervisor(self):
        self.ensure_one()
        user = self.env.user
        # 1. Marketing Supervisor
        if user.has_group('marketing_opportunity_management.group_marketing_supervisor'):
            return True
        # 2. Department Manager of the task
        if self.department_id and self.department_id.manager_id and self.department_id.manager_id == user:
            return True
        # 3. Marketing Material Responsible
        if self.material_id and self.material_id.user_id and self.material_id.user_id == user:
            return True
        # 4. Project Material Responsible
        mkt = self.marketing_id or (self.material_id and self.material_id.marketing_id)
        if mkt and mkt.material_responsible_id and mkt.material_responsible_id == user:
            return True
        return False

    def _can_user_edit_task(self):
        self.ensure_one()
        user = self.env.user
        if self._is_user_authorized_supervisor():
            return True
        if user in self.user_ids:
            return True
        if self.department_id and user == self.department_id.manager_id:
            return True
        return False

    def _send_task_assignees_notification(self, new_users):
        template = self.env.ref('marketing_opportunity_management.email_template_marketing_task_users_assigned', raise_if_not_found=False)
        if not template or not new_users:
            return
        emails = [u.email.strip() for u in new_users.filtered(lambda u: u.active and u.email)]
        if not emails:
            return
        email_to = ",".join(set(emails))
        for rec in self:
            try:
                email_values = {
                    'email_to': email_to,
                    'email_from': self.env.user.email or self.env.company.email,
                    'model': False,
                    'res_id': False,
                }
                template.send_mail(rec.id, force_send=True, email_values=email_values)
                _logger.info("[Task Email] Sent assignee notification to %s for task ID %s", email_to, rec.id)
            except Exception as e:
                _logger.error("Failed to send task assignee notification for task %s: %s", rec.id, str(e))

    def _send_task_completed_notification(self):
        template = self.env.ref('marketing_opportunity_management.email_template_marketing_task_completed', raise_if_not_found=False)
        if not template:
            return

        for rec in self:
            recipient_emails = set()
            if rec.material_id and rec.material_id.user_id and rec.material_id.user_id.active and rec.material_id.user_id.email:
                recipient_emails.add(rec.material_id.user_id.email.strip())
            mkt = rec.marketing_id or (rec.material_id and rec.material_id.marketing_id)
            if mkt and mkt.material_responsible_id and mkt.material_responsible_id.active and mkt.material_responsible_id.email:
                recipient_emails.add(mkt.material_responsible_id.email.strip())

            if not recipient_emails:
                continue

            email_to = ",".join(recipient_emails)
            try:
                email_values = {
                    'email_to': email_to,
                    'email_from': self.env.user.email or self.env.company.email,
                    'model': False,
                    'res_id': False,
                }
                template.send_mail(rec.id, force_send=True, email_values=email_values)
                _logger.info("[Task Email] Sent task completed notification to %s for task ID %s", email_to, rec.id)
            except Exception as e:
                _logger.error("Failed to send task completed notification for task %s: %s", rec.id, str(e))

    def create_mail_activity(self, users, summary='Request Approval', is_done=True):
        """Create Odoo activities for the specified users on this task record."""
        if is_done:
            activities = self.env['mail.activity'].sudo().search([
                ('res_model', '=', self._name),
                ('res_id', 'in', self.ids),
            ])
            if activities:
                activities.action_done()

        if users:
            activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            model_id = self.env['ir.model']._get(self._name).id

            for user in users:
                self.env['mail.activity'].sudo().create({
                    'summary': summary,
                    'activity_type_id': activity_type.id if activity_type else False,
                    'res_model_id': model_id,
                    'res_id': self.id,
                    'user_id': user.id,
                    'date_deadline': self.date_deadline or fields.Date.today(),
                })

    def _notify_stage_authorized_users(self):
        """Identify authorized users for the task state and create activities for them."""
        self.ensure_one()
        if self.state == 'done':
            # Complete task activities for assignees and notify manager/supervisors
            self.create_mail_activity(users=False, is_done=True)
            managers = self.env['res.users']
            if self.department_id and self.department_id.manager_id and self.department_id.manager_id.active:
                managers |= self.department_id.manager_id
            group_sup = self.env.ref('marketing_opportunity_management.group_marketing_supervisor', raise_if_not_found=False)
            if group_sup:
                managers |= group_sup.users.filtered(lambda u: u.active)
            if managers:
                summary = _("Approve marketing task: %s") % (self.name or '')
                self.create_mail_activity(managers, summary=summary, is_done=False)
        elif self.state in ['draft', 'in_progress']:
            self.create_mail_activity(users=False, is_done=True)
            if self.user_ids:
                summary = _("New task assigned: %s") % (self.name or '')
                self.create_mail_activity(self.user_ids, summary=summary, is_done=False)
        elif self.state in ['approved', 'cancel']:
            self.create_mail_activity(users=False, is_done=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec._is_user_authorized_supervisor():
                raise UserError(_("Creating tasks is restricted to the marketing supervisor, marketing material responsible, or department manager only."))
            if rec.user_ids:
                rec._send_task_assignees_notification(rec.user_ids)
            rec._notify_stage_authorized_users()
        return records

    def write(self, vals):
        if not self.env.su:
            for rec in self:
                if rec.state in ['approved', 'cancel']:
                    is_authorized = rec._is_user_authorized_supervisor()
                    non_state_vals = {k: v for k, v in vals.items() if k != 'state'}
                    if non_state_vals and not is_authorized:
                        raise UserError(_("Cannot modify task fields when the task state is Approved or Cancelled."))
                    if 'state' in vals and not is_authorized:
                        raise UserError(_("Changing the status of an Approved or Cancelled task is restricted to the Marketing Supervisor or Department Manager only."))

        check_notes_or_att = 'request_notes' in vals or 'request_attachment_ids' in vals
        check_approve_or_cancel = 'state' in vals and vals['state'] in ['approved', 'cancel']

        if check_notes_or_att:
            for rec in self:
                if not rec._is_user_authorized_supervisor():
                    raise UserError(_("You can only edit the request notes or attachments if you are the marketing supervisor or department manager."))

        if check_approve_or_cancel:
            for rec in self:
                if not rec._is_user_authorized_supervisor():
                    raise UserError(_("Approving or cancelling the task is restricted to the marketing supervisor or department manager only."))

        if 'state' in vals and not self.env.su:
            for rec in self:
                if not rec._can_user_edit_task():
                    raise UserError(_("Changing task status is restricted to assigned task members, department members, department manager, or marketing supervisor."))

        if ('result_notes' in vals or 'result_attachment_ids' in vals) and not self.env.su:
            for rec in self:
                if not (rec.is_task_assignee or rec._is_user_authorized_supervisor()):
                    raise UserError(_("Editing result notes or attachments is restricted to assigned task members, department manager, or marketing supervisor."))

        old_users_per_task = {rec.id: set(rec.user_ids.ids) for rec in self}
        old_states = {rec.id: rec.state for rec in self}

        res = super().write(vals)

        if 'user_ids' in vals:
            for rec in self:
                old_set = old_users_per_task.get(rec.id, set())
                added_users = rec.user_ids.filtered(lambda u: u.id not in old_set)
                if added_users:
                    rec._send_task_assignees_notification(added_users)

        if 'state' in vals and vals['state'] == 'done':
            for rec in self:
                if old_states.get(rec.id) != 'done':
                    rec._send_task_completed_notification()

        if 'user_ids' in vals or 'state' in vals:
            for rec in self:
                rec._notify_stage_authorized_users()

        return res
