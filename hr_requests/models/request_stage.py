# -*- coding: utf-8 -*-

from odoo import models, fields


class RequestStage(models.Model):
    _inherit = 'request.stage'

    hr_stage_selection = fields.Selection([
        # ── Fixed HR Request Stages ─────────────────────────────────────────
        ('hr_draft',       'Draft'),
        ('hr_submitted',   'Submitted'),
        ('hr_approval',    'HR Approval'),
        ('hr_approved',    'Approved'),
        ('hr_rejected',    'Rejected'),
        # ── Dynamic Department Approval Stages ──────────────────────────────
        ('hr_dept_commercial', 'Commercial Sector Management'),
        ('hr_dept_projects',   'Project Management'),
        ('hr_dept_marketing',  'Marketing Management'),
        ('hr_dept_legal',      'Legal Management'),
        ('hr_dept_finance',    'Financial Management'),
        ('hr_dept_hr',         'Human Resources Management'),
        ('hr_dept_assets',     'Assets & Investment Management'),
        ('hr_dept_it',         'IT Management'),
        ('hr_dept_executive',  'Executive Management'),
        # ── Clearance Stages ────────────────────────────────────────────────
        ('clearance_draft',       'Draft (Clearance)'),
        ('clearance_emp_dept',    'Employee Management'),
        ('clearance_departments', 'Concerned Departments'),
        ('clearance_archive',     'Archive'),
    ], string='HR Stage Selection')
