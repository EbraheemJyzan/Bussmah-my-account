import json
import logging
import pytz
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class BussmaMarketingMaterial(models.Model):
    _name = 'bussma.marketing.material'
    _description = 'Marketing Materials'
    _inherit = 'request'
    _order = 'id desc'

    @api.model
    def _default_request_type_id(self):
        return self.env.ref('marketing_opportunity_management.request_type_marketing_material', raise_if_not_found=False)

    @api.model
    def _default_stage_id(self):
        needs_content = self.env.context.get('default_needs_content')
        if needs_content == 'no':
            stage = self.env.ref('marketing_opportunity_management.stage_mat_design_exec', raise_if_not_found=False)
            if stage:
                return stage.id
        stage = self.env.ref('marketing_opportunity_management.stage_mat_content_exec', raise_if_not_found=False)
        if stage:
            return stage.id
        request_type = self._default_request_type_id()
        if request_type:
            stage = self.env['request.stage'].search([
                ('request_type_ids', 'in', [request_type.id]),
                ('res_model', '=', 'bussma.marketing.material')
            ], order='sequence asc', limit=1)
            return stage.id if stage else False
        return False

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        return self.env['request.stage'].search([('res_model', '=', 'bussma.marketing.material')], order='sequence asc')

    request_type_id = fields.Many2one(
        'request.type',
        string='Request Type',
        default=lambda self: self.env.ref('marketing_opportunity_management.request_type_marketing_material', raise_if_not_found=False)
    )
    stage_id = fields.Many2one(
        'request.stage',
        string='Stage',
        default=_default_stage_id,
        group_expand='_read_group_stage_ids',
        domain="[('res_model', '=', 'bussma.marketing.material')]",
        tracking=True
    )
    active = fields.Boolean(default=True)
    material_stage_selection = fields.Selection(
        related='stage_id.material_stage_selection',
        string='Material Stage Selection',
        store=True
    )
    code = fields.Char(string='Activity Code', tracking=True)
    name = fields.Char(string='Marketing Material Name', tracking=True)
    is_marketing_supervisor = fields.Boolean(
        string='Is Marketing Supervisor',
        compute='_compute_is_marketing_supervisor'
    )
    is_material_responsible = fields.Boolean(
        string='Is Material Responsible',
        compute='_compute_is_material_responsible'
    ) 
    user_id = fields.Many2one('res.users', string='Responsible', tracking=True)
    department_ids = fields.Many2many(
        'bussma.marketing.department',
        'bussma_material_dept_rel',
        'material_id',
        'dept_id',
        string='Departments',
        tracking=True
    )
    activity_id = fields.Many2one('bussma.marketing.activity', string='Marketing Activity', tracking=True)
    is_my_activity = fields.Boolean(
        string="Is My Activity",
        compute="_compute_is_my_activity"
    )
    marketing_id = fields.Many2one('bussma.marketing', string='Marketing Record', ondelete='cascade', tracking=True)
    bussma_project_id = fields.Many2one(related='marketing_id.bussma_project_id', string='Project')
    is_opportunity_request = fields.Boolean(related='marketing_id.is_opportunity_request', string='Is Opportunity Request')
    is_office_request = fields.Boolean(related='marketing_id.is_office_request', string='Is Office Request')
    pm_rejection_notes = fields.Text(string='Project Manager Return Notes', tracking=True)
    pm_rejection_attachment_ids = fields.Many2many(
        'ir.attachment',
        'bussma_material_pm_rejection_att_rel',
        'material_id',
        'att_id',
        string='Project Manager Return Attachments'
    )
    modification_request_notes = fields.Text(string='Modification Request Notes', tracking=True)
    last_return_type = fields.Selection([
        ('pm_rejection', 'Project Manager Rejection'),
        ('modification', 'Modification Request'),
    ], string='Last Return Type', tracking=True,
       help='Tracks whether the last return to marketing approval was a PM rejection or a modification request')
    modification_attachment_ids = fields.Many2many(
        'ir.attachment',
        'bussma_material_mod_att_rel',
        'material_id',
        'att_id',
        string='Modification Request Attachments'
    )
    return_note_ids = fields.One2many(
        'bussma.material.return.note',
        'material_id',
        string='Return Notes'
    )
    modification_request_count = fields.Integer(
        string='Modification Request Count',
        compute='_compute_return_note_counts',
        help='Total number of modification requests submitted by the requesting entity'
    )
    modification_return_count = fields.Integer(
        string='Modification Return Count',
        compute='_compute_return_note_counts',
    )
    rejection_return_count = fields.Integer(
        string='Rejection Return Count',
        compute='_compute_return_note_counts',
    )
    is_project_manager = fields.Boolean(
        string='Is Project Manager',
        compute='_compute_is_project_manager'
    )
    task_ids = fields.One2many('bussma.marketing.task', 'material_id', string='Tasks')
    task_count = fields.Integer(string='Task Count', compute='_compute_task_count', store=True)
    task_json = fields.Text(string='Task Data', compute='_compute_task_json')
    context_dept_code = fields.Char(string='Department Code Filter', compute='_compute_context_dept_code')
    hide_new_task = fields.Boolean(string='Hide New Task Button', compute='_compute_hide_new_task')
    notes = fields.Text(string='Notes')
    supervisor_notes = fields.Text(string='Marketing Supervisor Notes')
    returned_stage_id = fields.Many2one('request.stage', string='Returned Stage', tracking=True)
    supervisor_attachment_ids = fields.Many2many(
        'ir.attachment',
        'bussma_material_supervisor_att_rel',
        'material_id',
        'attachment_id',
        string='Notes Attachments'
    )
    completed_task_ids = fields.One2many(
        'bussma.marketing.task',
        'material_id',
        compute='_compute_completed_task_ids',
        string='Completed or Approved Tasks'
    )
    output_attachment_ids = fields.Many2many(
        'ir.attachment',
        'bussma_material_output_attachment_rel',
        'material_id',
        'attachment_id',
        compute='_compute_output_attachment_ids',
        store=True,
        readonly=False,
        string='Marketing Material Output Attachments'
    )
    result_notes = fields.Text(string='Marketing Material Result Notes', tracking=True)
    stage_history_ids = fields.One2many(
        'bussma.material.stage.history',
        'material_id',
        string='Stage History'
    )
    stage_history_filter_stage_id = fields.Many2one(
        'request.stage',
        string='Filter Stage History by Stage',
        domain="[('res_model', '=', 'bussma.marketing.material')]",
        store=False,
        help='Select a stage to filter the stage history log below'
    )
    stage_history_filtered_ids = fields.Many2many(
        'bussma.material.stage.history',
        compute='_compute_stage_history_filtered_ids',
        string='Stage History (Filtered)'
    )
    current_stage_duration_days = fields.Float(
        string='Current Stage Duration (Days)',
        compute='_compute_stage_durations',
        help='Cumulative days spent in the current stage (including previous visits if returned). Example: 1.5 = 1 day and 12 hours'
    )
    total_stage_duration_days = fields.Float(
        string='Total Duration Across All Stages (Days)',
        compute='_compute_stage_durations',
        help='Total days spent across all stages. Example: 2.5 = 2 days and 12 hours'
    )
    # Dedicated Stage Duration Fields (in Days)
    duration_content_exec_days = fields.Float(string='Content Execution Duration (Days)', compute='_compute_stage_durations')
    duration_content_approve_days = fields.Float(string='Content Approval Duration (Days)', compute='_compute_stage_durations')
    duration_design_exec_days = fields.Float(string='Design Execution Duration (Days)', compute='_compute_stage_durations')
    duration_design_approve_days = fields.Float(string='Design Approval Duration (Days)', compute='_compute_stage_durations')
    duration_digital_exec_days = fields.Float(string='Digital Execution Duration (Days)', compute='_compute_stage_durations')
    duration_digital_approve_days = fields.Float(string='Digital Approval Duration (Days)', compute='_compute_stage_durations')
    duration_ops_exec_days = fields.Float(string='Operations Execution Duration (Days)', compute='_compute_stage_durations')
    duration_ops_approve_days = fields.Float(string='Operations Approval Duration (Days)', compute='_compute_stage_durations')
    # Dedicated Department Duration Fields (in Days = Execution + Approval)
    duration_dept_content_days = fields.Float(string='Content Department Total Duration (Days)', compute='_compute_stage_durations')
    duration_dept_design_days = fields.Float(string='Design Department Total Duration (Days)', compute='_compute_stage_durations')
    duration_dept_digital_days = fields.Float(string='Digital Department Total Duration (Days)', compute='_compute_stage_durations')
    duration_dept_ops_days = fields.Float(string='Operations Department Total Duration (Days)', compute='_compute_stage_durations')
    # Return Count Fields (approve → exec per department)
    return_count_content = fields.Integer(
        string='Content Return Count',
        compute='_compute_return_counts',
        store=True,
        help='Number of times the record was returned from Content Approval to Content Execution'
    )
    return_count_design = fields.Integer(
        string='Design Return Count',
        compute='_compute_return_counts',
        store=True,
        help='Number of times the record was returned from Design Approval to Design Execution'
    )
    return_count_digital = fields.Integer(
        string='Digital Return Count',
        compute='_compute_return_counts',
        store=True,
        help='Number of times the record was returned from Digital Approval to Digital Execution'
    )
    return_count_ops = fields.Integer(
        string='Operations Return Count',
        compute='_compute_return_counts',
        store=True,
        help='Number of times the record was returned from Operations Approval to Operations Execution'
    )
    needs_content = fields.Selection(
        [
            ('yes', 'Yes'),
            ('no', 'No'),
        ],
        string='Does it require content?',
        compute='_compute_needs_content',
        store=True
    )
    content_supervisor_approval = fields.Selection([
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ], string='Content Supervisor Approval', tracking=True)
    content_supervisor_notes = fields.Text(string='Content Supervisor Notes', tracking=True)
    design_supervisor_approval = fields.Selection([
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ], string='Design Supervisor Approval', tracking=True)
    design_supervisor_notes = fields.Text(string='Design Supervisor Notes', tracking=True)
    digital_supervisor_approval = fields.Selection([
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ], string='Digital Supervisor Approval', tracking=True)
    digital_supervisor_notes = fields.Text(string='Digital Supervisor Notes', tracking=True)
    ops_supervisor_approval = fields.Selection([
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ], string='Operations Supervisor Approval', tracking=True)
    ops_supervisor_notes = fields.Text(string='Operations Supervisor Notes', tracking=True)

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields=allfields, attributes=attributes)
        if res and 'active' in res:
            res['active']['readonly'] = True
            res['active']['invisible'] = True
        return res

    @api.depends('return_note_ids', 'return_note_ids.return_type')
    def _compute_return_note_counts(self):
        for rec in self:
            rec.modification_return_count = len(rec.return_note_ids.filtered(lambda n: n.return_type == 'modification'))
            rec.rejection_return_count = len(rec.return_note_ids.filtered(lambda n: n.return_type == 'rejected'))
            rec.modification_request_count = rec.modification_return_count

    @api.depends_context('uid')
    def _compute_is_marketing_supervisor(self):
        is_sup = self.env.user.has_group('marketing_opportunity_management.group_marketing_supervisor') or self.env.su
        for rec in self:
            rec.is_marketing_supervisor = is_sup

    @api.depends('department_ids')
    def _compute_needs_content(self):
        content_dept = self.env.ref('marketing_opportunity_management.dept_content', raise_if_not_found=False)
        for rec in self:
            if content_dept and content_dept in rec.department_ids:
                rec.needs_content = 'yes'
            else:
                rec.needs_content = 'no'

    @api.depends('user_id', 'marketing_id.material_responsible_id', 'department_ids.manager_id', 'stage_id.department_id.manager_id')
    @api.depends_context('uid')
    def _compute_is_material_responsible(self):
        user = self.env.user
        for rec in self:
            rec.is_material_responsible = (
                (rec.user_id and rec.user_id == user) or
                (rec.marketing_id and rec.marketing_id.material_responsible_id and rec.marketing_id.material_responsible_id == user)
            )

    def _get_department_for_code(self, dept_code):
        self.ensure_one()
        if not dept_code:
            return False
        if self.stage_id and self.stage_id.department_id and self.stage_id.department_id.code and self.stage_id.department_id.code.upper() == dept_code.upper():
            return self.stage_id.department_id
        matched_dept = self.department_ids.filtered(lambda d: d.code and d.code.upper() == dept_code.upper())
        if matched_dept:
            return matched_dept[0]
        dept = self.env['bussma.marketing.department'].search([('code', '=ilike', dept_code)], limit=1)
        if dept:
            return dept
        xml_map = {
            'CONTENT': 'dept_content',
            'DESIGN': 'dept_design',
            'DIGITAL': 'dept_digital',
            'OPS': 'dept_ops',
        }
        xml_id = xml_map.get(dept_code.upper())
        if xml_id:
            return self.env.ref(f'marketing_opportunity_management.{xml_id}', raise_if_not_found=False)
        return False

    def _check_stage_change_permission(self, old_stage, new_stage):
        self.ensure_one()
        user = self.env.user

        old_sel = old_stage.material_stage_selection if old_stage else False
        new_sel = new_stage.material_stage_selection if new_stage else False

        if old_sel == new_sel:
            return True

        is_moving_forward = bool(old_stage and new_stage and new_stage.sequence > old_stage.sequence)

        # Allow returning to previous stages without restrictions
        if not is_moving_forward:
            return True

        dept_code = False
        is_approval = False

        if old_sel in ['mat_content_exec', 'mat_content_approve']:
            dept_code = 'CONTENT'
            is_approval = (old_sel == 'mat_content_approve')
        elif old_sel in ['mat_design_exec', 'mat_design_approve']:
            dept_code = 'DESIGN'
            is_approval = (old_sel == 'mat_design_approve')
        elif old_sel in ['mat_digital_exec', 'mat_digital_approve']:
            dept_code = 'DIGITAL'
            is_approval = (old_sel == 'mat_digital_approve')
        elif old_sel in ['mat_ops_exec', 'mat_ops_approve']:
            dept_code = 'OPS'
            is_approval = (old_sel == 'mat_ops_approve')

        # Check pending tasks ONLY when moving forward to a future stage from a department approval stage
        if is_approval and is_moving_forward and dept_code:
            dept = self._get_department_for_code(dept_code)
            if dept:
                pending_tasks = self.task_ids.filtered(
                    lambda t: ((t.department_id and t.department_id.id == dept.id) or (t.department_id.code and dept.code and t.department_id.code == dept.code)) and t.state not in ['approved', 'cancel']
                )
                if pending_tasks:
                    raise UserError(_("Cannot move to the next stage because there are tasks related to this department that have not been approved or cancelled yet."))

        if user.has_group('marketing_opportunity_management.group_marketing_supervisor') or user.has_group('base.group_system'):
            return True

        if old_sel == 'mat_pm_approve':
            if self.is_project_manager:
                return True
            raise UserError(_("Moving or returning from Project Manager approval stage is restricted to the Project Manager or Marketing Supervisor."))

        if not dept_code:
            raise UserError(_("Moving or returning the marketing material stage is restricted to the marketing supervisor only."))

        dept = self._get_department_for_code(dept_code)
        if dept:
            if dept.manager_id and dept.manager_id == user:
                return True
            if not is_approval:
                dept_tasks = self.task_ids.filtered(
                    lambda t: ((t.department_id and t.department_id.id == dept.id) or (t.department_id.code and dept.code and t.department_id.code.upper() == dept.code.upper())) and user in t.user_ids
                )
                if dept_tasks:
                    return True

        if is_approval:
            raise UserError(_("Moving or returning in this department approval stage is restricted to the department manager or marketing supervisor only."))
        else:
            raise UserError(_("Moving from this department execution stage is restricted to the marketing supervisor, department manager, or task assignees of this department only."))

    def _check_unlink_allowed(self):
        invalid_materials = self.filtered(lambda r: r.stage_id and r.stage_id.state == 'done')
        if invalid_materials:
            raise UserError(_("Can't delete completed marketing material."))

    def action_open_return_stage_wizard(self):
        self.ensure_one()
        user = self.env.user
        if not (user.has_group('base.group_system') or user.has_group('marketing_opportunity_management.group_marketing_supervisor')):
            raise UserError(_("Sorry, returning the record to a previous stage is only for the marketing supervisor."))
        return {
            'name': _('Return to Previous Stage'),
            'type': 'ir.actions.act_window',
            'res_model': 'material.return.stage.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_material_id': self.id,
            }
        }

    @api.depends('name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name

    def _compute_context_dept_code(self):
        dept_code = self.env.context.get('filter_dept_code', '')
        for rec in self:
            rec.context_dept_code = dept_code

    def _compute_hide_new_task(self):
        hide = self.env.context.get('hide_new_task', False)
        for rec in self:
            rec.hide_new_task = hide

    @api.depends_context('uid')
    @api.depends('activity_ids', 'activity_ids.user_id')
    def _compute_is_my_activity(self):
        current_user = self.env.user
        for record in self:
            record.is_my_activity = any(act.user_id == current_user for act in record.activity_ids)

    def create_mail_activity(self, users, summary='Request Approval', is_done=True):
        """Create Odoo activities for the specified users on this material record."""
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
                    'date_deadline': fields.Date.today(),
                })

    def _notify_stage_authorized_users(self):
        """Identify authorized users for the current stage and create activities for them."""
        self.ensure_one()
        if not self.stage_id:
            return

        # Always clear old activities when stage changes
        self.create_mail_activity(users=False, is_done=True)

        stage_sel = self.stage_id.material_stage_selection or ''
        
        # Map approval stage selection to department code
        dept_code_map = {
            'mat_content_approve': 'CONTENT',
            'mat_design_approve': 'DESIGN',
            'mat_digital_approve': 'DIGITAL',
            'mat_ops_approve': 'OPS',
        }

        if stage_sel == 'mat_marketing_approve':
            # Do not create new activity for marketing supervisor when moving to mat_marketing_approve
            return

        elif stage_sel in dept_code_map or stage_sel.endswith('_approve'):
            users = self.env['res.users']
            
            # Find department manager for the current approval stage
            dept_code = dept_code_map.get(stage_sel)
            dept = False
            if dept_code:
                dept = self._get_department_for_code(dept_code)
            elif self.stage_id.department_id:
                dept = self.stage_id.department_id

            if dept and dept.manager_id and dept.manager_id.active:
                users |= dept.manager_id

            if users:
                self.create_mail_activity(users, summary=False, is_done=False)

    @api.depends('task_ids', 'task_ids.name', 'task_ids.state', 'task_ids.user_ids', 'task_ids.department_id')
    def _compute_task_count(self):
        for record in self:
            record.task_count = len(record.task_ids)

    @api.depends_context('uid')
    @api.depends('task_ids', 'task_ids.name', 'task_ids.state', 'task_ids.user_ids', 'task_ids.user_ids.name', 'task_ids.department_id', 'task_ids.department_id.name', 'task_ids.department_id.color', 'task_ids.activity_ids', 'task_ids.activity_ids.user_id')
    def _compute_task_json(self):
        state_styles = {
            'draft': ('bg-secondary', 'bg-transparent'),
            'in_progress': ('bg-secondary text-white', 'bg-secondary-subtle'),
            'done': ('bg-warning text-dark', 'bg-warning-subtle'),
            'approved': ('bg-success', 'bg-success-subtle'),
            'cancel': ('bg-danger', 'bg-danger-subtle')
        }
        current_user = self.env.user
        for record in self:
            data = []
            for t in record.task_ids:
                st_class, bg_class = state_styles.get(t.state, ('bg-secondary', 'bg-transparent'))
                state_dict = dict(t._fields['state']._description_selection(self.env))
                st_title = _(state_dict.get(t.state, t.state))
                has_my_act = any(act.user_id == current_user for act in t.activity_ids)
                data.append({
                    'id': t.id,
                    'name': t.name,
                    'state': t.state,
                    'bg_class': bg_class,
                    'user_name': ', '.join(t.user_ids.mapped('name')) if t.user_ids else '',
                    'department_ids': [t.department_id.id] if t.department_id else [],
                    'department_code': t.department_id.code if t.department_id else '',
                    'departments': [{'id': t.department_id.id, 'name': t.department_id.name, 'color': t.department_id.color or 0}] if t.department_id else [],
                    'state_title': st_title,
                    'state_class': st_class,
                    'has_my_activity': has_my_act,
                })
            record.task_json = json.dumps(data)

    @api.depends('task_ids', 'task_ids.state')
    def _compute_completed_task_ids(self):
        for rec in self:
            rec.completed_task_ids = rec.task_ids.filtered(lambda t: t.state in ['done', 'approved'])

    @api.depends('task_ids', 'task_ids.state', 'task_ids.result_attachment_ids')
    def _compute_output_attachment_ids(self):
        for rec in self:
            approved_tasks = rec.task_ids.filtered(lambda t: t.state == 'approved')
            task_atts = approved_tasks.mapped('result_attachment_ids')
            if task_atts:
                rec.output_attachment_ids = [(4, att.id) for att in task_atts]

    @api.depends('stage_history_ids', 'stage_history_filter_stage_id')
    def _compute_stage_history_filtered_ids(self):
        for rec in self:
            if rec.stage_history_filter_stage_id:
                rec.stage_history_filtered_ids = rec.stage_history_ids.filtered(
                    lambda h: h.stage_id == rec.stage_history_filter_stage_id
                )
            else:
                rec.stage_history_filtered_ids = rec.stage_history_ids

    @api.depends('stage_history_ids', 'stage_history_ids.is_return', 'stage_history_ids.stage_id')
    def _compute_return_counts(self):
        for rec in self:
            returns = rec.stage_history_ids.filtered(lambda h: h.is_return)
            rec.return_count_content = len(returns.filtered(
                lambda h: h.stage_id.material_stage_selection == 'mat_content_exec'
            ))
            rec.return_count_design = len(returns.filtered(
                lambda h: h.stage_id.material_stage_selection == 'mat_design_exec'
            ))
            rec.return_count_digital = len(returns.filtered(
                lambda h: h.stage_id.material_stage_selection == 'mat_digital_exec'
            ))
            rec.return_count_ops = len(returns.filtered(
                lambda h: h.stage_id.material_stage_selection == 'mat_ops_exec'
            ))

    @api.depends('stage_id', 'stage_history_ids', 'stage_history_ids.start_date', 'stage_history_ids.end_date', 'stage_history_ids.duration_days')
    def _compute_stage_durations(self):
        now = fields.Datetime.now()
        for rec in self:
            rec.stage_history_ids._compute_duration()

            if rec.stage_id and rec.stage_id.material_stage_selection != 'mat_marketing_approve':
                current_stage_histories = rec.stage_history_ids.filtered(lambda h: h.stage_id == rec.stage_id)
                rec.current_stage_duration_days = round(sum(current_stage_histories.mapped('duration_days')), 2)
            else:
                rec.current_stage_duration_days = 0.0

            valid_histories = rec.stage_history_ids.filtered(lambda h: h.stage_id.material_stage_selection != 'mat_marketing_approve')
            rec.total_stage_duration_days = round(sum(valid_histories.mapped('duration_days')), 2)

            # Compute sum for each stage selection code
            stage_sums = {}
            for h in valid_histories:
                sel = h.stage_id.material_stage_selection
                if sel and sel != 'mat_marketing_approve':
                    stage_sums[sel] = stage_sums.get(sel, 0.0) + h.duration_days

            rec.duration_content_exec_days = round(stage_sums.get('mat_content_exec', 0.0), 2)
            rec.duration_content_approve_days = round(stage_sums.get('mat_content_approve', 0.0), 2)
            rec.duration_dept_content_days = round(rec.duration_content_exec_days + rec.duration_content_approve_days, 2)

            rec.duration_design_exec_days = round(stage_sums.get('mat_design_exec', 0.0), 2)
            rec.duration_design_approve_days = round(stage_sums.get('mat_design_approve', 0.0), 2)
            rec.duration_dept_design_days = round(rec.duration_design_exec_days + rec.duration_design_approve_days, 2)

            rec.duration_digital_exec_days = round(stage_sums.get('mat_digital_exec', 0.0), 2)
            rec.duration_digital_approve_days = round(stage_sums.get('mat_digital_approve', 0.0), 2)
            rec.duration_dept_digital_days = round(rec.duration_digital_exec_days + rec.duration_digital_approve_days, 2)

            rec.duration_ops_exec_days = round(stage_sums.get('mat_ops_exec', 0.0), 2)
            rec.duration_ops_approve_days = round(stage_sums.get('mat_ops_approve', 0.0), 2)
            rec.duration_dept_ops_days = round(rec.duration_ops_exec_days + rec.duration_ops_approve_days, 2)

    def action_open_task_dialog(self):
        task_id = self.env.context.get('click_task_id')
        if task_id:
            return {
                'name': _('Marketing Task'),
                'type': 'ir.actions.act_window',
                'res_model': 'bussma.marketing.task',
                'res_id': task_id,
                'view_mode': 'form',
                'target': 'new',
            }

    def _is_user_authorized_supervisor(self):
        self.ensure_one()
        user = self.env.user
        # 1. Marketing Supervisor
        if user.has_group('marketing_opportunity_management.group_marketing_supervisor'):
            return True

        # 2. Responsible for Marketing Material
        if self.user_id and self.user_id == user:
            return True

        # 3. Department Manager
        dept_id = self.env.context.get('click_department_id')
        if dept_id and isinstance(dept_id, int):
            dept = self.env['bussma.marketing.department'].browse(dept_id)
            if dept and dept.manager_id and dept.manager_id == user:
                return True
        if self.department_ids and any(d.manager_id and d.manager_id == user for d in self.department_ids):
            return True

        if self.stage_id and self.stage_id.department_id and self.stage_id.department_id.manager_id and self.stage_id.department_id.manager_id == user:
            return True

        return False

    def action_create_task_dialog(self):
        self.ensure_one()
        if not self._is_user_authorized_supervisor():
            raise UserError(_("Task creation is restricted to the marketing supervisor, marketing material responsible, or department manager only."))
        dept_id = self.env.context.get('click_department_id')
        ctx = {
            'default_material_id': self.id,
            'default_marketing_id': self.marketing_id.id if self.marketing_id else False,
        }
        if dept_id and isinstance(dept_id, int):
            ctx['default_department_id'] = dept_id
        return {
            'name': _('Add New Task'),
            'type': 'ir.actions.act_window',
            'res_model': 'bussma.marketing.task',
            'view_mode': 'form',
            'target': 'new',
            'context': ctx,
        }

    def action_send_to_content_approval(self):
        self.ensure_one()
        stage = self.env.ref('marketing_opportunity_management.stage_mat_content_approve', raise_if_not_found=False)
        if stage:
            self.stage_id = stage.id

    def _action_view_dept_returns(self, stage_selection):
        self.ensure_one()
        return {
            'name': _('Return Records'),
            'type': 'ir.actions.act_window',
            'res_model': 'bussma.material.stage.history',
            'view_mode': 'list',
            'domain': [
                ('material_id', '=', self.id),
                ('is_return', '=', True),
                ('stage_id.material_stage_selection', '=', stage_selection),
            ],
            'context': {'create': False, 'delete': False},
        }

    def action_view_content_returns(self):
        return self._action_view_dept_returns('mat_content_exec')

    def action_view_design_returns(self):
        return self._action_view_dept_returns('mat_design_exec')

    def action_view_digital_returns(self):
        return self._action_view_dept_returns('mat_digital_exec')

    def action_view_ops_returns(self):
        return self._action_view_dept_returns('mat_ops_exec')

    def action_send_to_design_exec(self):
        self.ensure_one()
        stage = self.env.ref('marketing_opportunity_management.stage_mat_design_exec', raise_if_not_found=False)
        if stage:
            self.stage_id = stage.id

    def action_send_to_design_approval(self):
        self.ensure_one()
        stage = self.env.ref('marketing_opportunity_management.stage_mat_design_approve', raise_if_not_found=False)
        if stage:
            self.stage_id = stage.id

    def action_send_to_digital_exec(self):
        self.ensure_one()
        stage = self.env.ref('marketing_opportunity_management.stage_mat_design_exec', raise_if_not_found=False)
        stage = self.env.ref('marketing_opportunity_management.stage_mat_digital_exec', raise_if_not_found=False)
        if stage:
            self.stage_id = stage.id

    def action_send_to_digital_approval(self):
        self.ensure_one()
        stage = self.env.ref('marketing_opportunity_management.stage_mat_digital_approve', raise_if_not_found=False)
        if stage:
            self.stage_id = stage.id

    def action_send_to_ops_exec(self):
        self.ensure_one()
        stage = self.env.ref('marketing_opportunity_management.stage_mat_ops_exec', raise_if_not_found=False)
        if stage:
            self.stage_id = stage.id

    def action_send_to_ops_approval(self):
        self.ensure_one()
        stage = self.env.ref('marketing_opportunity_management.stage_mat_ops_approve', raise_if_not_found=False)
        if stage:
            self.stage_id = stage.id
    
    @api.depends('marketing_id', 'marketing_id.bussma_project_id', 'marketing_id.bussma_project_id.project_manager_id', 'marketing_id.is_opportunity_request', 'marketing_id.opportunity_id', 'marketing_id.is_office_request', 'marketing_id.office_request_id', 'marketing_id.office_request_id.requested_by_id', 'marketing_id.requested_by_id')
    @api.depends_context('uid')
    def _compute_is_project_manager(self):
        user = self.env.user
        has_opp_group = user.has_group('marketing_opportunity_management.group_opportunity_management')
        for rec in self:
            is_pm = False
            if rec.marketing_id:
                mkt = rec.marketing_id
                if mkt.bussma_project_id and getattr(mkt.bussma_project_id, 'project_manager_id', False) == user:
                    is_pm = True
                elif mkt.is_opportunity_request or mkt.opportunity_id:
                    if has_opp_group:
                        is_pm = True
                elif mkt.is_office_request or mkt.office_request_id:
                    off_req = mkt.sudo().office_request_id
                    req_by = (off_req and off_req.requested_by_id) or mkt.requested_by_id
                    if req_by and req_by == user:
                        is_pm = True
                elif mkt.requested_by_id and mkt.requested_by_id == user:
                    is_pm = True
            rec.is_project_manager = is_pm

    def action_send_to_mat_marketing_approve(self):
        self.ensure_one()
        stage = self.env.ref('marketing_opportunity_management.stage_mat_marketing_approve', raise_if_not_found=False)
        if stage:
            self.stage_id = stage.id

    def _get_project_manager_and_source_name(self):
        self.ensure_one()
        pm_users = self.env['res.users']
        source_name = ''
        if self.marketing_id:
            mkt = self.marketing_id
            if mkt.bussma_project_id and mkt.bussma_project_id.project_manager_id:
                pm_users |= mkt.bussma_project_id.project_manager_id
                source_name = mkt.bussma_project_id.name or mkt.name or ''
            elif mkt.is_opportunity_request or mkt.opportunity_id:
                opp_members = self.env['bussma.opportunity.department'].get_opportunity_members()
                if opp_members:
                    pm_users |= opp_members
                source_name = (mkt.opportunity_id and mkt.opportunity_id.name) or mkt.name or ''
            elif mkt.is_office_request or mkt.office_request_id:
                off_req = mkt.sudo().office_request_id
                requester = (off_req and off_req.requested_by_id) or mkt.requested_by_id
                if requester:
                    pm_users |= requester
                source_name = (off_req and off_req.name) or mkt.name or ''
            elif mkt.requested_by_id:
                pm_users |= mkt.requested_by_id
                source_name = mkt.name or ''
        return pm_users, source_name

    def _send_pm_approval_request_email(self):
        template = self.env.ref('marketing_opportunity_management.email_template_marketing_material_sent_to_pm', raise_if_not_found=False)
        if not template:
            _logger.warning("[Material Email] Template email_template_marketing_material_sent_to_pm not found")
            return
        for rec in self:
            pm_users, source_name = rec._get_project_manager_and_source_name()
            valid_users = pm_users.filtered(lambda u: u.email and u.email.strip()) if pm_users else self.env['res.users']
            if not valid_users:
                _logger.warning("[Material Email] No PM email found for material ID %s", rec.id)
                continue
            emails = list(set(u.email.strip() for u in valid_users))
            email_to_str = ','.join(emails)
            pm_name_str = ', '.join([u.name for u in valid_users if u.name])
            mkt = rec.marketing_id
            is_opp = bool(mkt and (mkt.is_opportunity_request or mkt.opportunity_id))

            target_model = False
            target_id = False
            if is_opp and mkt and mkt.opportunity_id:
                target_model = 'bussma.opportunity'
                target_id = mkt.opportunity_id.id
            elif mkt and mkt.bussma_project_id:
                target_model = 'bussma.project'
                target_id = mkt.bussma_project_id.id
            elif mkt and (mkt.is_office_request or mkt.office_request_id) and mkt.office_request_id:
                target_model = 'office.request'
                target_id = mkt.office_request_id.id
            elif mkt:
                target_model = 'bussma.marketing'
                target_id = mkt.id
            else:
                target_model = rec._name
                target_id = rec.id

            base_url = rec.get_base_url()
            target_url = f"{base_url}/web#id={target_id}&model={target_model}&view_type=form"

            ctx = dict(
                self.env.context,
                pm_name=pm_name_str,
                source_project_name=source_name,
                is_opportunity=is_opp,
                target_model=target_model,
                target_id=target_id,
                target_url=target_url,
            )
            try:
                email_values = {
                    'email_to': email_to_str,
                    'email_from': self.env.user.email or self.env.company.email,
                    'model': False,
                    'res_id': False,
                }
                template.with_context(ctx).send_mail(rec.id, force_send=True, email_values=email_values)
            except Exception as e:
                _logger.error("Failed to send PM approval request email for material %s: %s", rec.id, str(e))

    def _update_opportunity_stage_on_first_material_send(self):
        self.ensure_one()
        if self.marketing_id and (self.marketing_id.is_opportunity_request or self.marketing_id.opportunity_id):
            opp = self.marketing_id.opportunity_id
            if opp:
                final_stage = self.env.ref('marketing_opportunity_management.stage_opportunity_final_material', raise_if_not_found=False)
                if final_stage and opp.stage_id != final_stage:
                    if opp.opportunity_stage_selection in ['opp_draft', 'opp_data_completion', 'opp_marketing_request']:
                        opp.sudo().write({'stage_id': final_stage.id})

    def action_send_to_pm_approval(self):
        self.ensure_one()
        stage = self.env.ref('marketing_opportunity_management.stage_mat_pm_approve', raise_if_not_found=False)
        if stage:
            self.write({'stage_id': stage.id})
            self._send_pm_approval_request_email()
            self._update_opportunity_stage_on_first_material_send()

    def action_approve_complete_material(self):
        self.ensure_one()
        stage = self.env.ref('marketing_opportunity_management.stage_mat_done', raise_if_not_found=False)
        if stage:
            self.write({'stage_id': stage.id})

    def action_pm_approve_material(self):
        self.ensure_one()
        stage = self.env.ref('marketing_opportunity_management.stage_mat_done', raise_if_not_found=False)
        if stage:
            self.with_context(bypass_marketing_check=True).write({'stage_id': stage.id})
            self._send_material_pm_approved_notification()

    def action_pm_reject_material(self):
        self.ensure_one()
        if not self.pm_rejection_notes:
            raise ValidationError(_("Please enter project manager return notes before rejecting."))
        stage = self.env.ref('marketing_opportunity_management.stage_mat_marketing_approve', raise_if_not_found=False)
        if stage:
            self.with_context(bypass_marketing_check=True).write({'stage_id': stage.id})

    def action_open_pm_approval_wizard(self):
        self.ensure_one()
        window_title = _('Project Manager Decision for Marketing Material')
        if self.marketing_id:
            mkt = self.marketing_id
            if mkt.is_opportunity_request or mkt.opportunity_id:
                window_title = _('Opportunity Management Decision for Marketing Material')
            elif mkt.is_office_request or mkt.office_request_id:
                window_title = _('Service Requester Decision for Marketing Material')

        return {
            'name': window_title,
            'type': 'ir.actions.act_window',
            'res_model': 'bussma.material.pm.approval.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_material_id': self.id,
                'default_pm_rejection_notes': self.pm_rejection_notes or '',
            }
        }

    def action_open_request_modification_wizard(self):
        self.ensure_one()
        return {
            'name': _('Request Marketing Material Modification'),
            'type': 'ir.actions.act_window',
            'res_model': 'bussma.material.request.modification.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_material_id': self.id,
            }
        }

    def action_view_return_notes(self):
        self.ensure_one()
        return {
            'name': _('Return Notes'),
            'type': 'ir.actions.act_window',
            'res_model': 'bussma.material.return.note',
            'view_mode': 'list,form',
            'domain': [('material_id', '=', self.id)],
            'context': {'create': False, 'delete': False, 'edit': False},
        }

    def action_view_modification_returns(self):
        self.ensure_one()
        return {
            'name': _('Modification Return Notes'),
            'type': 'ir.actions.act_window',
            'res_model': 'bussma.material.return.note',
            'view_mode': 'list,form',
            'domain': [('material_id', '=', self.id), ('return_type', '=', 'modification')],
            'context': {'default_material_id': self.id, 'default_return_type': 'modification'},
        }

    def action_view_rejection_returns(self):
        self.ensure_one()
        return {
            'name': _('Rejection Return Notes'),
            'type': 'ir.actions.act_window',
            'res_model': 'bussma.material.return.note',
            'view_mode': 'list,form',
            'domain': [('material_id', '=', self.id), ('return_type', '=', 'rejected')],
            'context': {'default_material_id': self.id, 'default_return_type': 'rejected'},
        }

    def action_reject_content_approval(self):
        self.ensure_one()
        if not self.content_supervisor_notes:
            raise ValidationError(_("Please enter content supervisor notes before returning the record."))
        stage = self.env.ref('marketing_opportunity_management.stage_mat_content_exec', raise_if_not_found=False)
        if stage:
            self.write({'stage_id': stage.id, 'content_supervisor_approval': 'reject'})

    def action_reject_design_approval(self):
        self.ensure_one()
        if not self.design_supervisor_notes:
            raise ValidationError(_("Please enter design supervisor notes before returning the record."))
        stage = self.env.ref('marketing_opportunity_management.stage_mat_design_exec', raise_if_not_found=False)
        if stage:
            self.write({'stage_id': stage.id, 'design_supervisor_approval': 'reject'})

    def action_reject_digital_approval(self):
        self.ensure_one()
        if not self.digital_supervisor_notes:
            raise ValidationError(_("Please enter digital supervisor notes before returning the record."))
        stage = self.env.ref('marketing_opportunity_management.stage_mat_digital_exec', raise_if_not_found=False)
        if stage:
            self.write({'stage_id': stage.id, 'digital_supervisor_approval': 'reject'})

    def action_reject_ops_approval(self):
        self.ensure_one()
        if not self.ops_supervisor_notes:
            raise ValidationError(_("Please enter operations supervisor notes before returning the record."))
        stage = self.env.ref('marketing_opportunity_management.stage_mat_ops_exec', raise_if_not_found=False)
        if stage:
            self.write({'stage_id': stage.id, 'ops_supervisor_approval': 'reject'})

    def _send_user_assigned_notification(self):
        template = self.env.ref('marketing_opportunity_management.email_template_marketing_material_user_assigned', raise_if_not_found=False)
        for rec in self:
            if rec.user_id and rec.user_id.email and template:
                try:
                    email_values = {
                        'email_to': rec.user_id.email,
                        'email_from': self.env.user.email or self.env.company.email,
                        'model': False,
                        'res_id': False,
                    }
                    template.send_mail(rec.id, force_send=True, email_values=email_values)
                    _logger.info("[Marketing Material Email] Sent user assignment notification to %s for material ID %s", rec.user_id.email, rec.id)
                except Exception as e:
                    _logger.error("Failed to send material user assignment email for material %s: %s", rec.id, str(e))

    def _send_material_supervisor_approval_notification(self):
        template = self.env.ref('marketing_opportunity_management.email_template_marketing_material_completed_to_supervisor', raise_if_not_found=False)
        if not template:
            return
        group_supervisor = self.env.ref('marketing_opportunity_management.group_marketing_supervisor', raise_if_not_found=False)
        if not group_supervisor:
            return
        users = group_supervisor.users.filtered(lambda u: u.active and u.email)
        emails = [u.email.strip() for u in users if u.email]
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
                _logger.info("[Material Email] Sent supervisor approval notification to %s for material ID %s", email_to, rec.id)
            except Exception as e:
                _logger.error("Failed to send supervisor approval notification for material %s: %s", rec.id, str(e))

    def _send_material_pm_rejected_notification(self):
        template = self.env.ref('marketing_opportunity_management.email_template_marketing_material_rejected_by_pm', raise_if_not_found=False)
        if not template:
            _logger.warning("[Material Email] Template email_template_marketing_material_rejected_by_pm not found")
            return
        new_subj = _("Notification: Marketing Material {{ object.name }} ({{ object.code or '' }}) Rejected by {{ 'Opportunity Department' if (ctx.get('is_opportunity') or object.is_opportunity_request or (object.marketing_id and (object.marketing_id.is_opportunity_request or object.marketing_id.opportunity_id))) else 'Project Manager' }}")
        template_en_subject = template.with_context(lang='en_US').subject or ''
        if 'Opportunity Department' not in template_en_subject:
            try:
                template.sudo().write({'subject': new_subj})
            except Exception:
                pass
        group_supervisor = self.env.ref('marketing_opportunity_management.group_marketing_supervisor', raise_if_not_found=False)
        if not group_supervisor:
            return
        users = group_supervisor.users.filtered(lambda u: u.active and u.email)
        emails = [u.email.strip() for u in users if u.email]
        if not emails:
            return
        email_to = ",".join(set(emails))
        for rec in self:
            is_opp = bool(rec.is_opportunity_request or (rec.marketing_id and (rec.marketing_id.is_opportunity_request or rec.marketing_id.opportunity_id)))
            ctx = dict(self.env.context, is_opportunity=is_opp)
            try:
                email_values = {
                    'email_to': email_to,
                    'email_from': self.env.company.email or self.env.user.email,
                    'model': False,
                    'res_id': False,
                }
                template.with_context(ctx).send_mail(rec.id, force_send=True, email_values=email_values)
            except Exception as e:
                _logger.error("Failed to send PM rejection notification for material %s: %s", rec.id, str(e))

    def _send_material_pm_approved_notification(self):
        template = self.env.ref('marketing_opportunity_management.email_template_marketing_material_approved_by_pm', raise_if_not_found=False)
        if not template:
            return
        group_supervisor = self.env.ref('marketing_opportunity_management.group_marketing_supervisor', raise_if_not_found=False)
        if not group_supervisor:
            return
        users = group_supervisor.users.filtered(lambda u: u.active and u.email)
        emails = [u.email.strip() for u in users if u.email]
        if not emails:
            return
        email_to = ",".join(set(emails))
        for rec in self:
            try:
                email_values = {
                    'email_to': email_to,
                    'email_from': self.env.company.email or self.env.user.email,
                    'model': False,
                    'res_id': False,
                }
                template.send_mail(rec.id, force_send=True, email_values=email_values)
            except Exception as e:
                _logger.error("Failed to send PM approval notification for material %s: %s", rec.id, str(e))

    def _send_material_returned_to_execution_notification(self, old_stage):
        template = self.env.ref('marketing_opportunity_management.email_template_marketing_material_returned_to_execution', raise_if_not_found=False)
        if not template:
            _logger.warning("[Material Email] Template email_template_marketing_material_returned_to_execution not found")
            return
        for rec in self:
            dept = rec.stage_id.department_id if rec.stage_id and rec.stage_id.department_id else (old_stage.department_id if old_stage else False)
            recipient_emails = set()
            non_cancel_tasks = rec.task_ids.filtered(lambda t: t.state != 'cancel')
            if dept:
                dept_tasks = non_cancel_tasks.filtered(
                    lambda t: (t.department_id and t.department_id.id == dept.id) or
                              (t.department_id.code and dept.code and t.department_id.code == dept.code)
                )
                for t in dept_tasks:
                    for u in t.user_ids.filtered(lambda u: u.active and u.email):
                        recipient_emails.add(u.email.strip())
            if not recipient_emails and non_cancel_tasks:
                for t in non_cancel_tasks:
                    for u in t.user_ids.filtered(lambda u: u.active and u.email):
                        recipient_emails.add(u.email.strip())

            if not recipient_emails and rec.user_id and rec.user_id.active and rec.user_id.email:
                recipient_emails.add(rec.user_id.email.strip())
            if not recipient_emails:
                _logger.warning("[Material Email] No task assignees with emails found for return notification on material ID %s", rec.id)
                continue
            email_to = ",".join(recipient_emails)
            old_stage_name = old_stage.name if old_stage else ''
            ctx = dict(self.env.context, old_stage_name=old_stage_name)
            try:
                email_values = {
                    'email_to': email_to,
                    'email_from': self.env.user.email or self.env.company.email,
                    'model': False,
                    'res_id': False,
                }
                template.with_context(ctx).send_mail(rec.id, force_send=True, email_values=email_values)
                _logger.info("[Material Email] Sent material return notification to %s for material ID %s", email_to, rec.id)
            except Exception as e:
                _logger.error("Failed to send material return notification for material %s: %s", rec.id, str(e))

    @api.model_create_multi
    def create(self, vals_list):
        records = super(BussmaMarketingMaterial, self).create(vals_list)
        now = fields.Datetime.now()
        for rec in records:
            if rec.user_id:
                rec._send_user_assigned_notification()
            if rec.stage_id and rec.stage_id.material_stage_selection != 'mat_marketing_approve':
                self.env['bussma.material.stage.history'].create({
                    'material_id': rec.id,
                    'stage_id': rec.stage_id.id,
                    'start_date': now,
                })
        return records

    def write(self, vals):
        if 'stage_id' in vals:
            now = fields.Datetime.now()
            new_stage = self.env['request.stage'].browse(vals['stage_id'])
            new_stage_sel = new_stage.material_stage_selection if new_stage else False
            # Mapping from exec stage selection → approve stage selection of same department
            _exec_to_approve_map = {
                'mat_content_exec': 'mat_content_approve',
                'mat_design_exec': 'mat_design_approve',
                'mat_digital_exec': 'mat_digital_approve',
                'mat_ops_exec': 'mat_ops_approve',
            }
            for rec in self:
                if rec.stage_id and rec.stage_id.id != new_stage.id:
                    open_histories = rec.stage_history_ids.filtered(lambda h: not h.end_date)
                    if open_histories:
                        open_histories.write({'end_date': now})
                    if new_stage_sel != 'mat_marketing_approve':
                        # Detect return: moving BACKWARDS to any _exec stage counts as a return for that department
                        is_return = False
                        if new_stage_sel in _exec_to_approve_map:
                            if new_stage.sequence < rec.stage_id.sequence:
                                is_return = True
                        self.env['bussma.material.stage.history'].create({
                            'material_id': rec.id,
                            'stage_id': new_stage.id,
                            'start_date': now,
                            'is_return': is_return,
                            'returned_by_user_id': self.env.uid if is_return else False,
                        })
        if not self.env.su and not self._context.get('bypass_marketing_check'):
            restricted_fields = {'name', 'user_id', 'department_ids'}
            if restricted_fields.intersection(vals.keys()):
                if not self.env.user.has_group('marketing_opportunity_management.group_marketing_supervisor'):
                    raise UserError(_("Editing the marketing material name and departments is restricted to the marketing supervisor only."))

        if 'stage_id' in vals:
            target_stage = self.env['request.stage'].browse(vals['stage_id'])
            user = self.env.user
            is_mkt_supervisor = user.has_group('base.group_system') or user.has_group('marketing_opportunity_management.group_marketing_supervisor')

            for rec in self:
                is_moving_forward = bool(rec.stage_id and target_stage and target_stage.sequence > rec.stage_id.sequence)
                if is_moving_forward and rec.stage_id != target_stage and not self.env.su and not self._context.get('bypass_marketing_check'):
                    rec._check_stage_change_permission(rec.stage_id, target_stage)

                    target_dept = target_stage.department_id
                    stage_sel = target_stage.material_stage_selection or ''

                    if stage_sel.endswith('_exec'):
                        is_dept_manager = target_dept and target_dept.manager_id == user
                        is_dept_member = target_dept and user in target_dept.member_ids
                        if not (is_mkt_supervisor or is_dept_manager or is_dept_member):
                            raise UserError(_("Sorry, only the marketing supervisor or department manager or department members have permission to move the record to the execution stage of (%s).", target_dept.name if target_dept else 'Department'))
                    elif stage_sel == 'mat_marketing_approve':
                        if not (is_mkt_supervisor or rec.is_project_manager):
                            raise UserError(_("Sorry, only the marketing supervisor has permission to move the record to the marketing supervisor approval stage."))
                    elif stage_sel.endswith('_approve'):
                        is_dept_manager = target_dept and target_dept.manager_id == user
                        if not (is_mkt_supervisor or is_dept_manager):
                            raise UserError(_("Sorry, only the marketing supervisor or department manager has permission to move the record to the approval stage of (%s).", target_dept.name if target_dept else 'Department'))

                if target_stage:
                    if target_stage.material_stage_selection == 'mat_marketing_approve':
                        unapproved_tasks = rec.task_ids.filtered(lambda t: t.state not in ['approved', 'cancel'])
                        if unapproved_tasks:
                            task_names = "\n- ".join([
                                f"{t.name} ({t.department_id.name if t.department_id else _('No Department')})"
                                for t in unapproved_tasks
                            ])
                            raise UserError(_("Can't move record to stage '%s' because there are tasks that have not been approved or cancelled yet:\n- %s", target_stage.name, task_names))

                    elif rec.stage_id and target_stage.sequence > rec.stage_id.sequence:
                        all_mat_stages = self.env['request.stage'].search([
                            ('res_model', '=', 'bussma.marketing.material')
                        ])
                        dept_max_seq = {}
                        for st in all_mat_stages:
                            if st.department_id:
                                dept_id = st.department_id.id
                                if dept_id not in dept_max_seq or st.sequence > dept_max_seq[dept_id]['max_seq']:
                                    dept_max_seq[dept_id] = {
                                        'dept': st.department_id,
                                        'max_seq': st.sequence
                                    }

                        for dept_id, dept_info in dept_max_seq.items():
                            if target_stage.sequence > dept_info['max_seq']:
                                dept = dept_info['dept']
                                dept_tasks = rec.task_ids.filtered(
                                    lambda t: (t.department_id and t.department_id.id == dept.id) or
                                              (t.department_id.code and dept.code and t.department_id.code == dept.code)
                                )
                                unapproved_tasks = dept_tasks.filtered(lambda t: t.state not in ['approved', 'cancel'])
                                if unapproved_tasks:
                                    task_names = "\n- ".join(unapproved_tasks.mapped('name'))
                                    raise UserError(_("Can't move record to stage '%s' because there are tasks for (%s) that have not been approved or cancelled yet:\n- %s", target_stage.name, dept.name, task_names))

        old_users = {rec.id: rec.user_id for rec in self}
        old_stage_objs = {rec.id: rec.stage_id for rec in self}
        res = super(BussmaMarketingMaterial, self).write(vals)

        # Auto-adjust stage when needs_content changes (computed from department_ids)
        for rec in self:
            if rec.needs_content == 'no':
                content_stage = self.env.ref(
                    'marketing_opportunity_management.stage_mat_content_exec',
                    raise_if_not_found=False
                )
                design_stage = self.env.ref(
                    'marketing_opportunity_management.stage_mat_design_exec',
                    raise_if_not_found=False
                )
                if content_stage and design_stage and rec.stage_id == content_stage:
                    rec.stage_id = design_stage.id

        if 'user_id' in vals:
            for rec in self:
                if rec.user_id and rec.user_id != old_users.get(rec.id):
                    rec._send_user_assigned_notification()

        if 'stage_id' in vals:
            target_stage = self.env['request.stage'].browse(vals['stage_id'])
            for rec in self:
                old_st = old_stage_objs.get(rec.id)
                old_sel = old_st.material_stage_selection if old_st else False
                new_sel = rec.stage_id.material_stage_selection if rec.stage_id else False

                if old_st != rec.stage_id:
                    rec._notify_stage_authorized_users()

                if old_st and target_stage and target_stage.sequence > old_st.sequence:
                    rec.supervisor_notes = False
                    rec.supervisor_attachment_ids = [(5, 0, 0)]

                if rec.stage_id and new_sel == 'mat_marketing_approve' and old_sel != 'mat_marketing_approve':
                    if old_sel == 'mat_pm_approve':
                        rec._send_material_pm_rejected_notification()
                    elif old_sel in [
                        'mat_content_exec', 'mat_content_approve',
                        'mat_design_exec', 'mat_design_approve',
                        'mat_digital_exec', 'mat_digital_approve',
                        'mat_ops_exec', 'mat_ops_approve'
                    ]:
                        rec._send_material_supervisor_approval_notification()

                if old_st and rec.stage_id and rec.stage_id.sequence < old_st.sequence and old_sel != 'mat_pm_approve':
                    rec._send_material_returned_to_execution_notification(old_st)

            self.mapped('marketing_id')._check_and_move_to_supervisor_approval()

        return res


