# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


DEPT_SELECTION = [
    ('hr_dept_commercial', 'Commercial Sector Management'),
    ('hr_dept_projects',   'Project Management'),
    ('hr_dept_marketing',  'Marketing Management'),
    ('hr_dept_legal',      'Legal Management'),
    ('hr_dept_finance',    'Financial Management'),
    ('hr_dept_hr',         'Human Resources Management'),
    ('hr_dept_assets',     'Assets & Investment Management'),
    ('hr_dept_it',         'IT Management'),
    ('hr_dept_executive',  'Executive Management'),
]


class HrRequestDeptLine(models.Model):
    _name = 'hr.request.dept.line'
    _description = 'HR Request Department Approval Line'
    _rec_name = 'department_label'
    _order = 'sequence asc, id asc'

    request_id = fields.Many2one(
        'hr.request',
        string='HR Request',
        required=False,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='Order', default=10)

    is_fixed = fields.Boolean(
        string='Is Fixed Stage',
        default=False,
        index=True,
    )
    fixed_stage = fields.Selection([
        ('draft',       'Draft'),
        ('submitted',   'Submitted'),
        ('hr_approval', 'HR Approval'),
        ('approved',    'Approved'),
        ('rejected',    'Rejected'),
    ], string='Fixed Stage', index=True)

    department = fields.Selection(
        selection=DEPT_SELECTION,
        string='Department',
        required=False,
    )
    department_label = fields.Char(
        string='Department Name',
        compute='_compute_department_label',
        store=False,
    )

    state = fields.Selection([
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='pending', required=True)

    approved_by = fields.Many2one('res.users', string='Decided By', readonly=True)
    approval_date = fields.Datetime(string='Decision Date', readonly=True)
    notes = fields.Char(string='Notes')

    @api.depends('department', 'is_fixed', 'fixed_stage')
    def _compute_department_label(self):
        dept_dict = dict(self._fields['department']._description_selection(self.env))
        fixed_dict = dict(self._fields['fixed_stage']._description_selection(self.env))
        for rec in self:
            if rec.is_fixed and rec.fixed_stage:
                rec.department_label = fixed_dict.get(rec.fixed_stage, rec.fixed_stage or '')
            elif rec.department:
                rec.department_label = dept_dict.get(rec.department, rec.department or '')
            else:
                rec.department_label = ''

    @api.depends('department', 'is_fixed', 'fixed_stage')
    def _compute_display_name(self):
        dept_dict = dict(self._fields['department']._description_selection(self.env))
        fixed_dict = dict(self._fields['fixed_stage']._description_selection(self.env))
        for rec in self:
            if rec.is_fixed and rec.fixed_stage:
                rec.display_name = fixed_dict.get(rec.fixed_stage, rec.fixed_stage or '')
            elif rec.department:
                rec.display_name = dept_dict.get(rec.department, rec.department or '')
            else:
                rec.display_name = f"Line #{rec.id}" if rec.id else "Stage Line"
