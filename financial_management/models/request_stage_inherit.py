from odoo import models, fields


class RequestStageInherit(models.Model):
    _inherit = 'request.stage'

    financial_stage_selection = fields.Selection([
        ('fin_draft', 'Request Submission'),
        ('fin_marketing_mgr', 'Marketing Manager Approval'),
        ('fin_sector_accountant', 'Commercial Sector Accountant Approval'),
        ('fin_dept_mgr', 'Department Manager Approval'),
        ('fin_sector_mgr', 'Commercial Sector Manager Approval'),
        ('fin_admin_accountant', 'Administration Accountant Approval'),
        ('fin_financial_mgr', 'Financial Management Manager Approval'),
        ('fin_attach_receipts', 'Attach Receipts'),
        ('fin_archived', 'Archived'),
    ], string='Financial Stage Selection')
