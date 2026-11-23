import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

DEPT_STAGE_SELECTIONS = [
    'hr_dept_commercial',
    'hr_dept_projects',
    'hr_dept_marketing',
    'hr_dept_legal',
    'hr_dept_finance',
    'hr_dept_hr',
    'hr_dept_assets',
    'hr_dept_it',
    'hr_dept_executive',
]
DEPT_APPROVAL_FIELD_MAP = {
    'hr_dept_commercial': ('dept_commercial_manager_approval', 'dept_commercial_manager_notes'),
    'hr_dept_projects':   ('dept_projects_manager_approval', 'dept_projects_manager_notes'),
    'hr_dept_marketing':  ('dept_marketing_manager_approval', 'dept_marketing_manager_notes'),
    'hr_dept_legal':      ('dept_legal_manager_approval', 'dept_legal_manager_notes'),
    'hr_dept_finance':    ('dept_finance_manager_approval', 'dept_finance_manager_notes'),
    'hr_dept_hr':         ('dept_hr_manager_approval', 'dept_hr_manager_notes'),
    'hr_dept_assets':     ('dept_assets_manager_approval', 'dept_assets_manager_notes'),
    'hr_dept_it':         ('dept_it_manager_approval', 'dept_it_manager_notes'),
    'hr_dept_executive':  ('dept_executive_manager_approval', 'dept_executive_manager_notes'),
}
DEPT_MANAGER_FIELD_MAP = {
    'hr_dept_commercial': 'dept_commercial_manager_id',
    'hr_dept_projects':   'dept_projects_manager_id',
    'hr_dept_marketing':  'dept_marketing_manager_id',
    'hr_dept_legal':      'dept_legal_manager_id',
    'hr_dept_finance':    'dept_finance_manager_id',
    'hr_dept_hr':         'dept_hr_manager_id',
    'hr_dept_assets':     'dept_assets_manager_id',
    'hr_dept_it':         'dept_it_manager_id',
    'hr_dept_executive':  'dept_executive_manager_id',
}
DEPT_NAME_MAP = {
    'hr_dept_commercial': 'Commercial Sector Management',
    'hr_dept_projects':   'Project Management',
    'hr_dept_marketing':  'Marketing Management',
    'hr_dept_legal':      'Legal Management',
    'hr_dept_finance':    'Financial Management',
    'hr_dept_hr':         'Human Resources Management',
    'hr_dept_assets':     'Assets & Investment Management',
    'hr_dept_it':         'IT Management',
    'hr_dept_executive':  'Executive Management',
}
# hr_stage_selection values that are ALWAYS visible (fixed stages)
FIXED_STAGE_SELECTIONS = [
    'hr_draft',
    'hr_submitted',
    'hr_approval',
    'hr_approved',
    'hr_rejected',
]