class BussmaMaterialStageHistory(models.Model):
    _name = 'bussma.material.stage.history'
    _description = 'Marketing Material Stage History'
    _order = 'start_date desc'

    material_id = fields.Many2one(
        'bussma.marketing.material',
        string='Marketing Material',
        ondelete='cascade',
        required=True
    )
    stage_id = fields.Many2one(
        'request.stage',
        string='Stage',
        required=True,
        domain="[('res_model', '=', 'bussma.marketing.material')]"
    )
    start_date = fields.Datetime(
        string='Start Date',
        default=fields.Datetime.now,
        required=True
    )
    end_date = fields.Datetime(
        string='End Date'
    )
    duration_days = fields.Float(
        string='Duration (Days)',
        compute='_compute_duration',
        store=True,
        digits=(16, 2),
        help='Duration in days. Example: 1.5 = 1 day and 12 hours'
    )
    is_return = fields.Boolean(
        string='Is Return',
        default=False,
        help='True if this history entry was created due to a return from an approval stage back to execution'
    )
    returned_by_user_id = fields.Many2one(
        'res.users',
        string='Returned By',
        help='The user who performed the return from approval to execution'
    )

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        now = fields.Datetime.now()
        tz_name = self.env.user.tz or 'Asia/Riyadh'
        try:
            tz = pytz.timezone(tz_name)
        except Exception:
            tz = pytz.timezone('Asia/Riyadh')

        valid_recs = [rec for rec in self if rec.start_date]
        for rec in self:
            if not rec.start_date:
                rec.duration_days = 0.0

        if not valid_recs:
            return

        min_start = min(rec.start_date for rec in valid_recs)
        max_end = max((rec.end_date or now) for rec in valid_recs)

        leaves = self.env['resource.calendar.leaves'].search([
            ('date_from', '<=', max_end),
            ('date_to', '>=', min_start),
        ])

        holiday_dates = set()
        for l in leaves:
            if not l.date_from or not l.date_to:
                continue
            dt_from = pytz.UTC.localize(l.date_from).astimezone(tz) if not l.date_from.tzinfo else l.date_from.astimezone(tz)
            dt_to = pytz.UTC.localize(l.date_to).astimezone(tz) if not l.date_to.tzinfo else l.date_to.astimezone(tz)
            cur_d = dt_from.date()
            end_d = dt_to.date()
            while cur_d <= end_d:
                holiday_dates.add(cur_d)
                cur_d += timedelta(days=1)

        for rec in valid_recs:
            end = rec.end_date or now
            if end <= rec.start_date:
                rec.duration_days = 0.0
                continue

            start_tz = pytz.UTC.localize(rec.start_date).astimezone(tz) if not rec.start_date.tzinfo else rec.start_date.astimezone(tz)
            end_tz = pytz.UTC.localize(end).astimezone(tz) if not end.tzinfo else end.astimezone(tz)

            total_working_seconds = 0.0
            cur_d = start_tz.date()
            end_d = end_tz.date()

            while cur_d <= end_d:
                # Friday (4) and Saturday (5) are weekend days in Saudi Arabia
                if cur_d.weekday() in (4, 5) or cur_d in holiday_dates:
                    cur_d += timedelta(days=1)
                    continue

                day_start = tz.localize(datetime.combine(cur_d, datetime.min.time()))
                day_next = tz.localize(datetime.combine(cur_d + timedelta(days=1), datetime.min.time()))

                overlap_start = max(start_tz, day_start)
                overlap_end = min(end_tz, day_next)

                if overlap_end > overlap_start:
                    total_working_seconds += (overlap_end - overlap_start).total_seconds()

                cur_d += timedelta(days=1)

            rec.duration_days = round(total_working_seconds / 86400.0, 2)
