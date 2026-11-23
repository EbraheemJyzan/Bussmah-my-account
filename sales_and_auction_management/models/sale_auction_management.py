import logging
from lxml import etree
from odoo import models, fields, api, exceptions, _
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class SalesAuctionManagement(models.Model):
    _name = 'sales.auction.management'
    _inherit = 'request'
    _description = 'Sales and Auctions Management'
    _rec_name = 'entrie_name'
    
    active = fields.Boolean(default=True)
    entry_id = fields.Many2one('entries', string='Original Entry', readonly=True, ondelete='cascade')
    project_type_selection = fields.Selection([
        ('sales', 'Sales'),
        ('auction_pvt', 'Auctions - Private'),
        ('auction_enf', 'Auctions - Eanfaz'),
        ('city', 'City'),
    ], string='Project Type Selection', compute='_compute_project_type_selection', store=True)
    project_id = fields.Many2one(
        'bussma.project', 
        string='Project', 
        tracking=True,
        domain="[('project_type', '=', project_type_selection), ('is_basic', '=', False)]"
    )
    is_project_basic = fields.Boolean(
        string='Is Project Basic',
        compute='_compute_is_project_basic',
        store=True,
    )
    transfer_status_display = fields.Char(
        string='Transfer Status Note',
        copy=False
    )
    entrie_name = fields.Char(string='Entry Reference', copy=False, readonly=True, index=True, default=lambda self: _('New'))
    color = fields.Integer(string='Color', default=0)
    task_ids = fields.One2many('project.task', 'entry_id', string="Tasks")
    stage_id = fields.Many2one(
        "request.stage",
        string="Stage",
        tracking=True,
        index=True,
        copy=False,
        domain=lambda self: ""
        "[('res_model_id.model', '=', '" + self._name + "'), ('state', '!=', 'cancel'),"
        "'|', ('request_type_ids', '=', False), ('request_type_ids', '=', request_type_id),"
        "'|', ('hide_on_flag', '=', False), ('hide_on_flag', '!=', amount_matches_selling_price)]",
    )
    #======================================================
    #           Listing Fields (Customer Data)
    #======================================================
    customer_intent = fields.Selection(
        [
            ('direct_sale', 'Direct Sale'),
            ('auction', 'Auction'),
            ('select_all', 'Select All'),
            ('studies_recommendation', 'Studies Recommendation')
        ],
        string='Customer Intent'
    )
    partner_id = fields.Many2one('res.partner', string='Customer Name')
    customer_role_rel = fields.Many2one('customer.role', string='Customer Role', domain="[('code', 'in', ['owner', 'agent', 'broker', 'other'])]")
    owner_type = fields.Selection(
        [
            ('individual', 'Individual'),
            ('company', 'Company'),
            ('government', 'Government Agency'),
            ('investor', 'Investor')
        ],
        string='Owner Type'
    )
    partner_mobile = fields.Char(related='partner_id.mobile', string='Customer Mobile')
    entered_by_id = fields.Many2one(
        'res.users',
        string='Entered By',
    )
    entered_by_email = fields.Char(
        string='Entered By Email',
    )
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    country_id = fields.Many2one('res.country', string='Country')
    city = fields.Many2one(
        'res.country.state',
        string='City',
        domain="[('country_id.code', '=', 'SA'), ('code', 'ilike', 'CT_')]",
        tracking=True
    )
    district_id = fields.Many2one(
        'res.city',
        string='District',
        domain="[('state_id', '=', city)]",
        tracking=True
    )
    property_type = fields.Many2one('property.type', string='Property Type', tracking=True)
    area_sqm = fields.Float(string='Area (m²)', tracking=True)
    property_usage_rel = fields.Many2one('property.usage.type', string='Property Usage', domain="[('active', '=', True)]")
    current_income = fields.Monetary(
        string='Current Income', currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    plan_number = fields.Char(string='Plan Number', tracking=True)
    deed_number = fields.Char(string='Deed Number', tracking=True)
    deed_date = fields.Date(string='Deed Date', tracking=True)
    plot_number = fields.Char(string='Plot Number', tracking=True)
    customer_price_per_sqm = fields.Monetary(
        string='Customer Price per Square Meter', currency_field='currency_id'
    )
    location_url = fields.Char(string='Location', tracking=True)
    requires_technical_offer = fields.Selection( [('yes', 'Yes'),('no', 'No'), ],string='Requires Technical Offer')
    entered_notes = fields.Text(string='Notes')
    ##########################################################################################
    #                Project Path Determination Fields
    ##########################################################################################
    is_authorized_property = fields.Selection(
        [
            ('yes', 'Yes'),
            ('no', 'No'),
            ('return_to_lister', 'Return to Lister'),
            ('data_completion', 'Data Completion'),
        ],
        string='Is Authorized Property'
    )
    rejection_reason = fields.Text(string='Rejection Reason')
    return_to_lister_note = fields.Text(string='Return to Lister Note')
    project_path = fields.Selection([('cities', 'Cities'), ('specialized', 'Specialized'), ('standard', 'Standard')], tracking=True, string='Project Path')
    analyst_id = fields.Many2one('res.users', tracking=True, string='Assigned Analyst')
    detailed_analyst_id = fields.Many2one('res.users', tracking=True, string='Detailed Assigned Analyst')
    ##########################################################################################
    #          Preliminary Study Fields
    ##########################################################################################
    verified_income = fields.Monetary(string='Verified Income', currency_field='currency_id')
    expected_full_lease_income = fields.Monetary(string='Expected Income (Full Lease)', currency_field='currency_id')
    building_requirements = fields.Text(string='Building Requirements')
    justice_index_average = fields.Monetary(string='Ministry of Justice Index Average', currency_field='currency_id')
    comparison_average = fields.Monetary(string='Comparables Average', currency_field='currency_id')
    final_property_price = fields.Monetary(string='Final Property Price', currency_field='currency_id')
    analyst_recommendation_preliminary = fields.Text(string='Analyst Recommendation Preliminary')
    properties_count = fields.Integer(string='Number of Properties', default=1)
    preliminary_study_status = fields.Selection([('completed', 'Completed'), ('rejected', 'Rejected')], string='Preliminary Study Result')
    analyst_rejection_notes = fields.Text(string='Analyst Rejection Notes')
    # ==========================================================
    #                     Cities Study Fields
    # ==========================================================
    gps_coordinates = fields.Char(string="GPS Coordinates")
    area = fields.Float(string="Area")
    industrial_city = fields.Char(string="Industrial City")
    allocation_fees = fields.Float(string="Allocation Fees")
    annual_financial_fee = fields.Float(string="Annual Financial Fee")
    previous_activity = fields.Char(string="Previous Facility Activity")
    facility_investor = fields.Char(string="Facility Investor")
    investor_contact_number = fields.Char(string="Investor Contact Number")
    has_movables = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Is there any movables?", default='no')
    equipment = fields.Text(string="Equipment")
    vehicles = fields.Text(string="Vehicles")
    machinery = fields.Text(string="Machinery")
    systems = fields.Text(string="Systems")
    analyst_notes = fields.Text(string="Analyst Notes")
    facility_photo_ids = fields.Many2many('ir.attachment', 'facility_photos_phase2_rel', 'entry_id', 'attachment_id', string="Facility Photos")
    coordinates_kmz = fields.Binary(string="Coordinates File (KMZ)", attachment=True)
    coordinates_kmz_name = fields.Char(string="Coordinates File Name")
    current_income_file = fields.Binary(string="Current Income File", attachment=True)
    current_income_file_name = fields.Char(string="Current Income File Name")
    rent_contract_ids = fields.Many2many('ir.attachment', 'rent_contracts_phase2_rel', 'entry_id', 'attachment_id', string="Rent Contracts")
    #############################################################################################################
    #                Detailed Study Fields
    #############################################################################################################
    is_assign_detailed_study = fields.Boolean(string='Is Assign Detailed Study', default=False)
    analyst_recommendation_details = fields.Text(string='Analyst Recommendation Details')
    detailed_building_requirements = fields.Text(string='Building Requirements')
    detailed_final_property_price = fields.Monetary(string='Final Property Price', currency_field='currency_id')
    detailed_comparison_average = fields.Monetary(string='Comparables Average', currency_field='currency_id')
    limit_east = fields.Char(string="Limit (East)", tracking=True)
    finishing_ratio = fields.Float(string="Finishing Ratio")
    electricity_meters_count = fields.Integer(string="Number of Electricity Meters")
    sewage_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Sewage Service")
    internal_strength_points = fields.Text(string="Internal Strength Points")
    current_total_income = fields.Monetary(string="Current Total Income", currency_field='currency_id')
    precise_plot_location_link = fields.Char(string="Precise Plot Location Link")
    length_east = fields.Float(string="Length (East)", tracking=True)
    limit_north = fields.Char(string="Limit (North)", tracking=True)
    floors_count = fields.Integer(string="Number of Floors")
    electricity_meters_numbers = fields.Char(string="Electricity Meters Numbers")
    water_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Water Service")
    street = fields.Char(string="Street")
    street_length = fields.Float(string="Street Length")
    best_property_use = fields.Text(string="Best Use of Property")
    justice_ministry_index_average = fields.Monetary(string="Average Justice Ministry Index", currency_field='currency_id')
    limit_west = fields.Char(string="Limit (West)", tracking=True)
    length_north = fields.Float(string="Length (North)", tracking=True)
    units_count = fields.Integer(string="Number of Units")
    building_license_date = fields.Date(string="Building License Date")
    electricity_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Electricity Service")
    nearest_main_road = fields.Char(string="Nearest Main Road")
    external_weakness_points = fields.Text(string="External Weakness Points")
    expected_total_income_full_rent = fields.Monetary(string="Expected Total Income (Full Rent)", currency_field='currency_id')
    property_description = fields.Text(string="Property Description")
    length_west = fields.Float(string="Length (West)", tracking=True)
    limit_south = fields.Char(string="Limit (South)", tracking=True)
    property_age_estimated = fields.Char(string="Property Age (Estimated if no License)")
    building_license_number = fields.Char(string="Building License Number")
    water_meters_count = fields.Integer(string="Number of Water Meters")
    pavement_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Pavement Service")
    external_strength_points = fields.Text(string="External Strength Points")
    lowest_price_per_meter_total_property = fields.Monetary(string="Lowest Price per Meter (Total Property)", currency_field='currency_id')
    approximate_building_value_per_meter = fields.Monetary(string="Approximate Building Value per Meter", currency_field='currency_id')
    building_area = fields.Float(string="Building Area")
    length_south = fields.Float(string="Length (South)", tracking=True)
    land_nature = fields.Char(string="Land Nature (If Raw Land)")
    completion_certificate_issued = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Completion Certificate Issued?")
    water_meters_numbers = fields.Char(string="Water Meters Numbers")
    lighting_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Lighting Service")
    gas_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Gas Service")
    ac_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="AC Service")
    internet_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Internet Service")
    telecom_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Telecom Service")
    security_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Security Guard Service")
    elevator_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Elevator Service")
    pool_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Pool Service")
    garden_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Garden Service")
    parking_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Parking Service")
    construction_warranty = fields.Char(string="Construction Warranty")
    electrical_warranty = fields.Char(string="Electrical Warranty")
    plumbing_warranty = fields.Char(string="Plumbing Warranty")
    services_description = fields.Char(string="Services Description")

    internal_weakness_points = fields.Text(string="Internal Weakness Points")
    highest_price_per_meter_total_property = fields.Monetary(string="Highest Price per Meter (Total Property)", currency_field='currency_id')
    approximate_land_value_per_meter = fields.Monetary(string="Approximate Land Value per Meter", currency_field='currency_id')
    standard_study_manager_approval = fields.Selection(
        [
            ('completed', 'Completed'),
            ('incomplete', 'Incomplete'),
            ('reject_and_archive', 'Reject and Archive'),
        ],
        string='Study Manager Approval', tracking=True
    )
    specialized_study_manager_approval = fields.Selection(
        [
            ('completed', 'Completed'),
            ('incomplete', 'Incomplete'),
        ],
        string='Study Manager Approval', tracking=True
    )
    specialized_study_manager_note = fields.Text(string="Specialized Study Manager Note")
    committee_decision = fields.Selection([('direct_sale', 'Direct Sale'), ('auction', 'Auction'), ('exclusion', 'Exclusion')], string="Committee Decision", tracking=True)
    committee_decision_date = fields.Date(string="Committee Decision Date")
    marketing_duration_months = fields.Integer(string="Marketing Duration (Months)")
    committe_notes = fields.Text(string="Notes")
    committee_decision_rel = fields.Many2one(
        'committee.decision.type',
        string="Committee Decision",
        compute='_compute_committee_decision_rel_val',
        store=True,
    )
    direct_sale_price_per_meter = fields.Float(
        string="Direct Sale Price per Square Meter",
        compute='_compute_pricing_from_entry',
        store=True,
    )
    direct_sale_total_price = fields.Float(
        string="Total Direct Sale Price",
        compute='_compute_pricing_from_entry',
        store=True,
    )
    auction_price_per_meter = fields.Float(
        string="Auction Price per Square Meter",
        compute='_compute_pricing_from_entry',
        store=True,
    )
    auction_total_price = fields.Float(
        string="Total Auction Sale Price",
        compute='_compute_pricing_from_entry',
        store=True,
    )
    sales_manager_approval = fields.Selection(
        [
            ('committee_decision_accepted', 'Accept Committee Decision'),
            ('committee_decision_rejected', 'Reject Committee Decision'),
            ('request_transfer_auction', 'Request Property Transfer to Auction'),
        ],
        string="Sales Manager Decision", tracking=True
    )
    auctions_manager_approval = fields.Selection(
        [
            ('committee_decision_accepted', 'Accept Committee Decision'),
            ('committee_decision_rejected', 'Reject Committee Decision'),
            ('request_transfer_direct_sale', 'Request Property Transfer to Direct Sale'),
        ],
        string="Auctions Manager Decision", tracking=True
    )
    # First: Negotiation by Listing Owner
    final_owner_decision = fields.Selection([('committee_price', 'Approved at Committee Price'), ('higher_price', 'Approved at Another Price'), ('rejected', 'Rejected')], string="Final Owner Decision")
    final_owner_price = fields.Monetary(string="Final Owner Price", currency_field='currency_id')
    manager_negotiator_final_owner_decision = fields.Selection([('committee_price', 'Approved at Committee Price'), ('higher_price', 'Approved at Another Price'), ('rejected', 'Rejected')], string="Final Owner Decision")
    manager_negotiator_final_owner_price = fields.Monetary(string="Final Owner Price", currency_field='currency_id')
    # ── Sales and Auctions Management Stage System ──--------------------------------------------------------------------------------------------
    # ============================================================================================================
    # ============================================================================================================
    # ============================================================================================================
    # ======================= Private Auction Path Specific Fields ================================
    auction_name = fields.Char(
        string="Property/Project Name",
        related='project_id.name',
        store=True,
    )
    project_manager_id = fields.Many2one(
        'res.users',
        string='Project Manager',
        related='project_id.project_manager_id',
        store=True,
    )
    bussma_project_stage_selection = fields.Selection(
        related='project_id.bussma_project_stage_selection',
        string='Project Stage Selection',
        store=True,
    )
    auction_project_path = fields.Selection([
        ('private', 'Private'),
        ('enforcement', 'Enforcement'),
        ('city', 'City'),
    ], string='Project Path', tracking=True)
    # Project Manager Stage
    auction_category = fields.Selection([
        ('vip', 'VIP'),
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
    ], string='Auction Category', tracking=True)
    property_category = fields.Selection([
        ('vip', 'VIP'),
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
    ], string='Property Category')
    need_identity = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Need Identity', tracking=True)
    property_status = fields.Selection([
        ('new', 'New'),
        ('withdrawn', 'Withdrawn'),
        ('unsold', 'Unsold'),
    ], string='Property Status', default='new')
    property_images_url = fields.Char(string='Property Images URL')
    # Sales with Finance Stage
    price_per_meter = fields.Monetary(string='Price Per Meter', store=True, compute='_compute_price_per_meter', readonly=False, currency_field='currency_id')
    selling_price = fields.Monetary(string='Selling Price', store=True, compute='_compute_selling_price', readonly=False, currency_field='currency_id')
    saai_amount = fields.Monetary(string='Brokerage Fee', store=True, compute="_compute_saai_amount", currency_field='currency_id')
    saai_tax = fields.Monetary(string='Brokerage Fee Tax', compute='_compute_values', store=True, currency_field='currency_id')
    saai_with_tax = fields.Monetary(string='Brokerage Fee With Tax', compute='_compute_values', store=True, currency_field='currency_id')
    total_price = fields.Monetary(string='Total Price', compute='_compute_values', store=True, currency_field='currency_id')
    property_price_display = fields.Monetary(string='Property Price Display', compute='_compute_property_price_display', store=True, currency_field='currency_id')
    bidder_number = fields.Char(string='Bidder Number')
    check_amount = fields.Monetary(string='Check Amount', currency_field='currency_id')
    participant_name = fields.Char(string='Participant Name')
    participant_id_number = fields.Char(string='Participant ID Number')
    participant_mobile = fields.Char(string='Participant Mobile')
    buyer_representative_name = fields.Char(string="Buyer Representative Name")
    buyer_representative_id = fields.Char(string="Buyer Representative ID")
    buyer_representative_mobile = fields.Char(string="Buyer Representative Mobile")
    is_sold = fields.Selection(
        [
            ('yes', 'Yes'),
            ('no', 'No'),
        ],
        string='Is Soled',
    )
    real_estate_invoice = fields.Binary(string='Real Estate Invoice', attachment=True)
    real_estate_invoice_name = fields.Char(string='Real Estate Invoice Name')
    real_estate_transaction_tax = fields.Monetary(
        string='Real Estate Transaction Tax', compute='_compute_values', store=True, currency_field='currency_id'
    )
    payment_proof = fields.Binary(string='Payment Proof', attachment=True)
    payment_proof_name = fields.Char(string='Payment Proof Name')
    net_basmah_share = fields.Monetary(string='Net Basmah Share', currency_field='currency_id')
    is_sale_cancelled = fields.Boolean(string='Is Sale Cancelled', default=False)
    is_contract_cancelled = fields.Boolean(
        string='Contract Cancelled',
        default=False,
        tracking=True,
        help="Indicates whether the contract for this entry has been cancelled."
    )
    # Collection and Transfer Stage
    award_record_number = fields.Char(string='Award Record Number')
    buyer_name = fields.Char(string='Buyer Name')
    buyer_id_number = fields.Char(string='Buyer ID Number')
    buyer_mobile = fields.Char(string='Buyer Mobile')
    payment_status = fields.Selection([
        ('invoice_paid', 'Real Estate Invoice Paid'),
        ('amount_paid', 'Amount Paid'),
        ('not_paid', 'Not Paid'),
    ], string='Payment Status (Deprecated)')
    payment_status_ids = fields.Many2many(
        'payment.status',
        'sales_auction_payment_status_rel',
        'sale_auction_id',
        'payment_status_id',
        string='Payment Status',
        tracking= True,
        domain=[('active', '=', True)],
    )
    collection_notes = fields.Text(string='Collection Notes')
    transfer_status = fields.Selection([
        ('transferred', 'Transferred'),
        ('not_transferred', 'Not Transferred'),
    ], string='Transfer Status')
    transfer_notes = fields.Text(string='Transfer Notes')
    # ── Collected Amount & Receipt (Collection & Transfer) ──────────────────
    # Actually collected amount (entered by collection officer)
    collected_amount = fields.Monetary(
        string='Collected Amount',
        currency_field='currency_id',
    )
    # Collection receipt attachment
    collection_receipt = fields.Binary(string='Collection Receipt', attachment=True)
    collection_receipt_name = fields.Char(string='Collection Receipt Name')
    # Does the collected amount match the saai amount? (computed - stored for domain use)
    amount_matches_selling_price = fields.Boolean(
        string='Amount Matches Saai Amount',
        compute='_compute_amount_matches_selling_price',
        store=True,
        default=True,
    )
    # ======================= Goverment Auction - Enfath================================
    asset_number = fields.Char(string="Asset Number", tracking=True)
    court_decision_number = fields.Char(string="Court Decision Number", tracking=True)
    execution_applicant_name = fields.Char(string="Execution Applicant Name", tracking=True)
    execution_applicant_phone = fields.Char(string="Execution Applicant Phone", tracking=True)
    deed_date_hijri = fields.Char(string="Deed Date (Hijri)", tracking=True)  # Can be Char or Date depending on usage
    deed_issuer = fields.Char(string="Deed Issuer", tracking=True)
    plan_number = fields.Char(string="Plan Number")
    plot_number = fields.Char(string="Plot Number")
    property_description = fields.Text(string="Property Description")
    project_notes = fields.Text(string="Project Notes")
    auction_manager_notes = fields.Text(string="Auction Manager Notes")
    auction_manager_approval = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Auction Manager Approval")
    # Project Manager after Auction Manager Approval
    lease_contract_type = fields.Selection([
        ('electronic', 'Electronic'),
        ('normal', 'Normal'),
        ('not_applicable', 'Not Applicable'),
        ], tracking=True, string="Lease Contract Type")
    has_operation_contract = fields.Boolean(string="Has Operation Contract", tracking=True)
    lease_contract_expiry_date = fields.Date(string="Lease Contract Expiry Date", tracking=True)
    project_manager_notes = fields.Text(string="Project Manager Notes")
    studies_supervisor_data_complete = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string="Studies Supervisor Data Complete")
    studies_supervisor_data_complete_notes = fields.Text(string="Studies Supervisor Data Complete Notes")
    notes_supervisor_study = fields.Text(string="Notes of Supervisor Study")
    assigned_study_user_id = fields.Many2one(
        'res.users',
        string="Assigned Study User"
    )
    # Detailed Study for Government Auctions
    has_movables = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Is there any movables?", default='no')
    is_estimated_more_than_50k = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Is the estimate more than 50k SAR?")
    are_keys_available = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Are keys available?")
    key_location = fields.Char(string="Key Location")
    property_condition = fields.Selection([('rented', 'Rented'), ('vacant', 'Vacant')], string="Property Condition")
    are_property_images_attached = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Are property images attached?")
    studies_manager_notes_second = fields.Text(string="Studies Manager Notes")
    study_approval_second = fields.Selection([('completed', 'Completed'), ('not_completed', 'Not Completed')], string="Study Approval")
    project_manager_study_approval = fields.Selection([('approved', 'Approved'), ('rejected', 'Rejected')], string="Project Manager Study Approval")
    study_rejection_notes = fields.Text(string="Study Rejection Notes")
    analyst_return_notes = fields.Text(string="Analyst Return Notes")
    # =================== Actions fields =======================
    sales_auction_stage_selection = fields.Selection(
        related='stage_id.sales_auction_stage_selection',
        string='Phase 2 Stage',
        store=True,
        tracking=True
    )
    request_type_id = fields.Many2one('request.type', string="Phase 2 Path")
    phase2_notes = fields.Text(string="Phase 2 Notes")
    phase2_additional_info = fields.Char(string="Additional Phase 2 Info")
    is_move_to_direct_sales = fields.Boolean(string='Is Move to Direct Sales', default=False)
    is_return_to_portfolio = fields.Boolean(string='Is Return to Portfolio', default=False)
    is_single_project = fields.Boolean(string='Is Single Project', default=False)
    is_source_pvt = fields.Boolean(
        compute='_compute_source_type_flags', store=True,
        string='Source is Private Auction')
    is_source_enf = fields.Boolean(
        compute='_compute_source_type_flags', store=True,
        string='Source is Eanfaz Auction')
    is_source_sales = fields.Boolean(
        compute='_compute_source_type_flags', store=True,
        string='Source is Sales')
    is_source_city = fields.Boolean(
        compute='_compute_source_type_flags', store=True,
        string='Source is Cities Auction')
    show_studies_info = fields.Boolean(string='Show Studies Info', default=False)
    is_not_move_to_sale_fin_notes = fields.Text(string='Is Not Move to Sale Fin Notes')
    # ============================================================
    # ======== Direct Sales Path Fields ===========================
    # ============================================================
    sales_properties_count = fields.Integer(string='Properties Count')
    sales_sold_count = fields.Integer(string='Sold Count')
    sales_reserved_count = fields.Integer(string='Reserved Count')
    sales_remaining_count = fields.Integer(
        string='Remaining Count',
        compute='_compute_sales_remaining',
        store=True,
    )
    sales_buyer_name = fields.Char(string='Buyer Name')
    sales_buyer_mobile = fields.Char(string='Buyer Mobile')
    sales_market_name = fields.Char(string='Sales Market Name')
    sales_buyer_birthdate = fields.Date(string='Buyer Birthdate')
    sales_buyer_capacity = fields.Char(string='Buyer Capacity')
    sales_property_type = fields.Selection([
        ('villa', 'Villa'),
        ('land', 'Land'),
    ], string='Property Type')
    sales_agreed_amount = fields.Float(string='Agreed Amount', compute='_compute_sales_agreed_amount', store=True, readonly=False)
    sales_brokerage_fee = fields.Float(string='Brokerage Fee', compute='_compute_sales_fees', store=True)
    sales_brokerage_tax = fields.Float(string='Brokerage Tax', compute='_compute_sales_fees', store=True)
    sales_brokerage_total = fields.Float(string='Brokerage Total')
    sales_buyer_identity_attachment = fields.Binary(string='Buyer Identity Attachment',attachment=True)
    sales_buyer_identity_attachment_name = fields.Char(string='Buyer Identity Attachment Name')
    sales_agent_identity_attachment = fields.Binary(string='Agent Identity Attachment',attachment=True)
    sales_agent_identity_attachment_name = fields.Char(string='Agent Identity Attachment Name')
    commission_payment_receipt = fields.Binary(string='Commission Payment Receipt', attachment=True)
    commission_payment_receipt_name = fields.Char(string='Commission Payment Receipt Name')
    property_transfer_method = fields.Char(string='Property Transfer Method')
    transfer_proof = fields.Binary(string='Transfer Proof', attachment=True)
    transfer_proof_name = fields.Char(string='Transfer Proof Name')
    sales_evacuation_status = fields.Selection([
        ('evacuated', 'Evacuated'),
        ('not_evacuated', 'Not Evacuated'),
    ], string='Evacuation and Closing')
    # Contract with buyer
    contract_buyer_attachment = fields.Binary(string='Contract Buyer Attachment',attachment=True)
    contract_buyer_attachment_name = fields.Char(string='Contract Buyer Attachment Name')
    is_contract_with_buyer = fields.Boolean(string='Is Contract with Buyer', default=False)

    # contracting stage fields
    contract_client_name = fields.Char(string="Client Name")
    contract_client_identity = fields.Char(string="Client Identity")
    contract_client_birthdate = fields.Date(string="Client Birth Date")
    contract_client_mobile = fields.Char(string="Client Mobile Number")
    contract_client_role = fields.Selection([('owner', 'Owner'), ('agent', 'Agent')], string="His Role")
    contract_owner_name = fields.Char(string="Owner Name")
    contract_owner_identity = fields.Char(string="Owner Identity")
    contract_owner_birthdate = fields.Date(string="Owner Birth Date")
    contract_owner_mobile = fields.Char(string="Owner Mobile Number")
    contract_agency_deed_attachment = fields.Binary(string="Power of Attorney Attachment", attachment=True)
    contract_agency_deed_attachment_name = fields.Char(string="Attachment Name")
    contract_agreed_price = fields.Float(string="Agreed Price")
    contract_duration = fields.Char(string="Contract Duration")
    rooms_count = fields.Integer(string="Number of Rooms")
    property_facade = fields.Char(string="Property Facade")

    # ============================================================
    # User Role Group Flags (for form-view field visibility)
    # ============================================================
    # — from bussma_system —
    is_studies_manager_group = fields.Boolean(compute='_compute_p2_user_role_groups')
    is_analyst_group = fields.Boolean(compute='_compute_p2_user_role_groups')
    is_sales_manager_group = fields.Boolean(compute='_compute_p2_user_role_groups')
    is_auctions_manager_group = fields.Boolean(compute='_compute_p2_user_role_groups')
    # — from sales_and_auction_management —
    is_auctions_pm_group = fields.Boolean(compute='_compute_p2_user_role_groups')
    is_commercial_accountant_group = fields.Boolean(compute='_compute_p2_user_role_groups')
    is_collection_officer_group = fields.Boolean(compute='_compute_p2_user_role_groups')

    @api.depends('entry_id', 'entry_id.committee_decision_rel', 'committee_decision')
    def _compute_committee_decision_rel_val(self):
        for rec in self:
            if rec.entry_id and rec.entry_id.committee_decision_rel:
                rec.committee_decision_rel = rec.entry_id.committee_decision_rel
            elif rec.committee_decision:
                rec.committee_decision_rel = self.env['committee.decision.type'].search([('code', '=', rec.committee_decision)], limit=1)
            else:
                rec.committee_decision_rel = False

    @api.depends('entry_id', 'entry_id.direct_sale_price_per_meter', 'entry_id.direct_sale_total_price', 'entry_id.auction_price_per_meter', 'entry_id.auction_total_price')
    def _compute_pricing_from_entry(self):
        for rec in self:
            if rec.entry_id:
                rec.direct_sale_price_per_meter = rec.entry_id.direct_sale_price_per_meter or 0.0
                rec.direct_sale_total_price = rec.entry_id.direct_sale_total_price or 0.0
                rec.auction_price_per_meter = rec.entry_id.auction_price_per_meter or 0.0
                rec.auction_total_price = rec.entry_id.auction_total_price or 0.0
            else:
                rec.direct_sale_price_per_meter = 0.0
                rec.direct_sale_total_price = 0.0
                rec.auction_price_per_meter = 0.0
                rec.auction_total_price = 0.0

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields=allfields, attributes=attributes)
        if res and 'active' in res:
            res['active']['readonly'] = True
            res['active']['invisible'] = True
        return res

    @api.depends('collected_amount')
    def _compute_amount_matches_selling_price(self):
        for rec in self:
            rec.amount_matches_selling_price = bool(
                rec.collected_amount and rec.saai_amount and
                rec.collected_amount == rec.saai_amount
            )

    def _compute_p2_user_role_groups(self):
        """
        Compute boolean flags for every Phase-2 authorized role.
        Used in the form view to toggle field visibility / readonly
        based on the currently logged-in user's group membership.
        """
        user = self.env.user
        # Groups inherited from bussma_system
        is_studies_manager = (
            user.has_group('bussma_system.group_studies_manager') or
            user.has_group('bussma_system.group_deputy_studies_manager')
        )
        is_analyst = user.has_group('bussma_system.group_analyst')
        is_sales = user.has_group('bussma_system.group_sales_manager')
        is_auctions = user.has_group('bussma_system.group_auctions_manager')
        # Groups defined in sales_and_auction_management 
        is_sales_pm = user.has_group('sales_and_auction_management.group_sales_project_manager')
        is_commercial_accountant = user.has_group('sales_and_auction_management.group_commercial_sector_accountant')
        is_collection_officer = user.has_group('sales_and_auction_management.group_collection_evacuation_officer')
        for rec in self:
            rec.is_studies_manager_group = is_studies_manager
            rec.is_analyst_group = is_analyst
            rec.is_sales_manager_group = is_sales
            rec.is_auctions_manager_group = is_auctions
            rec.is_auctions_pm_group = is_sales_pm
            rec.is_commercial_accountant_group = is_commercial_accountant
            rec.is_collection_officer_group = is_collection_officer

    def action_return_to_collection(self):
        col_stage = self.env.ref(
            'sales_and_auction_management.p2_stage_shared_col_trans',
            raise_if_not_found=True,
        )
        self.write({'stage_id': col_stage.id})

    @api.depends('sales_properties_count', 'sales_sold_count', 'sales_reserved_count')
    def _compute_sales_remaining(self):
        for rec in self:
            rec.sales_remaining_count = (
                (rec.sales_properties_count or 0)
                - (rec.sales_sold_count or 0)
                - (rec.sales_reserved_count or 0)
            )

    @api.onchange('real_estate_invoice_name', 'payment_proof_name', 
                  'commission_payment_receipt_name', 'transfer_proof_name', 'entrie_name', 'sales_buyer_identity_attachment_name',
                   'sales_agent_identity_attachment_name', 'contract_buyer_attachment_name')
    def _onchange_attachment_names_p2(self):
        fields_to_check = [
            'real_estate_invoice_name',
            'payment_proof_name',
            'commission_payment_receipt_name',
            'transfer_proof_name',
            'sales_buyer_identity_attachment_name',
            'sales_agent_identity_attachment_name',
            'contract_buyer_attachment_name'
        ]
        if self.entrie_name:
            for field in fields_to_check:
                name_val = getattr(self, field)
                if name_val and self.entrie_name not in name_val:
                    setattr(self, field, f"{self.entrie_name} - {name_val}")

    @api.depends('sales_brokerage_fee')
    def _compute_sales_fees(self):
        for rec in self:
            rec.sales_brokerage_tax = rec.sales_brokerage_fee * 0.15
            rec.sales_brokerage_total = rec.sales_brokerage_fee + rec.sales_brokerage_tax

    @api.depends('selling_price', 'area_sqm')
    def _compute_price_per_meter(self):
        for rec in self:
            if rec.selling_price and rec.area_sqm:
                rec.price_per_meter = rec.selling_price / rec.area_sqm

    @api.depends('price_per_meter', 'area_sqm')
    def _compute_selling_price(self):
        for rec in self:
            if rec.price_per_meter and rec.area_sqm:
                rec.selling_price = rec.price_per_meter * rec.area_sqm

    @api.depends('selling_price', 'saai_amount', 'price_per_meter', 'sales_brokerage_fee')
    def _compute_saai_amount(self):
        for rec in self:
            # Commission calculation (saai_amount):
            if rec.sales_brokerage_fee and not rec.selling_price:
                rec.saai_amount = rec.sales_brokerage_fee
            else:
                rec.saai_amount = rec.selling_price * 0.025

    @api.depends('selling_price', 'saai_amount', 'price_per_meter', 'is_source_sales', 'sales_brokerage_fee')
    def _compute_values(self):
        for rec in self:
            rec.saai_tax = rec.saai_amount * 0.15
            rec.saai_with_tax = rec.saai_amount + rec.saai_tax
            rec.total_price = rec.selling_price + rec.saai_with_tax
            rec.real_estate_transaction_tax = rec.selling_price * 0.05

    @api.depends('manager_negotiator_final_owner_price', 'final_owner_price')
    def _compute_property_price_display(self):
        for rec in self:
            if rec.manager_negotiator_final_owner_price:
                rec.property_price_display = rec.manager_negotiator_final_owner_price
            else:
                rec.property_price_display = rec.final_owner_price

    @api.depends('manager_negotiator_final_owner_price', 'final_owner_price')
    def _compute_sales_agreed_amount(self):
        for rec in self:
            if rec.manager_negotiator_final_owner_price:
                rec.sales_agreed_amount = rec.manager_negotiator_final_owner_price
            else:
                rec.sales_agreed_amount = rec.final_owner_price

    @api.depends('request_type_id')
    def _compute_source_type_flags(self):
        pvt = self.env.ref('sales_and_auction_management.p2_type_auction_pvt', raise_if_not_found=False)
        enf = self.env.ref('sales_and_auction_management.p2_type_auction_enf', raise_if_not_found=False)
        sales = self.env.ref('sales_and_auction_management.p2_type_sales', raise_if_not_found=False)
        city = self.env.ref('sales_and_auction_management.p2_type_auction_city', raise_if_not_found=False)
        for rec in self:
            rec.is_source_pvt = bool(pvt and rec.request_type_id == pvt)
            rec.is_source_enf = bool(enf and rec.request_type_id == enf)
            rec.is_source_sales = bool(sales and rec.request_type_id == sales)
            rec.is_source_city = bool(city and rec.request_type_id == city)
            
    @api.depends('request_type_id', 'auction_project_path')
    def _compute_project_type_selection(self):
        sales_type = self.env.ref('sales_and_auction_management.p2_type_sales', raise_if_not_found=False)
        enf_type = self.env.ref('sales_and_auction_management.p2_type_auction_enf', raise_if_not_found=False)
        pvt_type = self.env.ref('sales_and_auction_management.p2_type_auction_pvt', raise_if_not_found=False)
        city_type = self.env.ref('sales_and_auction_management.p2_type_auction_city', raise_if_not_found=False)
        for rec in self:
            if sales_type and rec.request_type_id == sales_type:
                rec.project_type_selection = 'sales'
            elif enf_type and rec.request_type_id == enf_type:
                rec.project_type_selection = 'auction_enf'
            elif city_type and rec.request_type_id == city_type:
                rec.project_type_selection = 'city'
            elif pvt_type and rec.request_type_id == pvt_type:
                rec.project_type_selection = 'auction_pvt'
            else:
                rec.project_type_selection = False

    @api.depends('project_id', 'project_id.is_basic')
    def _compute_is_project_basic(self):
        sales_basic = self.env.ref('sales_and_auction_management.project_sales_basic', raise_if_not_found=False)
        for rec in self:
            if not rec.project_id:
                rec.is_project_basic = True
            elif rec.project_id.is_basic or (sales_basic and rec.project_id == sales_basic):
                rec.is_project_basic = True
            else:
                rec.is_project_basic = False

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        if view_type == 'form' and self._context.get('active_id'):
            record = self.browse(self._context['active_id'])
            if record.exists():
                if record.is_source_sales:
                    v = self.env.ref('sales_and_auction_management.view_entries_sales_form', raise_if_not_found=False)
                    if v:
                        view_id = v.id
                elif record.is_source_enf:
                    v = self.env.ref('sales_and_auction_management.view_entries_eanfaz_form', raise_if_not_found=False)
                    if v:
                        view_id = v.id
                else:
                    v = self.env.ref('sales_and_auction_management.view_entries_auction_form', raise_if_not_found=False)
                    if v:
                        view_id = v.id

        result = super().get_view(view_id=view_id, view_type=view_type, **options)

        if view_type == 'form' and result.get('arch'):
            arch_node = etree.fromstring(result['arch'])
            # Lock all fields when contract is cancelled
            for node in arch_node.iter('field'):
                name = node.get('name')
                if name and name not in ('is_contract_cancelled', 'active', 'stage_id', 'project_id'):
                    ro = node.get('readonly')
                    if not ro:
                        node.set('readonly', 'is_contract_cancelled')
                    elif ro not in ('1', 'True', 'true'):
                        node.set('readonly', f"is_contract_cancelled or ({ro})")

            # Hide workflow buttons when contract is cancelled
            exempt_buttons = {'action_cancel_contract', 'action_reactivate_contract', 'action_archive', 'action_return_from_archive'}
            for header in arch_node.iter('header'):
                for btn in header.iter('button'):
                    bname = btn.get('name')
                    if bname and bname not in exempt_buttons:
                        inv = btn.get('invisible')
                        if not inv:
                            btn.set('invisible', 'is_contract_cancelled')
                        elif inv not in ('1', 'True', 'true'):
                            btn.set('invisible', f"is_contract_cancelled or ({inv})")

            result['arch'] = etree.tostring(arch_node, encoding='unicode').replace('\t', '')

        return result

    def fields_view_get(self, view_id=None, view_type='form', **options):
        if view_type == 'form' and self._context.get('active_id'):
            record = self.browse(self._context['active_id'])
            if record.is_source_sales:
                view_id = self.env.ref('sales_and_auction_management.view_entries_sales_form').id
            elif record.is_source_enf:
                view_id = self.env.ref('sales_and_auction_management.view_entries_eanfaz_form').id
            else:
                view_id = self.env.ref('sales_and_auction_management.view_entries_auction_form').id
        return super().fields_view_get(view_id=view_id, view_type=view_type, **options)

    def action_send_to_project_manager(self):
        """ Eanfaz: portfolio → project manager stage. Sends PM assignment email. """
        self.ensure_one()
        self._check_phase2_mandatory_fields()
        if not self.project_id or self.project_id.is_basic:
            raise exceptions.UserError(_("You must assign the property to a project first (it cannot be sent while still in the basic portfolio)."))
        stage_portfolio_inf = self.env.ref('sales_and_auction_management.p2_auction_enf_portfolio', raise_if_not_found=False)
        if self.is_source_enf and stage_portfolio_inf:
            self.write({'stage_id': self.env.ref('sales_and_auction_management.p2_auction_enf_project_manager', raise_if_not_found=False).id, 'amount_matches_selling_price': True})
    
    def action_send_to_supervisor(self):
        self.ensure_one()
        self._check_phase2_mandatory_fields()
        stage_project_manager_inf = self.env.ref('sales_and_auction_management.p2_auction_enf_project_manager', raise_if_not_found=False)
        if self.is_source_enf and stage_project_manager_inf:
            # Trigger Detailed Study creation on transition to Eanfaz supervisor stage
            self._create_detailed_study_eanfaz()
            self.write({
                'stage_id': self.env.ref('sales_and_auction_management.p2_auction_enf_supervisor', raise_if_not_found=False).id,
                'analyst_return_notes': False,
            })

    def action_send_to_detailed_study(self):
        """ Eanfaz: supervisor → detailed study stage. Sends study-user assignment email. """
        self.ensure_one()
        self._check_phase2_mandatory_fields()
        stage_supervisor_inf = self.env.ref('sales_and_auction_management.p2_auction_enf_supervisor', raise_if_not_found=False)
        if self.is_source_enf and stage_supervisor_inf:
            self.write({'stage_id': self.env.ref('sales_and_auction_management.p2_auction_enf_detailed', raise_if_not_found=False).id})
            # Send email to the assigned study user
            self._send_sales_auction_email(
                'sales_and_auction_management.email_template_sales_auction_study_user_assigned',
                self.assigned_study_user_id,
            )

    def action_send_to_project_manager_approval(self):
        self.ensure_one()
        self._check_phase2_mandatory_fields()
        stage_detailed_appr_inf = self.env.ref('sales_and_auction_management.p2_auction_enf_detailed_appr', raise_if_not_found=False)
        if self.is_source_enf and stage_detailed_appr_inf:
            self.write({'stage_id': self.env.ref('sales_and_auction_management.p2_auction_enf_pm_appr', raise_if_not_found=False).id})


    def action_enf_pm_appr_move_to_buyer_contracting(self):
        self.ensure_one()
        buyer_stage = self.env.ref('sales_and_auction_management.p2_stage_shared_buyer_contracting', raise_if_not_found=True)
        self.write({
            'stage_id': buyer_stage.id,
        })

    def action_send_to_sales_fin(self):
        self.ensure_one()
        self._check_phase2_mandatory_fields()
        if self.is_source_enf:
            self.write({'stage_id': self.env.ref('sales_and_auction_management.p2_stage_shared_sales_fin', raise_if_not_found=False).id})

    def action_return_to_pm(self):
        self.ensure_one()
        stage = self.env.ref('sales_and_auction_management.p2_auction_enf_project_manager', raise_if_not_found=False)
        if stage:
            self.write({'stage_id': stage.id})

    def action_open_return_to_pm_wizard(self):
        self.ensure_one()
        return {
            'name': _('Return to Project Manager'),
            'type': 'ir.actions.act_window',
            'res_model': 'entries.phase2.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_entry_id': self.id,
            }
        }

    def action_return_to_detailed_study(self):
        self.ensure_one()
        stage = self.env.ref('sales_and_auction_management.p2_auction_enf_detailed', raise_if_not_found=False)
        if stage:
            self.write({'stage_id': stage.id})
        detailed_study = self.env['entries'].search([
            ('sale_auction_id', '=', self.id),
            ('request_type_id', '=', self.env.ref('sales_and_auction_management.detailed_study_eanfaz').id)
        ], limit=1)
        if detailed_study:
            entriy_stage = self.env.ref('sales_and_auction_management.stage_detailed_study_eanfaz', raise_if_not_found=False)
            if entriy_stage:
                detailed_study.write({
                    'stage_id': entriy_stage.id, 
                    'study_rejection_notes': self.study_rejection_notes
                })
                
    def action_move_to_collection(self):
        self.ensure_one()
        self._check_phase2_mandatory_fields()
        col_stage = self.env.ref(
            'sales_and_auction_management.p2_stage_shared_col_trans',
            raise_if_not_found=True,
        )
        self.write({'stage_id': col_stage.id})

    def action_reject_to_portfolio(self):
        self.ensure_one()
        pvt_type = self.env.ref('sales_and_auction_management.p2_type_auction_pvt', raise_if_not_found=False)
        if not (pvt_type and self.request_type_id == pvt_type):
            raise exceptions.UserError(_('This action is only for the auction-private path.'))
        portfolio_stage = self.env.ref(
            'sales_and_auction_management.p2_stage_auction_pvt_portfolio',
            raise_if_not_found=True,
        )
        project_id = self.env.ref('sales_and_auction_management.project_auctions_pvt_basic', raise_if_not_found=False)
        if self.is_single_project:
            self.write({'is_single_project': False})
        self.write({'stage_id': portfolio_stage.id, 'is_return_to_portfolio': True, 'property_status': 'unsold', 'project_id': project_id.id if project_id else False})

    def action_reject_to_archive(self):
        self.ensure_one()
        enf_type = self.env.ref('sales_and_auction_management.p2_type_auction_enf', raise_if_not_found=False)
        if not (enf_type and self.request_type_id == enf_type):
            raise exceptions.UserError(_('This action is only for the auction-enfaz path.'))
        archive_stage = self.env.ref(
            'sales_and_auction_management.p2_stage_shared_archive',
            raise_if_not_found=True,
        )
        self.write({'stage_id': archive_stage.id})

    def action_city_move_to_sales_fin(self):
        """ Cities: project management → Sales & Finance shared stage. """
        self.ensure_one()
        if not self.is_source_city:
            raise exceptions.UserError(_('This action is only for the auction-city path.'))
        self._check_phase2_mandatory_fields()
        stage = self.env.ref('sales_and_auction_management.p2_stage_shared_sales_fin', raise_if_not_found=True)
        self.write({'stage_id': stage.id})

    def action_city_reject_to_portfolio(self):
        """ Cities: return to Cities Portfolio stage and reset to basic project. """
        self.ensure_one()
        if not self.is_source_city:
            raise exceptions.UserError(_('This action is only for the auction-city path.'))
        portfolio_stage = self.env.ref('sales_and_auction_management.p2_stage_auction_city_portfolio', raise_if_not_found=True)
        project_id = self.env.ref('sales_and_auction_management.project_cities_basic', raise_if_not_found=False)
        self.write({
            'stage_id': portfolio_stage.id,
            'is_return_to_portfolio': True,
            'property_status': 'unsold',
            'project_id': project_id.id if project_id else False,
        })

    def action_accept(self):
        self.ensure_one()
        return super().action_accept()

    def action_move_to_archive(self):
        """Move property directly to Archive (only when amounts match or from other stages)."""
        self.ensure_one()
        pvt_portfolio_stage = self.env.ref('sales_and_auction_management.p2_stage_auction_pvt_portfolio', raise_if_not_found=False)
        if pvt_portfolio_stage and self.stage_id == pvt_portfolio_stage and self.is_sold == 'no':
            pass
        else:
            self._check_phase2_mandatory_fields()
        # ── Normal archive routing ───────────────────────────────────────────
        if self.is_source_sales:
            archive_stage = self.env.ref('sales_and_auction_management.p2_stage_sales_archive', raise_if_not_found=True)
        elif self.is_source_pvt or self.is_source_enf or self.is_source_city:
            archive_stage = self.env.ref('sales_and_auction_management.p2_stage_shared_archive', raise_if_not_found=True)
        self.write({'stage_id': archive_stage.id})

    def action_send_to_sector_manager(self):
        """Send to Sector Manager Approval when collected_amount ≠ selling_price."""
        self.ensure_one()
        self._check_phase2_mandatory_fields()
        if not self.collected_amount:
            raise UserError(_("Please enter the collected amount first."))
        if self.amount_matches_selling_price:
            raise UserError(_("The collected amount matches the selling price — use 'Move to Archive' directly."))
        sector_stage = self.env.ref(
            'sales_and_auction_management.p2_stage_sector_manager_approval',
            raise_if_not_found=True,
        )
        self.write({'stage_id': sector_stage.id})

    def action_move_from_sector_approval_to_archive(self):
        """From Sector Manager Approval → Archive (used by sector manager role)."""
        self.ensure_one()
        self._check_phase2_mandatory_fields()
        if self.is_source_sales:
            archive_stage = self.env.ref('sales_and_auction_management.p2_stage_sales_archive', raise_if_not_found=True)
        else:
            archive_stage = self.env.ref('sales_and_auction_management.p2_stage_shared_archive', raise_if_not_found=True)
        self.write({'stage_id': archive_stage.id})

    def action_return_from_archive(self):
        self.ensure_one()
        # Define the target stages
        sales_portfolio = self.env.ref('sales_and_auction_management.p2_stage_sales_direct_mgmt', raise_if_not_found=False)
        pvt_portfolio = self.env.ref('sales_and_auction_management.p2_stage_auction_pvt_portfolio', raise_if_not_found=False)
        enf_portfolio = self.env.ref('sales_and_auction_management.p2_auction_enf_portfolio', raise_if_not_found=False)
        city_portfolio = self.env.ref('sales_and_auction_management.p2_stage_auction_city_portfolio', raise_if_not_found=False)
        project_id = False
        if self.is_source_sales:
            project_id = self.env.ref('sales_and_auction_management.project_sales_basic', raise_if_not_found=False)
        elif self.is_source_pvt:
            project_id = self.env.ref('sales_and_auction_management.project_auctions_pvt_basic', raise_if_not_found=False)
        elif self.is_source_enf:
            project_id = self.env.ref('sales_and_auction_management.project_auctions_enf_basic', raise_if_not_found=False)
        elif self.is_source_city:
            project_id = self.env.ref('sales_and_auction_management.project_cities_basic', raise_if_not_found=False)
        # Get request types
        pvt_type = self.env.ref('sales_and_auction_management.p2_type_auction_pvt', raise_if_not_found=False)
        enf_type = self.env.ref('sales_and_auction_management.p2_type_auction_enf', raise_if_not_found=False)
        sales_type = self.env.ref('sales_and_auction_management.p2_type_sales', raise_if_not_found=False)
        city_type = self.env.ref('sales_and_auction_management.p2_type_auction_city', raise_if_not_found=False)
        target_stage = False
        if self.request_type_id == sales_type:
            target_stage = sales_portfolio
        elif self.request_type_id == pvt_type:
            target_stage = pvt_portfolio
        elif self.request_type_id == enf_type:
            target_stage = enf_portfolio
        elif self.request_type_id == city_type:
            target_stage = city_portfolio
            
        if target_stage:
            self.write({'stage_id': target_stage.id, 'project_id': project_id.id if project_id else False})
        else:
            raise exceptions.UserError(_("No valid return stage found for this path."))

    def action_cancel_sale(self):
        self.ensure_one()
        self.is_sale_cancelled = True

    def action_cancel_contract(self):
        self.ensure_one()
        self.is_contract_cancelled = True

    def action_reactivate_contract(self):
        self.ensure_one()
        buyer_stage = self.env.ref(
            'sales_and_auction_management.p2_stage_shared_buyer_contracting',
            raise_if_not_found=True
        )
        return self.with_context(bypass_contract_cancelled_check=True).write({
            'is_contract_cancelled': False,
            'stage_id': buyer_stage.id,
        })

    def action_archive(self):
        """Move record to Archive stage (Sales Archive or Auctions Archive)."""
        self.ensure_one()
        if self.is_source_sales:
            archive_stage = self.env.ref('sales_and_auction_management.p2_stage_sales_archive', raise_if_not_found=True)
        else:
            archive_stage = self.env.ref('sales_and_auction_management.p2_stage_shared_archive', raise_if_not_found=True)
        return self.with_context(bypass_contract_cancelled_check=True).write({'stage_id': archive_stage.id})

    def action_confirm_cancellation_and_archive(self):
        self.ensure_one()
        if not self.net_basmah_share:
             raise exceptions.UserError(_("Please fill the 'Net Basmah Share' field before archiving."))
        if self.is_source_sales:
            archive_stage = self.env.ref('sales_and_auction_management.p2_stage_sales_archive', raise_if_not_found=True)
        else:
            archive_stage = self.env.ref('sales_and_auction_management.p2_stage_shared_archive', raise_if_not_found=True)
        self.write({
            'stage_id': archive_stage.id,
        })

    def action_move_to_sales_fin_manual(self):
        self.ensure_one()
        if self.sales_auction_stage_selection == 'p2_shared_buyer_contracting':
            self._check_phase2_mandatory_fields()
            sales_fin_stage = self.env.ref('sales_and_auction_management.p2_stage_shared_sales_fin', raise_if_not_found=True)
            self.write({'stage_id': sales_fin_stage.id, 'is_not_move_to_sale_fin_notes': False})

    def _check_phase2_mandatory_fields(self):
        """ Helper method to check mandatory fields at each stage for Phase 2 """
        self.ensure_one()
        fields_to_check = []
        if self.sales_auction_stage_selection == 'p2_shared_buyer_contracting':
            fields_to_check = [
                'sales_buyer_name', 'sales_buyer_mobile', 'sales_buyer_birthdate',
                'sales_buyer_capacity', 'sales_buyer_identity_attachment',
                'sales_property_type', 'sales_agreed_amount', 'sales_brokerage_fee',
                'sales_market_name',
            ]
            if self.is_contract_with_buyer:
                fields_to_check.append('contract_buyer_attachment')

        if self.is_source_pvt:
            if self.sales_auction_stage_selection == 'p2_auction_pvt_portfolio':
                fields_to_check = ['project_id']
            elif self.sales_auction_stage_selection == 'p2_shared_sales_fin':
                fields_to_check = ['selling_price', 'saai_amount', 'bidder_number', 'check_amount', 'participant_name', 'participant_id_number', 'participant_mobile', 'is_sold', 'buyer_representative_name', 'buyer_representative_id', 'buyer_representative_mobile']
            elif self.sales_auction_stage_selection == 'p2_shared_col_trans':
                fields_to_check = ['real_estate_invoice','payment_proof', 'award_record_number', 'payment_status_ids', 'transfer_status']
        if self.is_source_enf:
            if self.sales_auction_stage_selection == 'p2_auction_enf_portfolio':
                fields_to_check = ['project_id']
            elif self.sales_auction_stage_selection == 'p2_auction_enf_project_manager':
                fields_to_check = [
                    'auction_project_path', 'auction_category', 'asset_number',
                    'court_decision_number', 'execution_applicant_name', 'execution_applicant_phone',
                    'deed_number', 'deed_date', 'deed_issuer',
                    'plan_number', 'plot_number', 'city', 'district_id',
                    'property_type', 'area_sqm', 'location_url',
                    'limit_north', 'length_north', 'limit_south', 'length_south',
                    'limit_east', 'length_east', 'limit_west', 'length_west',
                    'property_description', 'project_notes',
                    'lease_contract_type', 'lease_contract_expiry_date', 'project_manager_notes',
                ]
            elif self.sales_auction_stage_selection == 'p2_auction_enf_sup':
                fields_to_check = ['studies_supervisor_data_complete', 'assigned_study_user_id']
            elif self.sales_auction_stage_selection == 'p2_auction_enf_detailed':
                fields_to_check = [
                    'has_movables', 'are_keys_available',
                    'property_condition', 'property_usage_rel',
                    'limit_east', 'limit_west', 'limit_north', 'limit_south',
                    'street', 'nearest_main_road',
                    'length_east', 'length_west', 'length_north', 'length_south',
                    'building_area', 'floors_count', 'units_count', 'property_age_estimated',
                    'land_nature', 'building_license_number', 'building_license_date',
                    'building_requirements', 'electricity_meters_count', 'electricity_meters_numbers',
                    'water_meters_count', 'water_meters_numbers',
                    'current_total_income', 'expected_total_income_full_rent',
                    'detailed_comparison_average', 'justice_ministry_index_average',
                    'lowest_price_per_meter_total_property', 'highest_price_per_meter_total_property',
                    'approximate_building_value_per_meter', 'approximate_land_value_per_meter',
                    'detailed_final_property_price',
                    'internal_strength_points', 'internal_weakness_points',
                    'external_strength_points', 'external_weakness_points',
                    'best_property_use', 'are_property_images_attached', 'finishing_ratio',
                ]
                if self.has_movables == 'yes':
                    fields_to_check.append('is_estimated_more_than_50k')
                if self.are_keys_available == 'yes':
                    fields_to_check.append('key_location')
            elif self.sales_auction_stage_selection == 'p2_auction_enf_detailed_appr':
                fields_to_check = ['study_approval_second']
            elif self.sales_auction_stage_selection == 'p2_auction_enf_pm_appr':
                fields_to_check = ['project_manager_study_approval']
            elif self.sales_auction_stage_selection == 'p2_shared_sales_fin':
                fields_to_check = [
                    'selling_price', 'saai_amount', 'bidder_number', 'check_amount',
                    'participant_name', 'participant_id_number', 'participant_mobile',
                    'is_sold', 'buyer_representative_name', 'buyer_representative_id',
                    'buyer_representative_mobile',
                ]
            elif self.sales_auction_stage_selection == 'p2_shared_col_trans':
                fields_to_check = [
                    'payment_proof',
                    'real_estate_invoice', 'award_record_number', 
                    'payment_status_ids', 'transfer_status',
                ]
        if self.is_source_sales:
            if self.sales_auction_stage_selection == 'p2_sales_direct_mgmt':
                fields_to_check = ['project_id']
            elif self.sales_auction_stage_selection == 'p2_shared_buyer_contracting':
                pass  # handled above
            elif self.sales_auction_stage_selection == 'p2_shared_sales_fin':
                fields_to_check = [
                    'selling_price', 'saai_amount', 'real_estate_transaction_tax',
                    'is_sold'
                ]
            elif self.sales_auction_stage_selection == 'p2_shared_col_trans':
                fields_to_check = [
                    'real_estate_invoice', 'payment_proof', 'award_record_number', 'payment_status_ids', 'transfer_status',
                ]
        if self.is_source_city:
            if self.sales_auction_stage_selection == 'p2_auction_city_portfolio':
                fields_to_check = ['project_id']
            elif self.sales_auction_stage_selection == 'p2_shared_sales_fin':
                fields_to_check = ['selling_price', 'saai_amount', 'bidder_number', 'check_amount', 'participant_name', 'participant_id_number', 'participant_mobile', 'is_sold', 'buyer_representative_name', 'buyer_representative_id', 'buyer_representative_mobile']
            elif self.sales_auction_stage_selection == 'p2_shared_col_trans':
                fields_to_check = ['real_estate_invoice', 'payment_proof', 'award_record_number', 'payment_status_ids', 'transfer_status']
        missing = [f for f in fields_to_check if not getattr(self, f)]
        if missing:
            labels = [self.fields_get([f])[f]['string'] for f in missing]
            stage_name = self.stage_id.name or ''
            raise exceptions.UserError(_("Stage: %s\n\nFields that are required:\n- %s") % (stage_name, "\n- ".join(labels)))

    def action_move_to_pm(self):
        """ Direct Sales: listing → direct-mgmt stage (kept for backward compatibility). """
        self.ensure_one()
        if self.is_source_sales:
            stage = self.env.ref(
                'sales_and_auction_management.p2_stage_sales_direct_mgmt',
                raise_if_not_found=True,
            )
            self.write({'stage_id': stage.id})

    def action_sales_contract_with_buyer(self):
        self.ensure_one()
        self._check_phase2_mandatory_fields()

        self.write({'is_contract_with_buyer': True})

    def action_sales_move_to_sales_fin(self):
        self.ensure_one()
        self._check_phase2_mandatory_fields()
        sales_fin_stage = self.env.ref('sales_and_auction_management.p2_stage_shared_sales_fin', raise_if_not_found=True)
        self.write({'stage_id': sales_fin_stage.id})

    def action_sales_move_to_archive(self):
        self.ensure_one()
        if self.is_sold != 'no':
            self._check_phase2_mandatory_fields()
        archive_stage = self.env.ref('sales_and_auction_management.p2_stage_sales_archive', raise_if_not_found=True)
        self.write({'stage_id': archive_stage.id})

    def action_move_to_direct_sales(self):
        self.ensure_one()
        if self.is_sold == 'yes':
            raise exceptions.UserError(
                _('The property cannot be directed to direct sales because it is already sold.')
            )
        sales_stage = self.env.ref('sales_and_auction_management.p2_stage_sales_direct_mgmt')
        sales_type = self.env.ref('sales_and_auction_management.p2_type_sales')
        project_id = self.env.ref('sales_and_auction_management.project_sales_basic', raise_if_not_found=False)
        self.write({
            'request_type_id': sales_type.id,
            'stage_id': sales_stage.id,
            'is_move_to_direct_sales': True,
            'project_id': project_id.id if project_id else False,
        })

    def action_move_to_auctions_portfolio(self):
        self.ensure_one()
        pvt_stage = self.env.ref('sales_and_auction_management.p2_stage_auction_pvt_portfolio')
        pvt_type = self.env.ref('sales_and_auction_management.p2_type_auction_pvt')
        project_id = self.env.ref('sales_and_auction_management.project_auctions_pvt_basic', raise_if_not_found=False)
        self.write({
            'request_type_id': pvt_type.id,
            'auction_project_path': 'private',
            'stage_id': pvt_stage.id,
            'project_id': project_id.id if project_id else False,
        })

    def action_return_to_portfolio(self):
        self.ensure_one()
        project_id = False
        if self.is_source_enf:
            stage = self.env.ref('sales_and_auction_management.p2_auction_enf_portfolio')
            project_id = self.env.ref('sales_and_auction_management.project_auctions_enf_basic', raise_if_not_found=False)
        elif self.is_source_city:
            stage = self.env.ref('sales_and_auction_management.p2_stage_auction_city_portfolio')
            project_id = self.env.ref('sales_and_auction_management.project_cities_basic', raise_if_not_found=False)
        elif self.is_source_pvt:
            stage = self.env.ref('sales_and_auction_management.p2_stage_auction_pvt_portfolio')
            project_id = self.env.ref('sales_and_auction_management.project_auctions_pvt_basic', raise_if_not_found=False)
        elif self.is_source_sales:
            stage = self.env.ref('sales_and_auction_management.p2_stage_sales_direct_mgmt')
            project_id = self.env.ref('sales_and_auction_management.project_sales_basic', raise_if_not_found=False)
            self.write({
                'stage_id': stage.id,
                'is_return_to_portfolio': True,
                'project_id': project_id.id if project_id else False,
            })
            return

        self.write({
            'stage_id': stage.id,
            'is_move_to_direct_sales': False,
            'is_return_to_portfolio': True,
            'project_id': project_id.id if project_id else False,
        })

    def action_return_to_auction_archive(self):
        self.ensure_one()
        stage = self.env.ref('sales_and_auction_management.p2_stage_shared_archive')
        self.write({
            'stage_id': stage.id,
            'is_move_to_direct_sales': False,
        })

    def action_assign_to_project(self):
        project_id = self.env.context.get('project_to_assign')
        if project_id and self:
            self.write({
                'project_id': project_id, 
            })
        return {'type': 'ir.actions.act_window_close'}

    def action_remove_from_project(self):
        self.ensure_one()
        sales_type = self.env.ref('sales_and_auction_management.p2_type_sales', raise_if_not_found=False)
        pvt_type = self.env.ref('sales_and_auction_management.p2_type_auction_pvt', raise_if_not_found=False)
        enf_type = self.env.ref('sales_and_auction_management.p2_type_auction_enf', raise_if_not_found=False)
        city_type = self.env.ref('sales_and_auction_management.p2_type_auction_city', raise_if_not_found=False)
        
        target_project = False
        if sales_type and self.request_type_id == sales_type:
            target_project = self.env.ref('sales_and_auction_management.project_sales_basic', raise_if_not_found=False)
        elif enf_type and self.request_type_id == enf_type:
            target_project = self.env.ref('sales_and_auction_management.project_auctions_enf_basic', raise_if_not_found=False)
        elif city_type and self.request_type_id == city_type:
            target_project = self.env.ref('sales_and_auction_management.project_cities_basic', raise_if_not_found=False)
        elif pvt_type and self.request_type_id == pvt_type:
            target_project = self.env.ref('sales_and_auction_management.project_auctions_pvt_basic', raise_if_not_found=False)
            
        self.write({'project_id': target_project.id if target_project else False})




    @api.depends('entrie_name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.entrie_name

    def init(self):
        super().init()
        # Idempotent migration of payment_status selection and legacy payment_status_id column to Many2many (payment_status_ids) via XML IDs
        self.env.cr.execute("""
            DO $$
            DECLARE
                v_invoice_paid_id INT;
                v_amount_paid_id INT;
                v_not_paid_id INT;
                v_is_jsonb BOOLEAN := FALSE;
            BEGIN
                -- 1. Ensure relation table for payment_status_ids exists
                -- The column 'payment_status_id' in this table is the FK pointing to payment.status(id)
                CREATE TABLE IF NOT EXISTS sales_auction_payment_status_rel (
                    sale_auction_id INT NOT NULL,
                    payment_status_id INT NOT NULL,
                    PRIMARY KEY (sale_auction_id, payment_status_id)
                );

                IF EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = 'payment_status'
                ) THEN
                    SELECT (data_type = 'jsonb') INTO v_is_jsonb
                    FROM information_schema.columns
                    WHERE table_name = 'payment_status'
                      AND column_name = 'name';

                    -- Ensure records exist in payment_status and ir_model_data if data file has not loaded yet
                    IF NOT EXISTS (
                        SELECT 1 FROM ir_model_data
                        WHERE module = 'sales_and_auction_management'
                          AND name = 'payment_status_invoice_paid'
                    ) THEN
                        IF v_is_jsonb THEN
                            INSERT INTO payment_status (name, active, create_date, write_date)
                            VALUES (jsonb_build_object('en_US', 'Real Estate Invoice Paid'), true, now(), now())
                            RETURNING id INTO v_invoice_paid_id;
                        ELSE
                            INSERT INTO payment_status (name, active, create_date, write_date)
                            VALUES ('Real Estate Invoice Paid', true, now(), now())
                            RETURNING id INTO v_invoice_paid_id;
                        END IF;

                        INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
                        VALUES ('payment_status_invoice_paid', 'sales_and_auction_management', 'payment.status', v_invoice_paid_id, false);
                    ELSE
                        SELECT res_id INTO v_invoice_paid_id
                        FROM ir_model_data
                        WHERE module = 'sales_and_auction_management'
                          AND name = 'payment_status_invoice_paid'
                        LIMIT 1;
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM ir_model_data
                        WHERE module = 'sales_and_auction_management'
                          AND name = 'payment_status_amount_paid'
                    ) THEN
                        IF v_is_jsonb THEN
                            INSERT INTO payment_status (name, active, create_date, write_date)
                            VALUES (jsonb_build_object('en_US', 'Amount Paid'), true, now(), now())
                            RETURNING id INTO v_amount_paid_id;
                        ELSE
                            INSERT INTO payment_status (name, active, create_date, write_date)
                            VALUES ('Amount Paid', true, now(), now())
                            RETURNING id INTO v_amount_paid_id;
                        END IF;

                        INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
                        VALUES ('payment_status_amount_paid', 'sales_and_auction_management', 'payment.status', v_amount_paid_id, false);
                    ELSE
                        SELECT res_id INTO v_amount_paid_id
                        FROM ir_model_data
                        WHERE module = 'sales_and_auction_management'
                          AND name = 'payment_status_amount_paid'
                        LIMIT 1;
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1 FROM ir_model_data
                        WHERE module = 'sales_and_auction_management'
                          AND name = 'payment_status_not_paid'
                    ) THEN
                        IF v_is_jsonb THEN
                            INSERT INTO payment_status (name, active, create_date, write_date)
                            VALUES (jsonb_build_object('en_US', 'Not Paid'), true, now(), now())
                            RETURNING id INTO v_not_paid_id;
                        ELSE
                            INSERT INTO payment_status (name, active, create_date, write_date)
                            VALUES ('Not Paid', true, now(), now())
                            RETURNING id INTO v_not_paid_id;
                        END IF;

                        INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
                        VALUES ('payment_status_not_paid', 'sales_and_auction_management', 'payment.status', v_not_paid_id, false);
                    ELSE
                        SELECT res_id INTO v_not_paid_id
                        FROM ir_model_data
                        WHERE module = 'sales_and_auction_management'
                          AND name = 'payment_status_not_paid'
                        LIMIT 1;
                    END IF;

                    -- 2. Migrate from legacy column payment_status_id if it exists in sales_auction_management
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'sales_auction_management'
                          AND column_name = 'payment_status_id'
                          AND data_type IN ('integer', 'bigint', 'smallint')
                    ) THEN
                        INSERT INTO sales_auction_payment_status_rel (sale_auction_id, payment_status_id)
                        SELECT id, payment_status_id
                        FROM sales_auction_management
                        WHERE payment_status_id IS NOT NULL
                        ON CONFLICT DO NOTHING;

                        ALTER TABLE sales_auction_management DROP CONSTRAINT IF EXISTS sales_auction_management_payment_status_id_fkey;
                        ALTER TABLE sales_auction_management DROP COLUMN IF EXISTS payment_status_id;
                    END IF;

                    -- 3. Migrate from legacy selection column payment_status
                    IF EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'sales_auction_management'
                          AND column_name = 'payment_status'
                    ) THEN
                        IF v_invoice_paid_id IS NOT NULL THEN
                            INSERT INTO sales_auction_payment_status_rel (sale_auction_id, payment_status_id)
                            SELECT id, v_invoice_paid_id
                            FROM sales_auction_management
                            WHERE payment_status = 'invoice_paid'
                            ON CONFLICT DO NOTHING;
                        END IF;

                        IF v_amount_paid_id IS NOT NULL THEN
                            INSERT INTO sales_auction_payment_status_rel (sale_auction_id, payment_status_id)
                            SELECT id, v_amount_paid_id
                            FROM sales_auction_management
                            WHERE payment_status = 'amount_paid'
                            ON CONFLICT DO NOTHING;
                        END IF;

                        IF v_not_paid_id IS NOT NULL THEN
                            INSERT INTO sales_auction_payment_status_rel (sale_auction_id, payment_status_id)
                            SELECT id, v_not_paid_id
                            FROM sales_auction_management
                            WHERE payment_status = 'not_paid'
                            ON CONFLICT DO NOTHING;
                        END IF;
                    END IF;

                    -- Clean up obsolete ir_model_fields entry if present
                    DELETE FROM ir_model_fields WHERE model = 'sales.auction.management' AND name = 'payment_status_id';
                END IF;
            END $$;
        """)
    
    @api.model_create_multi
    def create(self, vals_list):
        enf_type = self.env.ref('sales_and_auction_management.p2_type_auction_enf', raise_if_not_found=False)
        for vals in vals_list:
            if not vals.get('entrie_name') or vals.get('entrie_name') in (_('New'), 'New', 'جديد'):
                req_type_id = vals.get('request_type_id') or self.env.context.get('default_request_type_id')
                proj_path = vals.get('auction_project_path') or self.env.context.get('default_auction_project_path')
                proj_type = vals.get('project_type_selection')
                is_eanfaz = (
                    (enf_type and req_type_id == enf_type.id) or
                    proj_path == 'enforcement' or
                    proj_type == 'auction_enf'
                )
                if is_eanfaz:
                    vals['entrie_name'] = self.env['ir.sequence'].next_by_code('entries.auction.eanfaz') or _('New')
                else:
                    vals['entrie_name'] = self.env['ir.sequence'].next_by_code('bussma.entries.sequence') or _('New')
        records = super(SalesAuctionManagement, self).create(vals_list)
        for rec in records:
            if rec.stage_id:
                rec._notify_stage_authorized_users()
            if rec.project_id and not rec.project_id.is_basic:
                prop_name = rec.entrie_name or rec.name or f"Property #{rec.id}"
                rec.project_id.message_post(
                    body=_("Property (%s) was added to project properties.") % prop_name
                )
        return records

    def write(self, vals):
        if not self.env.context.get('bypass_contract_cancelled_check'):
            allowed_cancelled_keys = {
                'is_contract_cancelled', 'active', 'message_ids', 'activity_ids',
                'stage_id', 'project_id', 'transfer_status_display',
            }
            for rec in self:
                if rec.is_contract_cancelled and not set(vals.keys()).issubset(allowed_cancelled_keys):
                    raise exceptions.UserError(_("This contract is cancelled. You cannot modify fields on a cancelled contract."))
        # Store original stages and projects to detect changes
        original_stages = {rec.id: rec.stage_id.id for rec in self}
        old_projects = {rec.id: rec.project_id for rec in self}
        res = super(SalesAuctionManagement, self).write(vals)
        if 'stage_id' in vals:
            for rec in self:
                if rec.stage_id.id != original_stages.get(rec.id):
                    rec._notify_stage_authorized_users()

        if 'project_id' in vals or 'request_type_id' in vals or 'project_type_selection' in vals:
            from collections import defaultdict
            old_proj_props = defaultdict(list)
            new_proj_props = defaultdict(list)
            for rec in self:
                old_proj = old_projects.get(rec.id)
                new_proj = rec.project_id
                
                # Check if property left old_proj
                if old_proj and not old_proj.is_basic and (old_proj != new_proj or 'request_type_id' in vals or 'project_type_selection' in vals):
                    prop_name = rec.entrie_name or rec.name or f"Property #{rec.id}"
                    old_proj_props[old_proj].append(prop_name)
                    old_proj.sudo().write({'transferred_entry_ids': [(4, rec.id)]})

                    # Set transfer_status_display ONLY ONCE upon initial transfer
                    if not rec.transfer_status_display:
                        if new_proj and new_proj.is_basic:
                            status_note = _("Referred to Basic Portfolio")
                        elif new_proj and not new_proj.is_basic and new_proj != old_proj:
                            status_note = _("Assigned to project: %s") % new_proj.name
                        elif rec.project_type_selection == 'sales':
                            status_note = _("Converted to Sales Department")
                        elif rec.project_type_selection in ('auction_pvt', 'auction_enf', 'city'):
                            status_note = _("Converted to Auctions Department")
                        else:
                            status_note = _("Referred / Converted")
                        
                        rec.sudo().with_context(bypass_contract_cancelled_check=True).write({'transfer_status_display': status_note})

                # Check if property was assigned to new_proj
                if new_proj and not new_proj.is_basic:
                    prop_name = rec.entrie_name or rec.name or f"Property #{rec.id}"
                    if old_proj != new_proj:
                        new_proj_props[new_proj].append(prop_name)
                    if rec.id in new_proj.transferred_entry_ids.ids:
                        new_proj.sudo().write({'transferred_entry_ids': [(3, rec.id)]})

            for proj, names in old_proj_props.items():
                combined = ", ".join(filter(None, names))
                proj.message_post(
                    body=_("Property (%s) was removed from project properties.") % combined
                )

            for proj, names in new_proj_props.items():
                combined = ", ".join(filter(None, names))
                proj.message_post(
                    body=_("Property (%s) was added to project properties.") % combined
                )
        return res

    def _notify_stage_authorized_users(self):
        """ Identifies authorized users and creates activities for them. """
        self.ensure_one()
        if not self.stage_id:
            return
        # Always clear old activities when the stage changes, even if moving to archive
        self.create_mail_activity(users=False, is_done=True)
        # Exclude archive stages from creating new activities
        archive_stages = [
            self.env.ref('sales_and_auction_management.p2_stage_shared_archive', raise_if_not_found=False),
            self.env.ref('sales_and_auction_management.p2_stage_sales_archive', raise_if_not_found=False),
        ]
        if self.stage_id in [s for s in archive_stages if s]:
            return
        users = self.env['res.users']
        # 1. Direct user assignment
        if self.stage_id.assign_type == 'users' and self.stage_id.default_user_ids:
            users |= self.stage_id.default_user_ids
        # 2. Role-based assignment
        elif self.stage_id.assign_type == 'role' and self.stage_id.default_role_ids:
            role_lines = self.env['res.users.role.line'].sudo().search([
                ('role_id', 'in', self.stage_id.default_role_ids.ids)
            ])
            users |= role_lines.mapped('user_id')
        if users:
            summary = _("A new property has been assigned to your stage (%s), please review the data and take the necessary action.") % (
                self.stage_id.name
            )
            self.create_mail_activity(users, summary=summary, is_done=False)

            # Send email notification to managers when entering Portfolio stage
            portfolio_stages = [
                self.env.ref('sales_and_auction_management.p2_stage_sales_direct_mgmt', raise_if_not_found=False),
                self.env.ref('sales_and_auction_management.p2_stage_auction_pvt_portfolio', raise_if_not_found=False),
                self.env.ref('sales_and_auction_management.p2_stage_auction_city_portfolio', raise_if_not_found=False),
                self.env.ref('sales_and_auction_management.p2_auction_enf_portfolio', raise_if_not_found=False),
            ]
            portfolio_stages = [s for s in portfolio_stages if s]
            if self.stage_id in portfolio_stages:
                for user in users.filtered(lambda u: u.active and u.email):
                    self._send_sales_auction_email(
                        'sales_and_auction_management.email_template_sales_auction_portfolio_new_property',
                        user
                    )

    def _get_department_sender_name(self):
        self.ensure_one()
        is_sales = (
            self.project_type_selection == 'sales'
            or (self.entry_id and self.entry_id.committee_decision == 'direct_sale')
        )
        return _("Sales Department") if is_sales else _("Auctions Department")

    def create_mail_activity(self, users, summary='Request Approval', is_done=True):
        """ Create Odoo activities for the specified users """
        if is_done:
            # Mark previous activities for this record as done
            activities = self.env['mail.activity'].sudo().search([
                ('res_model', '=', self._name), 
                ('res_id', 'in', self.ids)
            ])
            activities.action_done()
        if users:
            # Use standard To Do activity type
            activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            model_id = self.env['ir.model']._get(self._name).id
            
            for user in users:
                self.env['mail.activity'].sudo().with_context(mail_activity_quick_update=True).create({
                    'summary': summary,
                    'activity_type_id': activity_type.id if activity_type else False,
                    'res_model_id': model_id,
                    'res_id': self.id,
                    'user_id': user.id,
                })

    def _send_sales_auction_email(self, template_xml_id, recipient_user):
        """ Helper: send a mail.template email to a res.users recipient.
        Silently skips if template or recipient e-mail is missing. """
        self.ensure_one()
        if not recipient_user or not recipient_user.email:
            _logger.warning(
                "[Sales and Auctions Management Email] Skipped — no recipient or email. Template: %s | Record: %s",
                template_xml_id, self.entrie_name
            )
            return
        template = self.env.ref(template_xml_id, raise_if_not_found=False)
        if not template:
            _logger.warning(
                "[Sale and Auction Email] Template not found: %s", template_xml_id
            )
            return
        sender_name = self._get_department_sender_name()
        base_email = self.env.user.email or self.env.company.email or ''
        email_from = f'"{sender_name}" <{base_email}>' if base_email else sender_name
        try:
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': recipient_user.email,
                    'email_from': email_from,
                    'model': False,
                    'res_id': False,
                },
            )
            _logger.info(
                "[Sale and Auction Email] Sent '%s' from '%s' to %s for record %s",
                template_xml_id, email_from, recipient_user.email, self.entrie_name
            )
        except Exception as e:
            _logger.error(
                "[Sale and Auction Email] Failed to send '%s': %s", template_xml_id, str(e)
            )

    def action_raise_marketing_request_wizard(self):
        self.ensure_one()
        return {
            'name': _('Raise a marketing request'),
            'type': 'ir.actions.act_window',
            'res_model': 'sales.auction.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_entry_id': self.id,
                'default_request_type': 'marketing',
            }
        }

    def action_raise_legal_request_wizard(self):
        self.ensure_one()
        return {
            'name': _('Raise a legal request'),
            'type': 'ir.actions.act_window',
            'res_model': 'sales.auction.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_entry_id': self.id,
                'default_request_type': 'legal',
            }
        }

    def _create_detailed_study_eanfaz(self):
        self.ensure_one()
        existing_study = self.env['entries'].search([('sale_auction_id', '=', self.id)], limit=1)
        if not existing_study:
            request_type = self.env.ref('sales_and_auction_management.detailed_study_eanfaz', raise_if_not_found=False)
            initial_stage = self.env.ref('sales_and_auction_management.stage_studies_supervisor_eanfaz', raise_if_not_found=False)
            if request_type and initial_stage:
                self.env['entries'].create({
                    'request_type_id': request_type.id,
                    'stage_id': initial_stage.id,
                    'sale_auction_id': self.id,
                    'entrie_name': self.entrie_name or '',
                    'company_id': self.company_id.id if self.company_id else False,
                    'entered_by_id': self.entered_by_id.id if self.entered_by_id else False,
                })
        if existing_study:
            existing_study.is_return_to_supervisor_study = False

    def _get_mail_thread_data_attachments(self):
        """ Exclude attachments belonging to explicit model fields from the Chatter attachment popover (📎 button). """
        res = super(SalesAuctionManagement, self)._get_mail_thread_data_attachments()
        if self:
            self.ensure_one()
            field_attachment_ids = set()
            for field_name in [
                'facility_photo_ids',
                'rent_contract_ids',
            ]:
                if hasattr(self, field_name):
                    attachments = getattr(self, field_name)
                    if attachments:
                        field_attachment_ids.update(attachments.ids)

            if field_attachment_ids:
                res = res.filtered(lambda a: a.id not in field_attachment_ids)
        return res

    def _get_extra_domain(self):
        search_domain = super(SalesAuctionManagement, self)._get_extra_domain()
        if len(self) == 1 and self.amount_matches_selling_price:
            search_domain = expression.AND([
                search_domain,
                [("hide_on_flag", "=", False)]
            ])
        return search_domain