class HrRequest(models.Model):
    _name = 'hr.request'
    _description = 'HR Request'
    _inherit = ['request', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # ─────────────────────────────────────────────
    # Stage helpers
    # ─────────────────────────────────────────────
    def _default_stage_id(self):
        if self.env.context.get('default_is_clearance'):
            stage = self.env.ref('hr_requests.stage_clearance_draft', raise_if_not_found=False)
            if stage:
                return stage.id
            req_type = self.env.ref('hr_requests.request_type_clearance', raise_if_not_found=False)
            if req_type:
                stage = self.env['request.stage'].search(
                    [('request_type_ids', 'in', req_type.id)],
                    order='sequence asc', limit=1
                )
                return stage.id if stage else False
            return False

        req_type = self.env.ref('hr_requests.request_type_hr', raise_if_not_found=False)
        if req_type:
            stage = self.env.ref('hr_requests.stage_hr_draft', raise_if_not_found=False)
            if stage:
                return stage.id
            stage = self.env['request.stage'].search(
                [('request_type_ids', 'in', req_type.id)],
                order='sequence asc', limit=1
            )
            return stage.id if stage else False
        return False

    def _default_dept_line_id(self):
        if self.env.context.get('default_is_clearance'):
            return False
        draft_line = self.env.ref('hr_requests.dept_line_draft', raise_if_not_found=False)
        if not draft_line:
            draft_line = self.env['hr.request.dept.line'].search([
                ('is_fixed', '=', True),
                ('fixed_stage', '=', 'draft')
            ], limit=1)
        return draft_line

    @api.model
    def _read_group_stage_ids(self, stages, domain=None, order=None):
        if self.env.context.get('default_is_clearance') or (domain and ('is_clearance', '=', True) in domain):
            req_type = self.env.ref('hr_requests.request_type_clearance', raise_if_not_found=False)
            if req_type:
                return self.env['request.stage'].search(
                    [('request_type_ids', 'in', req_type.id)],
                    order='sequence asc'
                )
        else:
            req_type = self.env.ref('hr_requests.request_type_hr', raise_if_not_found=False)
            if req_type:
                # In kanban/list we show only fixed stages to avoid per-record clutter
                return self.env['request.stage'].search(
                    [
                        ('request_type_ids', 'in', req_type.id),
                        ('hr_stage_selection', 'in', FIXED_STAGE_SELECTIONS),
                    ],
                    order='sequence asc'
                )
        return self.env['request.stage'].search(
            [('res_model', '=', 'hr.request')],
            order='sequence asc'
        )

    def _default_request_type_id(self):
        if self.env.context.get('default_is_clearance'):
            return self.env.ref('hr_requests.request_type_clearance', raise_if_not_found=False)
        return self.env.ref('hr_requests.request_type_hr', raise_if_not_found=False)

    # ─────────────────────────────────────────────
    # Employee classification
    # ─────────────────────────────────────────────
    @api.model
    def _default_employee_classification(self):
        user = self.env.user
        manager_group_xml_ids = [
            'bussma_system.group_commercial_sector_manager',
            'bussma_system.group_studies_manager',
            'bussma_system.group_sales_manager',
            'bussma_system.group_auctions_manager',
            'financial_management.group_financial_management',
            'marketing_opportunity_management.group_marketing_supervisor',
            'marketing_opportunity_management.group_opportunity_management',
            'hr_requests.group_hr_request_manager',
        ]
        for xml_id in manager_group_xml_ids:
            if user.has_group(xml_id):
                return 'manager'
        return 'employee'
    # ──────────────────────────────────────────────────────────────────────────
    # Department Manager Helpers & Defaults
    # ──────────────────────────────────────────────────────────────────────────
    @api.model
    def _has_user_column(self, col_name):
        """Check if column exists in res_users table before performing search."""
        try:
            self.env.cr.execute("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='res_users' AND column_name=%s
            """, (col_name,))
            return bool(self.env.cr.fetchone())
        except Exception:
            return False

    @api.model
    def _default_hr_user_id(self):
        if not self._has_user_column('is_hr_clearance_user'):
            return False
        user = self.env['res.users'].sudo().search([('is_hr_clearance_user', '=', True), ('active', '=', True)], limit=1)
        return user.id if user else False

    @api.model
    def _default_finance_user_id(self):
        if not self._has_user_column('is_finance_clearance_user'):
            return False
        user = self.env['res.users'].sudo().search([('is_finance_clearance_user', '=', True), ('active', '=', True)], limit=1)
        return user.id if user else False

    @api.model
    def _default_it_user_id(self):
        if not self._has_user_column('is_it_clearance_user'):
            return False
        user = self.env['res.users'].sudo().search([('is_it_clearance_user', '=', True), ('active', '=', True)], limit=1)
        return user.id if user else False

    @api.model
    def _default_legal_user_id(self):
        if not self._has_user_column('is_legal_clearance_user'):
            return False
        user = self.env['res.users'].sudo().search([('is_legal_clearance_user', '=', True), ('active', '=', True)], limit=1)
        return user.id if user else False

    @api.model
    def _default_commercial_manager_id(self):
        if not self._has_user_column('is_commercial_manager_user'):
            return False
        user = self.env['res.users'].sudo().search([('is_commercial_manager_user', '=', True), ('active', '=', True)], limit=1)
        return user.id if user else False

    @api.model
    def _default_projects_manager_id(self):
        if not self._has_user_column('is_projects_manager_user'):
            return False
        user = self.env['res.users'].sudo().search([('is_projects_manager_user', '=', True), ('active', '=', True)], limit=1)
        return user.id if user else False

    @api.model
    def _default_marketing_manager_id(self):
        if not self._has_user_column('is_marketing_manager_user'):
            return False
        user = self.env['res.users'].sudo().search([('is_marketing_manager_user', '=', True), ('active', '=', True)], limit=1)
        return user.id if user else False

    @api.model
    def _default_assets_manager_id(self):
        if not self._has_user_column('is_assets_manager_user'):
            return False
        user = self.env['res.users'].sudo().search([('is_assets_manager_user', '=', True), ('active', '=', True)], limit=1)
        return user.id if user else False

    @api.model
    def _default_executive_manager_id(self):
        if not self._has_user_column('is_executive_manager_user'):
            return False
        user = self.env['res.users'].sudo().search([('is_executive_manager_user', '=', True), ('active', '=', True)], limit=1)
        return user.id if user else False

    # ─────────────────────────────────────────────
    # Request type & Stage
    # ─────────────────────────────────────────────
    request_type_id = fields.Many2one(
        'request.type',
        string='Request Type (System)',
        default=_default_request_type_id
    )
    active = fields.Boolean(default=True)
    stage_id = fields.Many2one(
        'request.stage',
        string='Stage',
        default=_default_stage_id,
        group_expand='_read_group_stage_ids',
        domain="[('res_model', '=', 'hr.request'), ('request_type_ids', '=', request_type_id)]",
        tracking=True,
        readonly=False
    )
    hr_stage_selection = fields.Selection(
        related='stage_id.hr_stage_selection',
        string='Stage Selection',
        store=True
    )
    name = fields.Char(string='Request Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    is_manager = fields.Boolean(string='Is Manager', compute='_compute_is_manager', store=False)
    employee_classification = fields.Selection([
        ('employee', 'Employee Request'),
        ('manager', 'Manager Request'),
    ], string='Employee Classification', required=True, default=_default_employee_classification, tracking=True)
    category_id = fields.Many2one(
        'hr.request.category',
        string='Request Category',
        required=False,
        domain="['|', ('employee_classification', '=', 'employee'), ('employee_classification', '=', employee_classification)]",
        tracking=True
    )
    type_id = fields.Many2one(
        'hr.request.type',
        string='Request Type',
        required=False,
        domain="[('category_id', '=', category_id)]",
        tracking=True
    )
    request_type_code = fields.Char(
        related='type_id.code',
        string='Request Type Code',
        store=True,
        readonly=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        required=True
    )
    date = fields.Date(
        string='Request Date',
        default=fields.Date.context_today,
        required=True
    )
    # Dynamic Department Approvals
    dept_approval_ids = fields.One2many(
        'hr.request.dept.line',
        'request_id',
        string='Department Approvals',
        copy=False,
    )
    has_dept_approvals = fields.Boolean(
        string='Has Department Approvals',
        compute='_compute_has_dept_approvals',
        store=True,
    )

    allowed_dept_line_ids = fields.Many2many(
        'hr.request.dept.line',
        compute='_compute_allowed_dept_line_ids',
        string='Allowed Department Lines',
    )
    dept_line_id = fields.Many2one(
        'hr.request.dept.line',
        string='Approval Stage',
        default=_default_dept_line_id,
        compute='_compute_dept_line_id',
        inverse='_inverse_dept_line_id',
        store=True,
        readonly=False,
        domain="['|', ('is_fixed', '=', True), ('request_id', '=', id)]",
    )
    # ──────────────────────────────────────────────────────────────────────────
    # Department Manager Approvals & Notes (Per Department)
    # ──────────────────────────────────────────────────────────────────────────
    dept_commercial_manager_id = fields.Many2one(
        'res.users', string='Commercial Sector Manager',
        default=_default_commercial_manager_id
    )
    dept_commercial_manager_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Commercial Manager Approval', tracking=True)
    dept_commercial_manager_notes = fields.Text(string='Commercial Manager Notes')

    dept_projects_manager_id = fields.Many2one(
        'res.users', string='Projects Manager',
        default=_default_projects_manager_id
    )
    dept_projects_manager_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Projects Manager Approval', tracking=True)
    dept_projects_manager_notes = fields.Text(string='Projects Manager Notes')

    dept_marketing_manager_id = fields.Many2one(
        'res.users', string='Marketing Manager',
        default=_default_marketing_manager_id
    )
    dept_marketing_manager_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Marketing Manager Approval', tracking=True)
    dept_marketing_manager_notes = fields.Text(string='Marketing Manager Notes')

    dept_legal_manager_id = fields.Many2one(
        'res.users', string='Legal Manager',
        default=_default_legal_user_id
    )
    dept_legal_manager_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Legal Manager Approval', tracking=True)
    dept_legal_manager_notes = fields.Text(string='Legal Manager Notes')

    dept_finance_manager_id = fields.Many2one(
        'res.users', string='Finance Manager',
        default=_default_finance_user_id
    )
    dept_finance_manager_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Finance Manager Approval', tracking=True)
    dept_finance_manager_notes = fields.Text(string='Finance Manager Notes')

    dept_hr_manager_id = fields.Many2one(
        'res.users', string='HR Manager',
        default=_default_hr_user_id
    )
    dept_hr_manager_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='HR Manager Approval', tracking=True)
    dept_hr_manager_notes = fields.Text(string='HR Manager Notes')

    dept_assets_manager_id = fields.Many2one(
        'res.users', string='Assets Manager',
        default=_default_assets_manager_id
    )
    dept_assets_manager_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Assets Manager Approval', tracking=True)
    dept_assets_manager_notes = fields.Text(string='Assets Manager Notes')

    dept_it_manager_id = fields.Many2one(
        'res.users', string='IT Manager',
        default=_default_it_user_id
    )
    dept_it_manager_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='IT Manager Approval', tracking=True)
    dept_it_manager_notes = fields.Text(string='IT Manager Notes')

    dept_executive_manager_id = fields.Many2one(
        'res.users', string='Executive Manager',
        default=_default_executive_manager_id
    )
    dept_executive_manager_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Executive Manager Approval', tracking=True)
    dept_executive_manager_notes = fields.Text(string='Executive Manager Notes')
    # Department Tabs Visibility Flags
    show_dept_commercial = fields.Boolean(compute='_compute_show_dept_tabs')
    show_dept_projects   = fields.Boolean(compute='_compute_show_dept_tabs')
    show_dept_marketing  = fields.Boolean(compute='_compute_show_dept_tabs')
    show_dept_legal      = fields.Boolean(compute='_compute_show_dept_tabs')
    show_dept_finance    = fields.Boolean(compute='_compute_show_dept_tabs')
    show_dept_hr         = fields.Boolean(compute='_compute_show_dept_tabs')
    show_dept_assets     = fields.Boolean(compute='_compute_show_dept_tabs')
    show_dept_it         = fields.Boolean(compute='_compute_show_dept_tabs')
    show_dept_executive  = fields.Boolean(compute='_compute_show_dept_tabs')
    # Return Tracking from Department Rejection
    returned_from_stage_id = fields.Many2one(
        'request.stage',
        string='Returned From Stage',
        domain="[('res_model', '=', 'hr.request'), ('request_type_ids', '=', request_type_id)]",
        copy=False,
    )
    returned_from_dept = fields.Char(
        string='Returned From Department Code',
        copy=False,
    )
    returned_from_dept_notes = fields.Text(
        string='Department Rejection Note',
        compute='_compute_returned_from_dept_notes',
    )
    resend_notes = fields.Text(
        string='Resend Notes',
        tracking=True,
    )
    notified_dept_history = fields.Char(
        string='Notified Department History',
        copy=False,
    )
    request_details = fields.Char(string='Request Details')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'hr_request_attachment_rel',
        'request_id',
        'attachment_id',
        string='Attachments'
    )
    notes = fields.Text(string='Additional Notes')
    # ─ Recruitment Request ─
    job_title = fields.Char(string='Job Title')
    qualification = fields.Selection([
        ('high_school', 'High School'),
        ('diploma', 'Diploma'),
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('phd', 'PhD'),
    ], string='Qualification')
    required_skills = fields.Char(string='Required Skills')
    recruitment_structure = fields.Selection([
        ('new', 'New Employment'),
        ('replacement', 'Replacement Employment'),
    ], string='Employee Structure')
    recruitment_type = fields.Selection([
        ('urgent', 'Urgent'),
        ('non_urgent', 'Non-Urgent'),
    ], string='Recruitment Type')
    branch = fields.Char(string='Branch')
    required_tasks = fields.Text(string='Required Tasks')
    required_experience = fields.Char(string='Required Experience')
    office_department_id = fields.Many2one('office.department', string='Department')
    reason_for_need = fields.Text(string='Reason for Need')
    # ─ Salary Certificate ─
    directed_to = fields.Char(string='Directed To')
    # ─ ID Card ─
    card_name = fields.Char(string='Name', translate=True)
    employee_number = fields.Char(string='Employee Number')
    # ─ Bank Account Change ─
    new_bank_name = fields.Char(string='New Bank Name')
    new_iban = fields.Char(string='New IBAN')
    # ─ Flight Ticket ─
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    # ─ Training Course ─
    course_category = fields.Selection([
        ('tech', 'Technical'),
        ('admin', 'Administrative'),
        ('personal', 'Personal Skills'),
        ('compliance', 'Compliance'),
    ], string='Course Category')
    course_name = fields.Char(string='Course Name')
    price = fields.Float(string='Price')
    training_entity = fields.Char(string='Training Entity')
    # ─ Clearance Process ─
    is_clearance = fields.Boolean(string='Is Clearance Request', default=False)
    procedure_types = fields.Selection([
        ('resignation', 'Resignation'),
        ('no_renewal', 'Non-Renewal of Contract'),
        ('probation_fail', 'Failure to Pass Probation Period'),
        ('mutual_termination', 'Mutual Termination of Contract'),
        ('termination_77', 'Contract Termination - Article 77'),
        ('termination_80', 'Contract Termination - Article 80'),
        ('termination_87', 'Contract Termination - Article 87'),
        ('retirement', 'Retirement'),
        ('other', 'Other'),
    ], string='Procedure Type')
    joining_date = fields.Date(string='First Working Day')
    last_working_day = fields.Date(string='Last Working Day')
    employee_department = fields.Char(string='Employee Department')
    employee_manager_id = fields.Many2one('res.users', string='Department Manager')
    procedure_status = fields.Selection([
        ('interview', 'Personal Interview Conducted with Employee'),
        ('clearance_prepared', 'Financial Clearance Prepared for Termination of Services'),
        ('medical_insurance_removed', 'Employee Removed from Medical Insurance'),
        ('qiwa_removed', 'Employee Removed from Qiwa'),
        ('experience_cert_issued', 'Experience Certificate Issued'),
    ], string='Procedure Status')
    procedure_status_ids = fields.Many2many('hr.clearance.procedure.status', string='Procedure Status', tracking=True)
    final_interview = fields.Char(string='Final Interview')

    # Department Permissions (Computed)
    is_system = fields.Boolean(compute='_compute_department_permissions', store=False)
    is_hr_manager = fields.Boolean(compute='_compute_department_permissions', store=False)
    is_emp_manager_logged = fields.Boolean(compute='_compute_department_permissions', store=False)
    is_hr_user_logged = fields.Boolean(compute='_compute_department_permissions', store=False)
    is_finance_user_logged = fields.Boolean(compute='_compute_department_permissions', store=False)
    is_it_user_logged = fields.Boolean(compute='_compute_department_permissions', store=False)
    is_legal_user_logged = fields.Boolean(compute='_compute_department_permissions', store=False)

    is_dept_commercial_manager_logged = fields.Boolean(compute='_compute_department_permissions', store=False)
    is_dept_projects_manager_logged = fields.Boolean(compute='_compute_department_permissions', store=False)
    is_dept_marketing_manager_logged = fields.Boolean(compute='_compute_department_permissions', store=False)
    is_dept_legal_manager_logged = fields.Boolean(compute='_compute_department_permissions', store=False)
    is_dept_finance_manager_logged = fields.Boolean(compute='_compute_department_permissions', store=False)
    is_dept_hr_manager_logged = fields.Boolean(compute='_compute_department_permissions', store=False)
    is_dept_assets_manager_logged = fields.Boolean(compute='_compute_department_permissions', store=False)
    is_dept_it_manager_logged = fields.Boolean(compute='_compute_department_permissions', store=False)
    is_dept_executive_manager_logged = fields.Boolean(compute='_compute_department_permissions', store=False)
    is_current_dept_manager_logged = fields.Boolean(compute='_compute_current_dept_manager_logged', store=False)
    # Department 1: Employee Management
    emp_dept_notes = fields.Text(string='Employee Management Notes')
    emp_dept_custody_status = fields.Selection([
        ('in_progress', 'In Progress'),
        ('received', 'Received'),
        ('not_received', 'Not Received'),
    ], string='Employee Mgmt Custody Status', default='in_progress')

    # Department 2: HR Department
    hr_user_id = fields.Many2one('res.users', string='HR Manager / User', default=_default_hr_user_id)
    hr_notes = fields.Text(string='HR Notes')
    hr_custody_status = fields.Selection([
        ('in_progress', 'In Progress'),
        ('received', 'Received'),
        ('not_received', 'Not Received'),
        ('no_custody', 'No Custody'),
    ], string='HR Custody Status', default='in_progress')

    # Department 3: Financial Department
    finance_user_id = fields.Many2one('res.users', string='Financial Manager / User', default=_default_finance_user_id)
    finance_notes = fields.Text(string='Financial Notes')
    finance_custody_status = fields.Selection([
        ('in_progress', 'In Progress'),
        ('received', 'Received'),
        ('not_received', 'Not Received'),
        ('no_custody', 'No Custody'),
    ], string='Financial Custody Status', default='in_progress')

    # Department 4: IT Department
    it_user_id = fields.Many2one('res.users', string='IT Manager / User', default=_default_it_user_id)
    it_notes = fields.Char(string='IT Notes')
    it_custody_status = fields.Selection([
        ('in_progress', 'In Progress'),
        ('received', 'Received'),
        ('not_received', 'Not Received'),
        ('no_custody', 'No Custody'),
    ], string='IT Custody Status', default='in_progress')

    # Department 5: Legal Department
    legal_user_id = fields.Many2one('res.users', string='Legal Manager / User', default=_default_legal_user_id)
    legal_notes = fields.Char(string='Legal Notes')
    legal_custody_status = fields.Selection([
        ('in_progress', 'In Progress'),
        ('received', 'Received'),
        ('not_received', 'Not Received'),
        ('no_custody', 'No Custody'),
    ], string='Legal Custody Status', default='in_progress')

    def _sync_employee_details(self):
        """Disable parent request module automatic employee details syncing."""
        pass

    @api.model
    def web_search_read(self, domain=None, specification=None, offset=0, limit=None, order=None, count_limit=None):
        user = self.env.user
        is_hr_manager = user.has_group('hr_requests.group_hr_request_manager')
        if not is_hr_manager:
            uid = user.id
            # 1. Conditions for standard HR requests (is_clearance = False)
            hr_user_conditions = [
                [('user_id', '=', uid)],
                [('create_uid', '=', uid)],
            ]
            for dept_code, mgr_field in DEPT_MANAGER_FIELD_MAP.items():
                hr_user_conditions.append([
                    (mgr_field, '=', uid),
                    ('dept_approval_ids.department', '=', dept_code),
                ])

            hr_domain = expression.AND([
                [('is_clearance', '=', False)],
                expression.OR(hr_user_conditions),
            ])

            # 2. Conditions for Clearance requests (is_clearance = True)
            clearance_user_conditions = [
                [('user_id', '=', uid)],
                [('create_uid', '=', uid)],
                [('employee_manager_id', '=', uid)],
                [('hr_user_id', '=', uid)],
                [('finance_user_id', '=', uid)],
                [('it_user_id', '=', uid)],
                [('legal_user_id', '=', uid)],
            ]
            clearance_domain = expression.AND([
                [('is_clearance', '=', True)],
                expression.OR(clearance_user_conditions),
            ])

            user_visibility_domain = expression.OR([hr_domain, clearance_domain])
            domain = expression.AND([domain or [], user_visibility_domain])

        return super().web_search_read(
            domain=domain,
            specification=specification,
            offset=offset,
            limit=limit,
            order=order,
            count_limit=count_limit
        )

    @api.depends('returned_from_dept', 'dept_approval_ids', 'dept_approval_ids.notes')
    def _compute_returned_from_dept_notes(self):
        for rec in self:
            note = False
            if rec.returned_from_dept:
                line = rec.dept_approval_ids.filtered(lambda l: l.department == rec.returned_from_dept)[:1]
                if line and line.notes:
                    note = line.notes
                else:
                    field_pair = DEPT_APPROVAL_FIELD_MAP.get(rec.returned_from_dept)
                    if field_pair:
                        note = getattr(rec, field_pair[1], False)
            rec.returned_from_dept_notes = note

    @api.depends('dept_approval_ids', 'dept_approval_ids.department')
    def _compute_show_dept_tabs(self):
        for rec in self:
            depts = set(rec.dept_approval_ids.mapped('department'))
            rec.show_dept_commercial = 'hr_dept_commercial' in depts
            rec.show_dept_projects   = 'hr_dept_projects' in depts
            rec.show_dept_marketing  = 'hr_dept_marketing' in depts
            rec.show_dept_legal      = 'hr_dept_legal' in depts
            rec.show_dept_finance    = 'hr_dept_finance' in depts
            rec.show_dept_hr         = 'hr_dept_hr' in depts
            rec.show_dept_assets     = 'hr_dept_assets' in depts
            rec.show_dept_it         = 'hr_dept_it' in depts
            rec.show_dept_executive  = 'hr_dept_executive' in depts

    def _get_current_dept_manager(self):
        self.ensure_one()
        mgr_field = DEPT_MANAGER_FIELD_MAP.get(self.hr_stage_selection)
        return getattr(self, mgr_field, False) if mgr_field else False

    def _get_current_dept_name(self):
        self.ensure_one()
        return DEPT_NAME_MAP.get(self.hr_stage_selection, self.stage_id.name or 'Department')


    is_last_dept_approval = fields.Boolean(
        string='Is Last Department Approval',
        compute='_compute_is_last_dept_approval',
    )

    @api.depends('stage_id', 'dept_approval_ids', 'dept_approval_ids.state', 'dept_approval_ids.sequence', 'dept_approval_ids.is_fixed')
    def _compute_is_last_dept_approval(self):
        for rec in self:
            if rec.hr_stage_selection not in DEPT_STAGE_SELECTIONS:
                rec.is_last_dept_approval = False
                continue
            dept_lines = rec.dept_approval_ids.filtered(lambda l: not l.is_fixed).sorted('sequence')
            current_line = dept_lines.filtered(lambda l: l.department == rec.hr_stage_selection)[:1]
            if not current_line:
                rec.is_last_dept_approval = False
                continue
            current_idx = list(dept_lines).index(current_line)
            remaining = dept_lines[current_idx + 1:].filtered(lambda l: l.state == 'pending')
            rec.is_last_dept_approval = not bool(remaining)

    @api.depends('dept_approval_ids', 'dept_approval_ids.is_fixed')
    def _compute_has_dept_approvals(self):
        for rec in self:
            rec.has_dept_approvals = bool(rec.dept_approval_ids.filtered(lambda l: not l.is_fixed))

    @api.depends('dept_approval_ids', 'dept_approval_ids.department', 'dept_approval_ids.is_fixed')
    def _compute_allowed_dept_line_ids(self):
        fixed_lines = self.env['hr.request.dept.line'].search([('is_fixed', '=', True)])
        for rec in self:
            rec.allowed_dept_line_ids = fixed_lines | rec.dept_approval_ids.filtered(lambda l: not l.is_fixed)

    def _get_dept_line_for_stage(self, stage):
        """Find the corresponding hr.request.dept.line for a given request.stage."""
        self.ensure_one()
        if not stage or self.is_clearance:
            return self.env['hr.request.dept.line']

        sel = stage.hr_stage_selection
        fixed_map = {
            'hr_draft': 'draft',
            'hr_submitted': 'submitted',
            'hr_approval': 'hr_approval',
            'hr_approved': 'approved',
            'hr_rejected': 'rejected',
        }
        fixed_stage = fixed_map.get(sel)

        if not fixed_stage:
            if stage.state == 'draft':
                fixed_stage = 'draft'
            elif stage.state == 'done':
                fixed_stage = 'approved'
            elif stage.state == 'cancel':
                fixed_stage = 'rejected'

        if fixed_stage:
            fixed_line = self.env.ref(f'hr_requests.dept_line_{fixed_stage}', raise_if_not_found=False)
            if not fixed_line:
                fixed_line = self.env['hr.request.dept.line'].search([
                    ('is_fixed', '=', True),
                    ('fixed_stage', '=', fixed_stage),
                ], limit=1)
            return fixed_line

        # Dynamic department stage
        if sel:
            matching_lines = self.dept_approval_ids.filtered(
                lambda l: not l.is_fixed and l.department == sel
            )
            if matching_lines:
                return matching_lines[0]

        return self.env['hr.request.dept.line']

    def _get_stage_for_dept_line(self, dept_line):
        """Find the corresponding request.stage for a given hr.request.dept.line."""
        self.ensure_one()
        if not dept_line or self.is_clearance:
            return self.env['request.stage']

        if dept_line.is_fixed and dept_line.fixed_stage:
            xml_id_map = {
                'draft': 'hr_requests.stage_hr_draft',
                'submitted': 'hr_requests.stage_hr_submitted',
                'approved': 'hr_requests.stage_hr_approved',
                'rejected': 'hr_requests.stage_hr_rejected',
            }
            xml_id = xml_id_map.get(dept_line.fixed_stage)
            if xml_id:
                stage = self.env.ref(xml_id, raise_if_not_found=False)
                if stage:
                    return stage
        elif dept_line.department:
            return self._get_dept_stage_by_selection(dept_line.department)

        return self.env['request.stage']

    @api.depends('stage_id', 'is_clearance', 'dept_approval_ids', 'dept_approval_ids.department', 'dept_approval_ids.is_fixed')
    def _compute_dept_line_id(self):
        for rec in self:
            if rec.is_clearance:
                rec.dept_line_id = False
            else:
                rec.dept_line_id = rec._get_dept_line_for_stage(rec.stage_id)

    def _inverse_dept_line_id(self):
        for rec in self:
            if rec.is_clearance:
                continue
            if rec.dept_line_id:
                stage = rec._get_stage_for_dept_line(rec.dept_line_id)
                if stage and rec.stage_id != stage:
                    rec.stage_id = stage

    @api.onchange('stage_id')
    def _onchange_stage_id_sync_dept_line(self):
        if self.is_clearance:
            self.dept_line_id = False
            return
        if self.stage_id:
            line = self._get_dept_line_for_stage(self.stage_id)
            if line and self.dept_line_id != line:
                self.dept_line_id = line

    @api.onchange('dept_line_id')
    def _onchange_dept_line_id_sync_stage(self):
        if self.is_clearance:
            return
        if self.dept_line_id:
            stage = self._get_stage_for_dept_line(self.dept_line_id)
            if stage and self.stage_id != stage:
                self.stage_id = stage

    def _get_extra_domain(self):
        """
        Extend the parent domain so that when a single record is being
        evaluated, only the stages relevant TO THAT RECORD are considered
        for next/previous stage navigation.
        """
        search_domain = super(HrRequest, self)._get_extra_domain()

        if len(self) == 1 and not self.is_clearance:
            dept_sels = self.dept_approval_ids.sorted('sequence').mapped('department')
            allowed_selections = ['hr_draft', 'hr_submitted'] + [d for d in dept_sels if d] + ['hr_approved', 'hr_rejected']

            search_domain = expression.AND([
                search_domain,
                [
                    '|',
                    ('hr_stage_selection', '=', False),
                    ('hr_stage_selection', 'in', allowed_selections),
                ]
            ])

        return search_domain

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields=allfields, attributes=attributes)
        if res and 'active' in res:
            res['active']['readonly'] = True
            res['active']['invisible'] = True
        return res

    @api.depends('name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name

    # ─────────────────────────────────────────────
    # Computes & Onchanges
    # ─────────────────────────────────────────────
    @api.depends_context('uid')
    def _compute_department_permissions(self):
        current_user = self.env.user
        is_hr_mgr = current_user.has_group('hr_requests.group_hr_request_manager')
        is_sys = current_user.has_group('base.group_system') or self.env.is_admin()
        for rec in self:
            rec.is_system = is_sys
            rec.is_hr_manager = is_hr_mgr
            rec.is_emp_manager_logged = (rec.employee_manager_id and rec.employee_manager_id == current_user)
            rec.is_hr_user_logged = (rec.hr_user_id and rec.hr_user_id == current_user)
            rec.is_finance_user_logged = (rec.finance_user_id and rec.finance_user_id == current_user)
            rec.is_it_user_logged = (rec.it_user_id and rec.it_user_id == current_user)
            rec.is_legal_user_logged = (rec.legal_user_id and rec.legal_user_id == current_user)
            rec.is_dept_commercial_manager_logged = bool(rec.dept_commercial_manager_id and rec.dept_commercial_manager_id == current_user)
            rec.is_dept_projects_manager_logged = bool(rec.dept_projects_manager_id and rec.dept_projects_manager_id == current_user)
            rec.is_dept_marketing_manager_logged = bool(rec.dept_marketing_manager_id and rec.dept_marketing_manager_id == current_user)
            rec.is_dept_legal_manager_logged = bool(rec.dept_legal_manager_id and rec.dept_legal_manager_id == current_user)
            rec.is_dept_finance_manager_logged = bool(rec.dept_finance_manager_id and rec.dept_finance_manager_id == current_user)
            rec.is_dept_hr_manager_logged = bool(rec.dept_hr_manager_id and rec.dept_hr_manager_id == current_user)
            rec.is_dept_assets_manager_logged = bool(rec.dept_assets_manager_id and rec.dept_assets_manager_id == current_user)
            rec.is_dept_it_manager_logged = bool(rec.dept_it_manager_id and rec.dept_it_manager_id == current_user)
            rec.is_dept_executive_manager_logged = bool(rec.dept_executive_manager_id and rec.dept_executive_manager_id == current_user)

    @api.depends_context('uid')
    @api.depends(
        'stage_id', 'hr_stage_selection',
        'dept_commercial_manager_id', 'dept_projects_manager_id', 'dept_marketing_manager_id',
        'dept_legal_manager_id', 'dept_finance_manager_id', 'dept_hr_manager_id',
        'dept_assets_manager_id', 'dept_it_manager_id', 'dept_executive_manager_id'
    )
    def _compute_current_dept_manager_logged(self):
        current_user = self.env.user
        for rec in self:
            current_sel = rec.hr_stage_selection
            mgr_field = DEPT_MANAGER_FIELD_MAP.get(current_sel)
            if mgr_field:
                rec.is_current_dept_manager_logged = bool(getattr(rec, mgr_field) == current_user)
            else:
                rec.is_current_dept_manager_logged = False

    @api.depends_context('uid')
    def _compute_is_manager(self):
        default_class = self._default_employee_classification()
        for rec in self:
            rec.is_manager = (default_class == 'manager')

    @api.onchange('employee_classification')
    def _onchange_employee_classification(self):
        if self.category_id:
            allowed_classifications = ['employee', 'manager'] if self.employee_classification == 'manager' else ['employee']
            if self.category_id.employee_classification not in allowed_classifications:
                self.category_id = False
                self.type_id = False

    @api.onchange('category_id')
    def _onchange_category_id(self):
        if self.type_id and self.type_id.category_id != self.category_id:
            self.type_id = False

    def init(self):
        super().init()
        self.env.cr.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'hr_clearance_procedure_status_hr_request_rel'
                ) AND EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'hr_request' AND column_name = 'procedure_status'
                ) THEN
                    INSERT INTO hr_clearance_procedure_status_hr_request_rel (hr_request_id, hr_clearance_procedure_status_id)
                    SELECT req.id, imd.res_id
                    FROM hr_request req
                    JOIN ir_model_data imd ON imd.model = 'hr.clearance.procedure.status'
                                          AND imd.module = 'hr_requests'
                                          AND imd.name = 'procedure_status_' || req.procedure_status
                    WHERE req.procedure_status IS NOT NULL
                    ON CONFLICT DO NOTHING;
                END IF;
            END $$;
        """)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            is_clearance = vals.get('is_clearance')
            if is_clearance is None and self.env.context.get('default_is_clearance'):
                is_clearance = True

            if is_clearance:
                if not self.env.user.has_group('hr_requests.group_hr_request_manager') and not self.env.is_superuser():
                    raise UserError(_("Only HR Request Managers are allowed to create Clearance Requests."))

            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.request') or _('New')
            if is_clearance:
                if not vals.get('hr_user_id'):
                    vals['hr_user_id'] = self._default_hr_user_id()
                if not vals.get('finance_user_id'):
                    vals['finance_user_id'] = self._default_finance_user_id()
                if not vals.get('it_user_id'):
                    vals['it_user_id'] = self._default_it_user_id()
                if not vals.get('legal_user_id'):
                    vals['legal_user_id'] = self._default_legal_user_id()
            else:
                if not vals.get('dept_commercial_manager_id'):
                    vals['dept_commercial_manager_id'] = self._default_commercial_manager_id()
                if not vals.get('dept_projects_manager_id'):
                    vals['dept_projects_manager_id'] = self._default_projects_manager_id()
                if not vals.get('dept_marketing_manager_id'):
                    vals['dept_marketing_manager_id'] = self._default_marketing_manager_id()
                if not vals.get('dept_legal_manager_id'):
                    vals['dept_legal_manager_id'] = self._default_legal_user_id()
                if not vals.get('dept_finance_manager_id'):
                    vals['dept_finance_manager_id'] = self._default_finance_user_id()
                if not vals.get('dept_hr_manager_id'):
                    vals['dept_hr_manager_id'] = self._default_hr_user_id()
                if not vals.get('dept_assets_manager_id'):
                    vals['dept_assets_manager_id'] = self._default_assets_manager_id()
                if not vals.get('dept_it_manager_id'):
                    vals['dept_it_manager_id'] = self._default_it_user_id()
                if not vals.get('dept_executive_manager_id'):
                    vals['dept_executive_manager_id'] = self._default_executive_manager_id()
            if is_clearance and not vals.get('stage_id'):
                clearance_draft = self.env.ref('hr_requests.stage_clearance_draft', raise_if_not_found=False)
                if clearance_draft:
                    vals['stage_id'] = clearance_draft.id
            elif not is_clearance and not vals.get('stage_id'):
                draft_stage = self.env.ref('hr_requests.stage_hr_draft', raise_if_not_found=False)
                if draft_stage:
                    vals['stage_id'] = draft_stage.id

        records = super(HrRequest, self).create(vals_list)
        for rec in records:
            rec._update_attachment_names()
            rec._notify_stage_authorized_users()
        return records

    def write(self, vals):
        stage_changed = 'stage_id' in vals
        old_stages = {rec.id: rec.hr_stage_selection for rec in self} if stage_changed else {}
        res = super(HrRequest, self).write(vals)
        self._update_attachment_names()
        if stage_changed:
            self._notify_stage_authorized_users(old_stages=old_stages)
        return res

    def _update_attachment_names(self):
        """Prepend request number to attachment names for attachment_ids."""
        for rec in self:
            if not rec.name or rec.name == _('New'):
                continue
            for att in rec.attachment_ids:
                if att.name and rec.name not in att.name:
                    att.sudo().write({'name': f"{rec.name} - {att.name}"})

    def _get_mail_thread_data_attachments(self):
        """Exclude attachments belonging to explicit model fields from the Chatter."""
        res = super()._get_mail_thread_data_attachments()
        if self:
            self.ensure_one()
            field_attachment_ids = set()
            if hasattr(self, 'attachment_ids') and self.attachment_ids:
                field_attachment_ids.update(self.attachment_ids.ids)
            if field_attachment_ids:
                res = res.filtered(lambda a: a.id not in field_attachment_ids)
        return res

    def get_hr_request_url(self):
        """Return URL to open this HR request specifically in view_hr_request_form."""
        self.ensure_one()
        base_url = self.get_base_url()
        action = self.env.ref('hr_requests.action_hr_request', raise_if_not_found=False)
        view = self.env.ref('hr_requests.view_hr_request_form', raise_if_not_found=False)
        action_param = f"&action={action.id}" if action else ""
        view_param = f"&view_id={view.id}" if view else ""
        return f"{base_url}/web#id={self.id}{action_param}&model={self._name}&view_type=form{view_param}"

    def get_formview_url(self):
        """Return the appropriate form view URL based on request type."""
        self.ensure_one()
        if self.is_clearance:
            base_url = self.get_base_url()
            action = self.env.ref('hr_requests.action_hr_clearance_request', raise_if_not_found=False)
            view = self.env.ref('hr_requests.view_hr_clearance_request_form', raise_if_not_found=False)
            action_param = f"&action={action.id}" if action else ""
            view_param = f"&view_id={view.id}" if view else ""
            return f"{base_url}/web#id={self.id}{action_param}&model={self._name}&view_type=form{view_param}"
        return self.get_hr_request_url()

    def get_formview_id(self, access_uid=None):
        """Ensure non-clearance requests always default to view_hr_request_form."""
        if self.is_clearance:
            clearance_form = self.env.ref('hr_requests.view_hr_clearance_request_form', raise_if_not_found=False)
            if clearance_form:
                return clearance_form.id
        request_form = self.env.ref('hr_requests.view_hr_request_form', raise_if_not_found=False)
        if request_form:
            return request_form.id
        return super().get_formview_id(access_uid=access_uid)

    def get_formview_action(self, access_uid=None):
        """Ensure get_formview_action uses the correct action and form view."""
        res = super().get_formview_action(access_uid=access_uid)
        view_id = self.get_formview_id(access_uid=access_uid)
        if view_id:
            res['views'] = [(view_id, 'form')]
        return res

    # ─────────────────────────────────────────────
    # Stage transition helpers & actions
    # ─────────────────────────────────────────────
    def _move_to_stage(self, xml_id):
        """Helper to move all records in self to a given stage by xml_id."""
        stage = self.env.ref(xml_id, raise_if_not_found=False)
        if not stage:
            raise UserError(_("The requested stage was not found."))
        send_email = self.env.context.get('send_stage_email', True)
        for rec in self:
            rec.with_context(send_stage_email=send_email).write({'stage_id': stage.id})

    def _get_stage_target_users(self, stage_selection):
        """Get target users to notify for a given stage selection."""
        self.ensure_one()
        users = self.env['res.users']

        # If entering a department stage, notify that department's manager
        mgr_field = DEPT_MANAGER_FIELD_MAP.get(stage_selection)
        if mgr_field:
            mgr = getattr(self, mgr_field, False)
            if mgr and mgr.active:
                users |= mgr

        # If entering HR Approval stage, notify HR Request Managers
        if stage_selection == 'hr_approval':
            hr_group = self.env.ref('hr_requests.group_hr_request_manager', raise_if_not_found=False)
            if hr_group:
                users |= hr_group.users.filtered(lambda u: u.active)

        return users

    def _notify_stage_authorized_users(self, old_stages=None):
        """
        Send email notifications when moving to hr_submitted, hr_approved, hr_rejected,
        or department stages (via action buttons only), and manage review activities.
        """
        send_email = self.env.context.get('send_stage_email', False)

        for rec in self:
            stage_sel = rec.hr_stage_selection
            if not stage_sel:
                continue
            # Clear old activities
            old_activities = rec.env['mail.activity'].sudo().search([
                ('res_model', '=', rec._name),
                ('res_id', '=', rec.id),
            ])
            if old_activities:
                if stage_sel in ('hr_approved', 'hr_rejected', 'hr_draft', 'clearance_archive', 'clearance_draft'):
                    old_activities.unlink()
                else:
                    old_activities.action_done()

            if stage_sel == 'hr_draft':
                continue

            if send_email:
                # Stage: Submitted (from Draft) for request_type_hr -> Send email to HR Request Managers
                if stage_sel == 'hr_submitted' and not rec.is_clearance:
                    req_type_hr = rec.env.ref('hr_requests.request_type_hr', raise_if_not_found=False)
                    is_hr_type = not rec.request_type_id or (req_type_hr and rec.request_type_id == req_type_hr)
                    prev_stage = (old_stages or {}).get(rec.id)
                    from_draft = prev_stage in (False, 'hr_draft') and not rec.returned_from_stage_id
                    if is_hr_type and from_draft:
                        hr_group = rec.env.ref('hr_requests.group_hr_request_manager', raise_if_not_found=False)
                        if hr_group:
                            managers = hr_group.users.filtered(lambda u: u.active and u.email)
                            template = rec.env.ref('hr_requests.email_template_hr_request_submitted', raise_if_not_found=False)
                            if template and managers:
                                for mgr in managers:
                                    try:
                                        template.with_context(manager_name=mgr.name).send_mail(
                                            rec.id,
                                            email_values={'email_to': mgr.email.strip()},
                                            force_send=True
                                        )
                                    except Exception as e:
                                        _logger.error(
                                            "[HR Request Submitted Email] Failed to send email for request %s to %s: %s",
                                            rec.name, mgr.name, str(e)
                                        )

                # Stage: HR Approval (Dept Approvals Completed) -> Send email to HR Request Managers
                if stage_sel == 'hr_approval' and not rec.is_clearance:
                    req_type_hr = rec.env.ref('hr_requests.request_type_hr', raise_if_not_found=False)
                    is_hr_type = not rec.request_type_id or (req_type_hr and rec.request_type_id == req_type_hr)
                    if is_hr_type:
                        hr_group = rec.env.ref('hr_requests.group_hr_request_manager', raise_if_not_found=False)
                        if hr_group:
                            managers = hr_group.users.filtered(lambda u: u.active and u.email)
                            template = rec.env.ref('hr_requests.email_template_hr_approval_required', raise_if_not_found=False)
                            if template and managers:
                                for mgr in managers:
                                    try:
                                        template.with_context(manager_name=mgr.name).send_mail(
                                            rec.id,
                                            email_values={'email_to': mgr.email.strip()},
                                            force_send=True
                                        )
                                    except Exception as e:
                                        _logger.error(
                                            "[HR Request HR Approval Email] Failed to send email for request %s to %s: %s",
                                            rec.name, mgr.name, str(e)
                                        )

                if stage_sel in ('hr_approved', 'hr_rejected'):
                    template_xml_id = (
                        'hr_requests.email_template_hr_request_approved'
                        if stage_sel == 'hr_approved'
                        else 'hr_requests.email_template_hr_request_rejected'
                    )
                    template = rec.env.ref(template_xml_id, raise_if_not_found=False)
                    if template and rec.user_id and rec.user_id.email:
                        try:
                            template.send_mail(
                                rec.id,
                                email_values={'email_to': rec.user_id.email.strip()},
                                force_send=True
                            )
                        except Exception as e:
                            _logger.error(
                                "[HR Request Email] Failed to send email for request %s: %s",
                                rec.name, str(e)
                            )

                if stage_sel in DEPT_STAGE_SELECTIONS and not rec.is_clearance:
                    mgr = rec._get_current_dept_manager()
                    if mgr and mgr.email:
                        dept_name = rec._get_current_dept_name()
                        notified_list = [d.strip() for d in (rec.notified_dept_history or '').split(',') if d.strip()]
                        is_reassigned = self.env.context.get('is_resend_to_dept') or (stage_sel in notified_list)
                        template_xml_id = (
                            'hr_requests.email_template_hr_dept_approval_reassigned'
                            if is_reassigned
                            else 'hr_requests.email_template_hr_dept_approval_required'
                        )
                        template = rec.env.ref(template_xml_id, raise_if_not_found=False)
                        if template:
                            try:
                                ctx = {
                                    'dept_name': dept_name,
                                    'dept_manager_name': mgr.name,
                                    'dept_manager_email': mgr.email.strip(),
                                }
                                template.with_context(**ctx).send_mail(
                                    rec.id,
                                    email_values={'email_to': mgr.email.strip()},
                                    force_send=True
                                )
                            except Exception as e:
                                _logger.error(
                                    "[HR Request Dept Email] Failed to send email for request %s to %s (%s): %s",
                                    rec.name, mgr.name, dept_name, str(e)
                                )
                        if not is_reassigned:
                            notified_list.append(stage_sel)
                            rec.sudo().with_context(tracking_disable=True).write({
                                'notified_dept_history': ','.join(notified_list)
                            })

            target_users = rec._get_stage_target_users(stage_sel)
            if not target_users:
                continue

            activity_type = rec.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            model_id = rec.env['ir.model']._get(rec._name).id
            stage_name = rec.stage_id.name or 'Review'

            for user in target_users:
                rec.env['mail.activity'].sudo().with_context(
                    mail_activity_quick_update=True,
                    mail_create_nosubscribe=True,
                ).create({
                    'summary': f'HR Request Pending Review: {stage_name}',
                    'note': (
                        f'HR Request No. <b>{rec.name}</b> '
                        f'(Type: {rec.type_id.name or "-"}) '
                        f'is awaiting your review at stage <b>{stage_name}</b>.'
                    ),
                    'activity_type_id': activity_type.id if activity_type else False,
                    'res_model': rec._name,
                    'res_model_id': model_id,
                    'res_id': rec.id,
                    'user_id': user.id,
                    'date_deadline': fields.Date.today(),
                })

    def _check_missing_fields(self):
        """Helper method to check mandatory fields before moving to submitted stage"""
        for rec in self:
            if rec.request_type_code == 'recruitment_request':
                fields_to_check = [
                    'office_department_id',
                    'recruitment_structure',
                    'recruitment_type',
                    'branch',
                    'required_experience',
                    'required_tasks',
                    'reason_for_need',
                ]
                missing = [f for f in fields_to_check if not getattr(rec, f) or getattr(rec, f) == '']
                if missing:
                    labels = [rec.fields_get([f])[f]['string'] for f in missing]
                    raise UserError(
                        _("Please fill in the following fields before submitting the request:\n• %s")
                        % ("\n• ".join(labels))
                    )

    def action_submit(self):
        """Draft -> Submitted."""
        self._check_missing_fields()
        self._move_to_stage('hr_requests.stage_hr_submitted')

    def action_send_to_departments(self):
        """Submitted -> first dept stage (or HR Approval if no depts)."""
        self._check_missing_fields()
        for rec in self:
            if rec.returned_from_stage_id:
                raise UserError(_("This request was returned from a department. Please use 'Re-send to Department'."))
            dept_lines = rec.dept_approval_ids.filtered(lambda l: not l.is_fixed).sorted('sequence')
            if dept_lines:
                first_dept = dept_lines[0]
                rec._move_to_dept_stage(first_dept)
            else:
                rec._move_to_stage('hr_requests.stage_hr_approval')

    def action_approve(self):
        """HR Approval -> Approved."""
        self._check_missing_fields()
        self._move_to_stage('hr_requests.stage_hr_approved')

    def action_resend_to_dept(self):
        """
        Re-send a request returned from department rejection back to that department stage.
        Groups: hr_requests.group_hr_request_manager
        """
        self.ensure_one()
        self._check_missing_fields()
        if not self.returned_from_stage_id:
            raise UserError(_("This request was not returned from a department rejection."))

        target_stage = self.returned_from_stage_id
        target_dept = self.returned_from_dept

        # Reset the rejecting department line to pending
        if target_dept:
            dept_lines = self.dept_approval_ids.filtered(lambda l: l.department == target_dept)
            dept_lines.write({
                'state': 'pending',
                'approved_by': False,
                'approval_date': False,
            })

        if self.resend_notes:
            self.message_post(body=_("Request re-sent to department with note: %s") % self.resend_notes)

        self.with_context(send_stage_email=True, is_resend_to_dept=True).write({
            'stage_id': target_stage.id,
            'returned_from_stage_id': False,
            'returned_from_dept': False,
        })

    def action_reject(self):
        """Submitted -> Rejected."""
        self.write({
            'returned_from_stage_id': False,
            'returned_from_dept': False,
            'resend_notes': False,
        })
        self._move_to_stage('hr_requests.stage_hr_rejected')

    def action_reset_to_draft(self):
        """Reset to Draft."""
        for rec in self:
            rec.dept_approval_ids.filtered(lambda l: not l.is_fixed).write({
                'state': 'pending',
                'approved_by': False,
                'approval_date': False,
            })
            reset_vals = {
                'returned_from_stage_id': False,
                'returned_from_dept': False,
                'resend_notes': False,
            }
            for appr_field, dummy_notes in DEPT_APPROVAL_FIELD_MAP.values():
                reset_vals[appr_field] = False
            rec.write(reset_vals)
            rec.with_context(send_stage_email=False)._move_to_stage('hr_requests.stage_hr_draft')

    # ─────────────────────────────────────────────
    # Dynamic Dept Approval actions
    # ─────────────────────────────────────────────
    def _get_dept_stage_by_selection(self, selection_value):
        """Return the request.stage record for a dept hr_stage_selection value."""
        return self.env['request.stage'].search([
            ('hr_stage_selection', '=', selection_value),
            ('res_model', '=', 'hr.request'),
        ], limit=1)

    def _move_to_dept_stage(self, dept_line):
        """Move record to the stage corresponding to a dept_line."""
        self.ensure_one()
        stage = self._get_dept_stage_by_selection(dept_line.department)
        if not stage:
            raise UserError(_(
                "Could not find the stage for department: %s"
            ) % dept_line.department_label)
        self.with_context(send_stage_email=True).write({'stage_id': stage.id})

    def action_dept_approve(self):
        """
        Approve the current department step and advance to the next one,
        or to 'Approved' if all dept steps are done.
        """
        self.ensure_one()
        self._check_missing_fields()
        if not self.env.user.has_group('hr_requests.group_hr_request_manager') and not self.is_current_dept_manager_logged:
            raise UserError(_("Only the assigned department manager can perform this action."))

        dept_lines = self.dept_approval_ids.filtered(lambda l: not l.is_fixed).sorted('sequence')
        if not dept_lines:
            raise UserError(_("No department approval steps are configured for this request."))

        current_sel = self.hr_stage_selection
        current_line = dept_lines.filtered(lambda l: l.department == current_sel)
        if not current_line:
            raise UserError(_("This action is only available at a department approval stage."))

        current_line = current_line[0]

        # Verify that the assigned manager has granted approval
        field_pair = DEPT_APPROVAL_FIELD_MAP.get(current_sel)
        if field_pair:
            appr_field, notes_field = field_pair
            appr_val = getattr(self, appr_field)
            if appr_val != 'approved':
                dept_name = current_line.department_label or DEPT_NAME_MAP.get(current_sel, current_sel)
                raise UserError(_(
                    "Cannot send the request to the next stage because approval from %(dept)s has not been granted. "
                    "The approval status must be set to 'Approved' by the assigned manager."
                ) % {'dept': dept_name})

            notes_val = getattr(self, notes_field)
            if notes_val:
                current_line.notes = notes_val

        mgr_field = DEPT_MANAGER_FIELD_MAP.get(current_sel)
        mgr_user = getattr(self, mgr_field) if mgr_field else None

        current_line.write({
            'state': 'approved',
            'approved_by': mgr_user.id if mgr_user else self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })
        self.write({
            'returned_from_stage_id': False,
            'returned_from_dept': False,
            'resend_notes': False,
        })

        # Find next pending dept line
        current_idx = list(dept_lines).index(current_line)
        remaining = dept_lines[current_idx + 1:]
        next_line = remaining.filtered(lambda l: l.state == 'pending')[:1]

        if next_line:
            self._move_to_dept_stage(next_line)
        else:
            # All dept approvals done -> move to HR Approval stage
            self._move_to_stage('hr_requests.stage_hr_approval')

    def action_dept_reject(self):
        """
        Reject at the current department step and return to 'Submitted' stage.
        """
        self.ensure_one()
        if not self.env.user.has_group('hr_requests.group_hr_request_manager') and not self.is_current_dept_manager_logged and not self.env.is_superuser():
            raise UserError(_("Only the assigned department manager or an HR Request Manager can perform this action."))

        dept_lines = self.dept_approval_ids.filtered(lambda l: not l.is_fixed).sorted('sequence')
        current_sel = self.hr_stage_selection
        current_line = dept_lines.filtered(lambda l: l.department == current_sel)
        if not current_line:
            raise UserError(_("This action is only available at a department approval stage."))

        current_line = current_line[0]

        # Verify that the assigned manager has rejected
        field_pair = DEPT_APPROVAL_FIELD_MAP.get(current_sel)
        if field_pair:
            appr_field, notes_field = field_pair
            appr_val = getattr(self, appr_field)
            if appr_val != 'rejected':
                dept_name = current_line.department_label or DEPT_NAME_MAP.get(current_sel, current_sel)
                raise UserError(_(
                    "Cannot return the request to HR because approval status from %(dept)s is not 'Rejected'. "
                    "The approval status must be set to 'Rejected' by the assigned manager."
                ) % {'dept': dept_name})

            notes_val = getattr(self, notes_field)
            if notes_val:
                current_line.notes = notes_val

        mgr_field = DEPT_MANAGER_FIELD_MAP.get(current_sel)
        mgr_user = getattr(self, mgr_field) if mgr_field else None

        current_line.write({
            'state': 'rejected',
            'approved_by': mgr_user.id if mgr_user else self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })
        self.write({
            'returned_from_stage_id': self.stage_id.id,
            'returned_from_dept': current_sel,
            'resend_notes': False,
        })

        dept_display_name = current_line.department_label or DEPT_NAME_MAP.get(current_sel, current_sel)
        rejected_by_display = mgr_user.name if mgr_user else self.env.user.name
        self._send_dept_rejected_email(
            dept_name=dept_display_name,
            rejected_by_name=rejected_by_display,
            rejection_notes=notes_val or current_line.notes or False,
        )

        # Move back to Submitted stage (rejection email already sent to HR)
        self.with_context(send_stage_email=False)._move_to_stage('hr_requests.stage_hr_submitted')

    def _send_dept_rejected_email(self, dept_name, rejected_by_name, rejection_notes=False):
        """Send email notification to HR Request Managers when a department rejects the request."""
        self.ensure_one()
        hr_group = self.env.ref('hr_requests.group_hr_request_manager', raise_if_not_found=False)
        if not hr_group:
            return
        managers = hr_group.users.filtered(lambda u: u.active and u.email)
        template = self.env.ref('hr_requests.email_template_hr_dept_rejected', raise_if_not_found=False)
        if not template or not managers:
            return

        for mgr in managers:
            try:
                ctx = {
                    'manager_name': mgr.name,
                    'dept_name': dept_name,
                    'rejected_by_name': rejected_by_name,
                    'rejection_notes': rejection_notes,
                }
                template.with_context(**ctx).send_mail(
                    self.id,
                    email_values={'email_to': mgr.email.strip()},
                    force_send=True
                )
            except Exception as e:
                _logger.error(
                    "[HR Request Dept Rejection Email] Failed to send email for request %s to %s: %s",
                    self.name, mgr.name, str(e)
                )

    # ─────────────────────────────────────────────
    # Clearance Stage Transition Actions
    # ─────────────────────────────────────────────
    def action_clearance_submit(self):
        """Draft -> Employee Management"""
        for rec in self:
            if rec.is_clearance:
                missing_fields = []
                if not rec.user_id:
                    missing_fields.append(_('Employee Name'))
                if not rec.joining_date:
                    missing_fields.append(_('First Working Day'))
                if not rec.employee_manager_id:
                    missing_fields.append(_('Department Manager'))
                if not rec.last_working_day:
                    missing_fields.append(_('Last Working Day'))

                if missing_fields:
                    raise UserError(
                        _("Please fill in the following fields before submitting the request:\n• %s")
                        % ("\n• ".join(missing_fields))
                    )

        self._move_to_stage('hr_requests.stage_clearance_emp_dept')
        for rec in self:
            if rec.is_clearance and rec.employee_manager_id and rec.employee_manager_id.email:
                template = rec.env.ref('hr_requests.email_template_clearance_emp_manager', raise_if_not_found=False)
                if template:
                    try:
                        template.send_mail(
                            rec.id,
                            email_values={'email_to': rec.employee_manager_id.email.strip()},
                            force_send=True
                        )
                    except Exception as e:
                        _logger.error(
                            "[Clearance Email] Failed to send email to employee manager for request %s: %s",
                            rec.name, str(e)
                        )

    def action_clearance_to_departments(self):
        """Employee Management -> Concerned Departments"""
        self._move_to_stage('hr_requests.stage_clearance_departments')
        for rec in self:
            if rec.is_clearance:
                dept_user_templates = [
                    (rec.hr_user_id, 'hr_requests.email_template_clearance_hr'),
                    (rec.finance_user_id, 'hr_requests.email_template_clearance_finance'),
                    (rec.it_user_id, 'hr_requests.email_template_clearance_it'),
                    (rec.legal_user_id, 'hr_requests.email_template_clearance_legal'),
                ]
                for user, template_xml_id in dept_user_templates:
                    if user and user.email:
                        template = rec.env.ref(template_xml_id, raise_if_not_found=False)
                        if template:
                            try:
                                template.send_mail(
                                    rec.id,
                                    email_values={'email_to': user.email.strip()},
                                    force_send=True
                                )
                            except Exception as e:
                                _logger.error(
                                    "[Clearance Email] Failed to send email for template %s on request %s: %s",
                                    template_xml_id, rec.name, str(e)
                                )

    def action_clearance_archive(self):
        """Concerned Departments -> Archive"""
        self._move_to_stage('hr_requests.stage_clearance_archive')

    def action_clearance_reset_to_draft(self):
        """Reset to Clearance Draft"""
        self._move_to_stage('hr_requests.stage_clearance_draft')
