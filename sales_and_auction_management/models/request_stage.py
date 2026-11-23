from odoo import models, fields, api, _

class RequestStage(models.Model):
    _inherit = 'request.stage'

    hide_on_flag = fields.Boolean(string="Hide on Request Flag", default=False)
    sales_auction_stage_selection = fields.Selection([
        # Auctions - Private
        ('p2_auction_pvt_portfolio', 'Property Portfolio (Private)'),
        # Auctions - Eanfaz
        ('p2_auction_enf_portfolio', 'Study Request (Eanfaz)'),
        ('p2_auction_enf_project_manager', 'Auction Manager Approval (Eanfaz)'),
        ('p2_auction_enf_sup', 'Study Supervisor (Eanfaz)'),
        ('p2_auction_enf_detailed', 'Detailed Study (Gov Auctions)'),
        ('p2_auction_enf_detailed_appr', 'Detailed Study Approval (Gov)'),
        ('p2_auction_enf_pm_appr', 'Project Manager Study Approval (Gov)'),
        # Auctions - Cities
        ('p2_auction_city_portfolio', 'Cities Portfolio'),
        # Sales
        ('p2_sales_direct_mgmt', 'Sales Property Portfolio'),
        ('p2_sales_archive', 'Sales Archive'),
        # ── Shared Stages ──────────────────────────────────────
        ('p2_shared_buyer_contracting', 'Contracting with Buyer (Shared)'),
        ('p2_shared_sales_fin', 'Sales with Finance (Shared)'),
        ('p2_shared_col_trans', 'Collection and Transfer (Shared)'),
        ('p2_shared_sector_manager_approval', 'Sector Manager Approval'),
        ('p2_shared_archive', 'Auctions Archive (Shared)'),
    ], string='Phase 2 Stage Selection')
    project_stage_selection = fields.Selection(selection_add=[
        ('studies_supervisor_eanfaz', 'Studies Supervisor - Eanfaz'),
        ('detailed_study_eanfaz', 'Detailed Study - Eanfaz'),
        ('detailed_study_approval_eanfaz', 'Detailed Study Approval - Eanfaz'),
        ('detailed_study_completed_eanfaz', 'Detailed Study - Eanfaz Completed'),
    ], ondelete={
        'studies_supervisor_eanfaz': 'set null',
        'detailed_study_eanfaz': 'set null',
        'detailed_study_approval_eanfaz': 'set null',
        'detailed_study_completed_eanfaz': 'set null',
    })
    bussma_project_stage_selection = fields.Selection([
        ('bussma_project_sales_pm', 'Project Management - Direct Sales'),
        ('bussma_project_pvt_pm', 'Project Management - Private'),
        ('bussma_project_city_pm', 'Project Management - Cities'),
        ('bussma_project_enf_pm', 'Project Management - Eanfaz'),
        ('bussma_project_sales_fin', 'Sales and Finance'),
        ('bussma_project_completed', 'Completed'),
    ], string='Bussma Project Stage Selection')
