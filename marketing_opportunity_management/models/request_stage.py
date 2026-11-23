from odoo import models, fields

class RequestStage(models.Model):
    _inherit = 'request.stage'

    opportunity_stage_selection = fields.Selection([
        ('opp_draft', 'Opportunity - Draft'),
        ('opp_data_completion', 'Opportunity - Data Completion'),
        ('opp_marketing_request', 'Opportunity - Marketing Request'),
        ('opp_final_material', 'Opportunity - Final Material'),
        ('opp_approve_close', 'Opportunity - Approve Close'),
        ('opp_contracted', 'Opportunity - Contracted'),
    ], string='Opportunity Stage Selection')

    marketing_stage_selection = fields.Selection([
        ('mkt_draft', 'Marketing - Reception'),
        ('mkt_review', 'Marketing - Review & Classify'),
        ('mkt_approval', 'Marketing - Supervisor Approval'),
        ('mkt_done', 'Marketing - Completed'),
    ], string='Marketing Stage Selection')

    department_id = fields.Many2one('bussma.marketing.department', string='Department')

    material_stage_selection = fields.Selection([
        ('mat_content_exec', 'Content Execution'),
        ('mat_content_approve', 'Content Supervisor Approval'),
        ('mat_design_exec', 'Design Execution'),
        ('mat_design_approve', 'Design Supervisor Approval'),
        ('mat_digital_exec', 'Campaigns & Publishing Setup'),
        ('mat_digital_approve', 'Digital Supervisor Approval'),
        ('mat_ops_exec', 'Printing & Production'),
        ('mat_ops_approve', 'Operations Supervisor Approval'),
        ('mat_marketing_approve', 'Marketing Supervisor Approval'),
        ('mat_pm_approve', 'Pending PM Approval'),
        ('mat_done', 'Completed')
    ], string='Material Stage Selection')

