# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from odoo import api,fields,models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
_logger = logging.getLogger(__name__)

    
class Entries(models.Model):
    _name = 'entries'
    _inherit = 'request'
    _description = 'Entries'
    _rec_name = 'entrie_name'
    
    entrie_name = fields.Char(string='Entry Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
#======================================================
#           Listing Fields (Customer Data)
#======================================================
    # Customer Intent
    customer_intent = fields.Selection(
        [
            ('direct_sale', 'Direct Sale'),
            ('auction', 'Auction'),
            ('select_all', 'Select All'),
            ('studies_recommendation', 'Studies Recommendation')
        ],
        string='Customer Intent',
        tracking=True,
    )
    customer_intent_rel = fields.Many2one('customer.intent', string='Customer Intent', domain="[('code', 'in', ['direct_sale', 'auction', 'select_all', 'studies_recommendation'])]", tracking=True)
    # Customer Name
    partner_id = fields.Many2one('res.partner', string='Customer Name', tracking=True)
    customer_role_rel = fields.Many2one('customer.role', string='Customer Role', domain="[('code', 'in', ['owner', 'agent', 'broker', 'other'])]", tracking=True)
    owner_type = fields.Selection(
        [
            ('individual', 'Individual'),
            ('company', 'Company'),
            ('government', 'Government Agency'),
            ('investor', 'Investor')
        ],
        string='Owner Type',
        tracking=True,
    )
    # Customer Contact Number
    partner_mobile = fields.Char(
        string='Customer Mobile',
        compute='_compute_partner_mobile',
        store=True,
        readonly=False,
        precompute=True,
        tracking=True,
    )

    # Entered By (User)
    entered_by_id = fields.Many2one(
        'res.users',
        string='Entered By',
        default=lambda self: self.env.user,
        tracking=True,
    )
    # Entered By Email
    entered_by_email = fields.Char(
        string='Entered By Email',
        tracking=True
    )
    # Company
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, tracking=True)
    # Property Attachments
    property_attachment_ids = fields.Many2many(
        'ir.attachment',
        'entries_property_attachments_rel',
        'entry_id',
        'attachment_id',
        string='Property Attachments',
        tracking=True,
    )
    # Country (related for domain evaluation)
    country_id = fields.Many2one('res.country', related='company_id.country_id', store=True)
    # City (Using res.country.state as Cities)
    city = fields.Many2one(
        'res.country.state',
        string='City',
        domain="[('country_id.code', '=', 'SA'), ('code', 'ilike', 'CT_')]",
        tracking=True,
    )
    # District (Using res.city as Districts)
    district_id = fields.Many2one(
        'res.city',
        string='District',
        domain="[('state_id', '=', city)]",
        tracking=True,
    )
    property_type = fields.Many2one('property.type', string='Property Type', domain=lambda self: self._get_property_type_domain(), tracking=True)
    # Area (Square Meters)
    area_sqm = fields.Float(string='Area (m²)', tracking=True)
    property_usage_rel = fields.Many2one(
        'property.usage.type',
        string='Property Usage',
        domain="[('active', '=', True)]",
        tracking=True,
    )
    # Current Income Value
    current_income = fields.Float(
        string='Current Income',
        tracking=True,
    )
    # Currency
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        tracking=True,
    )
    # Plan Number
    plan_number = fields.Char(string='Plan Number', tracking=True)
    # Deed Number
    deed_number = fields.Char(string='Deed Number', tracking=True)
    # Deed Date
    deed_date = fields.Date(string='Deed Date', tracking=True)
    # Plot Number
    plot_number = fields.Char(string='Plot Number', tracking=True)
    # Listing Date
    listing_date = fields.Date(
        string='Listing Date',
        default=fields.Date.context_today,
        required=False,
        tracking=True
    )
    # Customer Price per Square Meter
    customer_price_per_sqm = fields.Float(
        string='Customer Price per Square Meter',
        tracking=True,
    )
    # Customer Total Price (area_sqm * customer_price_per_sqm)
    customer_total_price = fields.Float(
        string='Customer Total Price',
        compute='_compute_customer_total_price',
        store=True,
        tracking=True,
    )
    # Location URL (Map Link)
    location_url = fields.Char(string='Location', tracking=True)
    # Requires Technical Offer?
    requires_technical_offer = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Requires Technical Offer', tracking=True)
    is_modon_auction = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Is Modon Auction', tracking=True)
    # Notes
    entered_notes = fields.Text(string='Notes', tracking=True)
    # Does this property have an income?
    has_income = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Is there an income?', tracking=True)
##########################################################################################
#                Project Path Determination Fields
##########################################################################################
    # Is Property Authorized (Yes / No / Return to Lister / Data Completion)
    is_authorized_property = fields.Selection(
        [
            ('yes', 'Yes'),
            ('no', 'No'),
            ('return_to_lister', 'Return to Lister'),
            ('data_completion', 'Data Completion'),
        ],
        tracking=True,
        string='Is Authorized Property'
    )
    # Rejection Reason
    rejection_reason = fields.Text(string='Rejection Reason')
    # Return to Lister Note
    return_to_lister_note = fields.Text(string='Return to Lister Note')
    # Data Completion
    data_completer_id = fields.Many2one('res.users', string='Data Completer', tracking=True)
    data_completion_note = fields.Text(string='Data Completion Note')
    # Project Path (Cities / Specialized / Standard)
    project_path = fields.Selection([('cities', 'Cities'), ('specialized', 'Specialized'), ('standard', 'Standard')], tracking=True, string='Project Path')
    project_path_rel = fields.Many2one('project.path', string='Project Path', domain="[('code', 'in', ['cities', 'specialized', 'standard'])]")
    # Assigned Analyst (User)
    analyst_id = fields.Many2one('res.users', tracking=True, string='Assigned Analyst')
    detailed_analyst_id = fields.Many2one('res.users', tracking=True, string='Detailed Assigned Analyst')
    city_analyst_id = fields.Many2one('res.users', tracking=True, string='City Assigned Analyst')
##########################################################################################
#          Preliminary Study Fields
##########################################################################################
    # Verified Income Amount
    verified_income = fields.Float(string='Verified Income', currency_field='currency_id')
    # Expected Income (Full Lease)
    expected_full_lease_income = fields.Float(string='Expected Income (Full Lease)', currency_field='currency_id')
    # Building Requirements
    building_requirements = fields.Text(string='Building Requirements')
    # Ministry of Justice Index Average
    justice_index_average = fields.Float(string='Ministry of Justice Index Average', currency_field='currency_id')
    # Comparables Average
    comparison_average = fields.Float(string='Comparables Average', currency_field='currency_id')
    # Price Per Meter
    price_per_meter = fields.Float(string='Price Per Meter', currency_field='currency_id')
    # Final Property Price
    final_property_price = fields.Float(string='Final Property Price', currency_field='currency_id')
    # Analyst Recommendation Preliminary
    analyst_recommendation_preliminary = fields.Text(string='Analyst Recommendation Preliminary')
    # Number of Properties
    properties_count = fields.Integer(string='Number of Properties', default=1)
    # Preliminary Study Completion / Rejection
    preliminary_study_status = fields.Selection([('completed', 'Completed'), ('rejected', 'Rejected')], string='Preliminary Study Result')
    # Analyst Rejection Notes
    analyst_rejection_notes = fields.Text(string='Analyst Rejection Notes')
    property_usage_standard = fields.Char(string="Property Usage")
#############################################################################################################
#                Detailed Study Fields
#############################################################################################################
    # Analyst Recommendation (Details)
    analyst_recommendation_details = fields.Text(string='Analyst Recommendation Details')
    # Building Requirements (Detailed)
    detailed_building_requirements = fields.Text(string='Building Requirements')
    detailed_price_per_meter = fields.Float(string='Detailed Price Per Meter', currency_field='currency_id')
    # Final Property Price (Detailed)
    detailed_final_property_price = fields.Float(string='Final Property Price', currency_field='currency_id')
    # Comparables Average (Detailed)
    detailed_comparison_average = fields.Float(string='Comparables Average', currency_field='currency_id')
    # Boundary (East)
    limit_east = fields.Char(string="Limit (East)")
    # Finishing Ratio
    finishing_ratio = fields.Float(string="Finishing Ratio")
    # Number of Electricity Meters
    electricity_meters_count = fields.Integer(string="Number of Electricity Meters")
    # Sewage Service Availability
    sewage_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Sewage Service")
    # Internal Strength Points
    internal_strength_points = fields.Text(string="Internal Strength Points")
    # Current Total Income
    current_total_income = fields.Float(string="Current Total Income")
    # Precise Plot Location Link
    precise_plot_location_link = fields.Char(string="Precise Plot Location Link")
    # Length (East)
    length_east = fields.Float(string="Length (East)")
    # Boundary (North)
    limit_north = fields.Char(string="Limit (North)")
    # Number of Floors
    floors_count = fields.Integer(string="Number of Floors")
    # Electricity Meter Numbers
    electricity_meters_numbers = fields.Char(string="Electricity Meters Numbers")
    # Water Service Availability
    water_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Water Service")
    # Street
    street = fields.Char(string="Street")
    # Street Length
    street_length = fields.Float(string="Street Length")
    # Best Use of Property
    best_property_use = fields.Text(string="Best Use of Property")
    # Ministry of Justice Index Average
    justice_ministry_index_average = fields.Float(string="Average Justice Ministry Index")
    # Boundary (West)
    limit_west = fields.Char(string="Limit (West)")
    # Length (North)
    length_north = fields.Float(string="Length (North)")
    # Number of Units
    units_count = fields.Integer(string="Number of Units")
    # Building License Date
    building_license_date = fields.Date(string="Building License Date")
    # Electricity Service Availability
    electricity_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Electricity Service")
    # Nearest Main Road
    nearest_main_road = fields.Char(string="Nearest Main Road")
    # External Weakness Points
    external_weakness_points = fields.Text(string="External Weakness Points")
    # Expected Total Income (Full Rent)
    expected_total_income_full_rent = fields.Float(string="Expected Total Income (Full Rent)")
    # Property Description
    property_description = fields.Text(string="Property Description")
    # Length (West)
    length_west = fields.Float(string="Length (West)")
    # Boundary (South)
    limit_south = fields.Char(string="Limit (South)")
    # Property Age (Estimated if No License Exists)
    property_age_estimated = fields.Char(string="Property Age (Estimated if no License)")
    # Building License Number
    building_license_number = fields.Char(string="Building License Number")
    # Number of Water Meters
    water_meters_count = fields.Integer(string="Number of Water Meters")
    # Pavement Service Availability
    pavement_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Pavement Service")
    # External Strength Points
    external_strength_points = fields.Text(string="External Strength Points")
    # Lowest Price per Meter (Entire Property)
    lowest_price_per_meter_total_property = fields.Float(string="Lowest Price per Meter (Total Property)")
    # Approximate Building Value per Meter
    approximate_building_value_per_meter = fields.Float(string="Approximate Building Value per Meter")
    # Building Area
    building_area = fields.Float(string="Building Area")
    # Length (South)
    length_south = fields.Float(string="Length (South)")
    # Land Nature (If Raw Land)
    land_nature = fields.Char(string="Land Nature (If Raw Land)")
    # Completion Certificate Issued?
    completion_certificate_issued = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Completion Certificate Issued?")
    # Water Meter Numbers
    water_meters_numbers = fields.Char(string="Water Meters Numbers")
    # Lighting Service Availability
    lighting_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Lighting Service")
    # Gas Service Availability
    gas_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Gas Service")
    # AC Service Availability
    ac_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="AC Service")
    # Internet Service Availability
    internet_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Internet Service")
    # Telecom Service Availability
    telecom_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Telecom Service")
    # Security Guard Service Availability
    security_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Security Guard Service")
    # Elevator Service Availability
    elevator_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Elevator Service")
    # Pool Service Availability
    pool_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Pool Service")
    # Garden Service Availability
    garden_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Garden Service")
    # Parking Service Availability
    parking_service = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Parking Service")
    # Construction Warranty
    construction_warranty = fields.Char(string="Construction Warranty")
    # Electrical Warranty
    electrical_warranty = fields.Char(string="Electrical Warranty")
    # Plumbing Warranty
    plumbing_warranty = fields.Char(string="Plumbing Warranty")
    # Services Description
    services_description = fields.Char(string="Services Description")

    # Internal Weakness Points
    internal_weakness_points = fields.Text(string="Internal Weakness Points")
    # Highest Price per Meter (Entire Property)
    highest_price_per_meter_total_property = fields.Float(string="Highest Price per Meter (Total Property)")
    # Approximate Land Value per Meter
    approximate_land_value_per_meter = fields.Float(string="Approximate Land Value per Meter")
    property_usage_detailed = fields.Char(string="Property Usage")
    detailed_analyst_notes = fields.Text(string="Analyst Notes")

############################################################################################################
#                    Cities Study Fields
############################################################################################################
    # GPS Coordinates
    gps_coordinates = fields.Char(string="GPS Coordinates")
    # Area
    area = fields.Float(string="Area")
    # Industrial City
    industrial_city = fields.Char(string="Industrial City")
    # Allocation Fees
    allocation_fees = fields.Float(string="Allocation Fees", currency_field="currency_id")
    # Annual Financial Fee
    annual_financial_fee = fields.Float(string="Annual Financial Fee", currency_field="currency_id")
    # Previous Facility Activity
    previous_activity = fields.Char(string="Previous Facility Activity")
    # Facility Investor
    facility_investor = fields.Char(string="Facility Investor")
    # Investor Contact Number
    investor_contact_number = fields.Char(string="Investor Contact Number")
    # Are There Any Movables?
    has_movables = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Is there any movables?", default='no')
    # Equipment
    equipment = fields.Text(string="Equipment")
    # Vehicles
    vehicles = fields.Text(string="Vehicles")
    # Machinery
    machinery = fields.Text(string="Machinery")
    # Systems
    systems = fields.Text(string="Systems")
    # Analyst Notes
    analyst_notes = fields.Text(string="Analyst Notes")

    # ==========================================================
    #            City Study Analyst Fields (Documents)
    # ==========================================================
    facility_photo_ids = fields.Many2many('ir.attachment', 'facility_photos_rel', 'entry_id', 'attachment_id', string="Facility Photos")
    coordinates_kmz = fields.Binary(string="Coordinates File (KMZ)", attachment=True)
    coordinates_kmz_name = fields.Char(string="Coordinates File Name")
    current_income_file = fields.Binary(string="Current Income File", attachment=True)
    current_income_file_name = fields.Char(string="Current Income File Name")
    rent_contract_ids = fields.Many2many('ir.attachment', 'rent_contracts_rel', 'entry_id', 'attachment_id', string="Rent Contracts")
#############################################################################################################
#   Study Manager Approval Fields (All Studies & Paths)
#############################################################################################################
    # Preliminary Study Manager Approval
    standard_study_manager_approval = fields.Selection(
        [
            ('completed', 'Completed'),
            ('incomplete', 'Incomplete'),
            ('reject_and_archive', 'Reject and Archive'),
        ],
        string='Study Manager Approval', tracking=True
    )
    standard_study_manager_approval_rel = fields.Many2one(
        'standard.study.manager.approval',
        string="Study Manager Approval",
        domain="[('code', 'in', ['completed', 'incomplete', 'reject_and_archive'])]",
    )
    # Preliminary Study Manager Notes
    standard_study_manager_note = fields.Text(
        string='Study Manager Note',
        tracking=True
    )
    # Detailed Study Manager Approval
    specialized_study_manager_approval = fields.Selection(
        [
            ('completed', 'Completed'),
            ('incomplete', 'Incomplete'),
        ],
        string='Study Manager Approval', tracking=True
    )
    # Detailed Study Manager Notes
    specialized_study_manager_note = fields.Text(
        string='Study Manager Note'
    )
    # Cities Study Manager Approval
    cities_study_manager_approval = fields.Selection(
        [
            ('completed', 'Completed'),
            ('incomplete', 'Incomplete'),
        ],
        string='Study Manager Approval', tracking=True
    )
    # Cities Study Manager Notes
    cities_study_manager_note = fields.Text(
        string='Study Manager Note'
    )
##############################################################################################################
#          Committee Decision Fields (Direct Sale & Auction)
##############################################################################################################
    # Committee Decision (Direct Sale / Auction / Exclusion)
    committee_decision = fields.Selection([('direct_sale', 'Direct Sale'), ('auction', 'Auction'), ('exclusion', 'Exclusion')], string="Committee Decision", tracking=True)
    committee_decision_rel = fields.Many2one('committee.decision.type', string="Committee Decision", domain="[('code', 'in', ['direct_sale', 'auction', 'exclusion'])]")
    # Committee Decision Date
    committee_decision_date = fields.Date(string="Committee Decision Date")
    # Marketing Duration (Months)
    marketing_duration_months = fields.Integer(string="Marketing Duration (Months)")
    # Direct Sale Price per Square Meter
    direct_sale_price_per_meter = fields.Float(string="Direct Sale Price per Square Meter")
    # Auction Price per Square Meter
    auction_price_per_meter = fields.Float(string="Auction Price per Square Meter")
    # Total Direct Sale Price
    direct_sale_total_price = fields.Float(string="Total Direct Sale Price")
    # Total Auction Sale Price
    auction_total_price = fields.Float(string="Total Auction Sale Price")
    # Committee Notes
    committe_notes = fields.Text(string="Notes")
    # Committee Decisions (User Lists)
    committee_approved_users = fields.Many2many('res.users', 'committee_approved_users_rel', 'entry_id', 'user_id', string="Approved")
    committee_rejected_users = fields.Many2many('res.users', 'committee_rejected_users_rel', 'entry_id', 'user_id', string="Rejected" )
    committee_postponed_users = fields.Many2many('res.users', 'committee_postponed_users_rel', 'entry_id', 'user_id', string="Postponed")
#######################################################################################################################
#        Sales Manager & Auctions Manager Approval Fields
#######################################################################################################################
# Sales Manager Approval
    sales_manager_approval = fields.Selection(
        [
            ('committee_decision_accepted', 'Accept Committee Decision'),
            ('committee_decision_rejected', 'Reject Committee Decision'),
            ('request_transfer_direct_sale', 'Request Property Transfer to Direct Sale'),
        ],
        string="Sales Manager Decision", tracking=True
    )
    # Sales Manager Notes
    sales_manager_notes = fields.Text(string="Sales Manager Notes")
    sales_manager_approval_rel = fields.Many2one('sales.manager.approval', string="Sales Manager Decision", domain="[('code', 'in', ['committee_decision_accepted', 'committee_decision_rejected', 'request_transfer_direct_sale'])]")
    # Auctions Manager Approval
    auctions_manager_approval = fields.Selection(
        [
            ('committee_decision_accepted', 'Accept Committee Decision'),
            ('committee_decision_rejected', 'Reject Committee Decision'),
            ('request_transfer_auction', 'Request Property Transfer to Auction'),
        ],
        string="Auctions Manager Decision", tracking=True
    )
    auctions_manager_approval_rel = fields.Many2one('auction.manager.approval', string="Auctions Manager Decision", domain="[('code', 'in', ['committee_decision_accepted', 'committee_decision_rejected', 'request_transfer_auction'])]")
    # Auctions Manager Notes
    auctions_manager_notes = fields.Text(string="Auctions Manager Notes")
######################################################################################################################
#     Commercial Sector Manager Approval — Committee Decision
######################################################################################################################
    # Commercial Sector Manager Approval on Committee Decision
    commercial_sector_manager_approval = fields.Selection([
        ('approval', 'Approval'),
        ('return_committee', 'Return to commit'),
        ('transfer', 'Transfer to Partners'),
        ('declined', 'Declined'),
        ('postponed', 'Postponed'),
    ], string="Commercial Sector Manager Approval", tracking=True)
    commercial_sector_manager_approval_rel = fields.Many2one(
        'commercial.sector.manager.approval',
        string="Commercial Sector Manager Decision",
        domain="[('code', 'in', ['approval', 'return_committee', 'transfer', 'declined', 'postponed'])]"
    )
    # Reason for Rejection or Transfer
    commercial_sector_manager_reason = fields.Text(string="Reason for Rejection or Transfer")
    # Commercial Sector Manager Notes
    commercial_sector_manager_notes = fields.Text(string="Commercial Sector Manager Notes")
####################################################################################################################
#                Negotiation Fields
####################################################################################################################
    # Assign Negotiator
    assigned_negotiator = fields.Many2one(
        'res.users',
        string="Assign Negotiator",
        compute='_compute_assigned_negotiator',
        store=True,
        readonly=False,
        precompute=True,
        tracking=True
    )
    # Assign Project Manager
    assigned_project_manager = fields.Many2one('res.users', string="Project Manager", tracking=True)
###################  Negotiation #######################
# First: Negotiation by Listing Owner
    # Final Owner Decision
    final_owner_decision = fields.Selection([('committee_price', 'Approved at Committee Price'), ('higher_price', 'Approved at Another Price'), ('rejected', 'Rejected')], string="Final Owner Decision")
    final_owner_decision_rel = fields.Many2one('final.owner.decision', string="Final Owner Decision", domain="[('code', 'in', ['committee_price', 'higher_price', 'rejected'])]")
    # Final Owner Price
    final_owner_price_per_meter = fields.Float(string="Final Owner Price Per Meter", currency_field='currency_id')
    final_owner_price = fields.Float(string="Final Owner Price")
    final_owner_price_diff_percentage = fields.Float(
        string="Price Difference Percentage",
        compute="_compute_negotiation_price_diff_percentages",
        store=True
    )
    # Owner Rejection Reasons
    owner_rejection_reasons = fields.Text(string="Owner Rejection Reasons")
    negotiator_note = fields.Text(string="Negotiator Note")

# Second: Negotiation by Department Manager
    # Is Manager the Negotiator?
    is_manager_negotiator =  fields.Boolean(string="Is Manager Negotiator", default=False)
    # Final Owner Decision (Manager Negotiation)
    manager_negotiator_final_owner_decision = fields.Selection([('committee_price', 'Approved at Committee Price'), ('higher_price', 'Approved at Another Price'), ('rejected', 'Rejected')], string="Final Owner Decision")
    # Final Owner Price
    manager_negotiator_final_owner_price_per_meter = fields.Float(string="Final Owner Price Per Meter", currency_field='currency_id')
    manager_negotiator_final_owner_price = fields.Float(string="Final Owner Price")
    manager_negotiator_price_diff_percentage = fields.Float(
        string="Price Difference Percentage",
        compute="_compute_negotiation_price_diff_percentages",
        store=True
    )
    # Owner Rejection Reasons
    manager_negotiator_owner_rejection_reasons = fields.Text(string="Owner Rejection Reasons")
    manager_negotiator_note = fields.Text(string="Manager Negotiator Note")

#################### Negotiation Approval #################
    # Deputy Studies Manager Approval sub-step
    is_sent_to_deputy_studies_manager = fields.Boolean(
        string="Sent to Deputy Studies Manager", default=False, tracking=True
    )
    deputy_studies_manager_approval = fields.Selection(
        [
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected'),
        ],
        string="Deputy Studies Manager Approval", tracking=True
    )
    deputy_studies_manager_notes = fields.Text(string="Deputy Studies Manager Notes")
    # Commercial Sector Manager Contract Approval
    commercial_sector_manager_contract_approval = fields.Selection(
        [
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected'),
            ('transfer', 'Transfer to Partners'),
        ],
        string="Commercial Sector Manager Contract Approval", tracking=True
    )
    # Contract Approval Notes
    commercial_sector_manager_contract_notes = fields.Text(string="Commercial Sector Manager Notes for Client Contract")
    # Contracting Stage Fields
    contract_client_name = fields.Char(string="Client Name", compute='_compute_client_details', store=True, readonly=False)
    contract_client_identity = fields.Char(string="Client Identity")
    contract_client_birthdate = fields.Date(string="Client Birth Date")
    contract_client_mobile = fields.Char(string="Client Mobile Number", compute='_compute_client_details', store=True, readonly=False)
    contract_client_role = fields.Selection([('owner', 'Owner'), ('agent', 'Agent')], string="His Role")
    contract_owner_name = fields.Char(string="Owner Name")
    contract_owner_identity = fields.Char(string="Owner Identity")
    contract_owner_birthdate = fields.Date(string="Owner Birth Date")
    contract_owner_mobile = fields.Char(string="Owner Mobile Number")
    contract_agency_deed_attachment = fields.Binary(string="Power of Attorney Attachment", attachment=True)
    contract_agency_deed_attachment_name = fields.Char(string="Attachment Name")
    contract_agreed_price = fields.Float(string="Agreed Price", compute='_compute_contract_agreed_price', store=True, readonly=False)
    contract_duration = fields.Char(string="Contract Duration")
    contract_notes = fields.Text(string="Contract Notes")
    rooms_count = fields.Integer(string="Number of Rooms")
    property_facade = fields.Char(string="Property Facade")
    is_land_property_type = fields.Boolean(compute='_compute_is_land_property_type', string="Is Land Property Type")
####################################################################################################################
#      Contract Follow-up — Sales Department
####################################################################################################################
    # Assigned Contract Manager
    direct_sale_assigned_contract_manager = fields.Many2one('res.users', string="Assigned Contract Manager", tracking=True)
    # Contract Status
    direct_sale_contract_status = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Contract Status", tracking=True)
    # Reasons for Not Contracting
    direct_sale_contract_non_compliance_reasons = fields.Text(string="Reasons for Not Contracting", tracking=True)
    # Contract Attachments (Direct Sale)
    direct_sale_contract_attachments = fields.Many2many(
        'ir.attachment',
        'direct_sale_contract_attachments_rel',
        'entry_id',
        'attachment_id',
        string="Contract Documents",
    )
####################################################################################################################
#      Contract Follow-up — Auctions Department
####################################################################################################################
    # Assigned Contract Manager
    auction_assigned_contract_manager = fields.Many2one('res.users', string="Assigned Contract Manager", tracking=True)
    # Contract Status
    auction_contract_status = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Contract Status", tracking=True)
    # Reasons for Not Contracting
    auction_contract_non_compliance_reasons = fields.Text(string="Reasons for Not Contracting", tracking=True)
    # Contract Attachments (Auction)
    auction_contract_attachments = fields.Many2many(
        'ir.attachment',
        'auction_contract_attachments_rel',
        'entry_id',
        'attachment_id',
        string="Contract Documents",
    )
    # Negotiation Approval Fields
    negotiation_commercial_manager_approval = fields.Selection([
        ('approval', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Commercial Sector Manager Negotiation Approval", tracking=True)
    negotiation_studies_manager_approval = fields.Selection([
        ('approval', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Studies Manager Negotiation Approval", tracking=True)
    negotiation_approval_notes = fields.Text(string="Negotiation Approval Notes", tracking=True)
####################################################################################################################
#                Procedures Fields
####################################################################################################################
    project_stage_selection = fields.Selection(related='stage_id.project_stage_selection', string='Project Stage Selection', store=True)
    is_entry_archive = fields.Boolean(string="Archived Entry", default=False, tracking=True)
    is_deferred_opportunities_archive = fields.Boolean(string="Deferred Opportunities Archive", default=False, tracking=True)
    is_listing_archive_2023 = fields.Boolean(string="Archived Listings 2023", default=False, tracking=True)
    is_technical_offers_archive = fields.Boolean(string="Archived Technical Offers", default=False, tracking=True)
    is_partners_screen = fields.Boolean(string="Partners Screen", default=False, tracking=True)
    is_assign_detailed_study = fields.Boolean(string="Assign Detailed Study", default=False, tracking=True)
    has_data_completion = fields.Boolean(
        string="Has Data Completion",
        compute='_compute_has_data_completion',
        store=True,
        readonly=False,
    )
    is_send_email_to_detailed_study = fields.Boolean(string="Send Email to Detailed Study", default=False)
    is_returned_from_commercial_manager = fields.Boolean(string="Is Returned from Commercial Sector Manager", default=False, tracking=True)
    is_from_deferred_archive_menu = fields.Boolean(compute='_compute_is_from_deferred_archive_menu')
    is_from_smart_sheet = fields.Boolean(string="From Smart Sheet", default=False)
    # Stage History & Durations
    stage_history_ids = fields.One2many(
        'entries.stage.history',
        'entry_id',
        string='Stage History'
    )
    stage_history_filter_stage_id = fields.Many2one(
        'request.stage',
        string='Filter Stage History by Stage',
        domain="[('res_model', '=', 'entries'), ('project_stage_selection', 'not in', ['completed', 'city_study_completed'])]",
        store=False,
        help='Select a stage to filter the stage history log below'
    )
    stage_history_filtered_ids = fields.Many2many(
        'entries.stage.history',
        compute='_compute_stage_history_filtered_ids',
        string='Stage History (Filtered)'
    )
    current_stage_duration_days = fields.Float(
        string='Current Stage Duration (Days)',
        compute='_compute_stage_durations',
        help='Cumulative days spent in the current stage'
    )
    total_stage_duration_days = fields.Float(
        string='Total Duration Across All Stages (Days)',
        compute='_compute_stage_durations',
        help='Total days spent across all stages'
    )
    # Dedicated Stage Duration Fields (in Days)
    duration_entry_screen_days = fields.Float(string='Entry Screen Duration (Days)', compute='_compute_stage_durations')
    duration_data_completion_days = fields.Float(string='Data Completion Duration (Days)', compute='_compute_stage_durations')
    duration_define_path_days = fields.Float(string='Define Path Duration (Days)', compute='_compute_stage_durations')
    duration_preliminary_analyst_days = fields.Float(string='Preliminary Study Analyst Duration (Days)', compute='_compute_stage_durations')
    duration_detailed_analyst_days = fields.Float(string='Detailed Study Analyst Duration (Days)', compute='_compute_stage_durations')
    duration_preliminary_study_approval_days = fields.Float(string='Preliminary Study Approval Duration (Days)', compute='_compute_stage_durations')
    duration_detailed_study_approval_days = fields.Float(string='Detailed Study Approval Duration (Days)', compute='_compute_stage_durations')
    duration_study_approval_days = fields.Float(string='Study Approval Duration (Days)', compute='_compute_stage_durations')
    duration_committee_decision_days = fields.Float(string='Committee Decision Duration (Days)', compute='_compute_stage_durations')
    duration_sales_manager_decision_days = fields.Float(string='Sales Manager Decision Duration (Days)', compute='_compute_stage_durations')
    duration_auctions_manager_decision_days = fields.Float(string='Auctions Manager Decision Duration (Days)', compute='_compute_stage_durations')
    duration_sale_manager_decision_days = fields.Float(string='Department Manager Decision Duration (Days)', compute='_compute_stage_durations')
    duration_commercial_approval_days = fields.Float(string='Commercial Manager Approval Duration (Days)', compute='_compute_stage_durations')
    duration_assign_negotiator_days = fields.Float(string='Assign Negotiator Duration (Days)', compute='_compute_stage_durations')
    duration_negotiator_days = fields.Float(string='Negotiator Duration (Days)', compute='_compute_stage_durations')
    duration_manager_contract_approval_days = fields.Float(string='Manager Contract Approval Duration (Days)', compute='_compute_stage_durations')
    duration_contract_followup_days = fields.Float(string='Contract Followup Duration (Days)', compute='_compute_stage_durations')
    duration_negotiation_approval_days = fields.Float(string='Negotiation Approval Duration (Days)', compute='_compute_stage_durations')
    duration_contract_completion_days = fields.Float(string='Contract Completion Duration (Days)', compute='_compute_stage_durations')
    duration_city_study_analyst_days = fields.Float(string='City Study Analyst Duration (Days)', compute='_compute_stage_durations')
    duration_city_study_approval_days = fields.Float(string='City Study Approval Duration (Days)', compute='_compute_stage_durations')
    # Return Logs
    return_log_ids = fields.One2many('entries.return.log', 'entry_id', string='Return Logs')
    study_return_count = fields.Integer(compute='_compute_return_counts', string='Preliminary Study Returns')
    detailed_study_return_count = fields.Integer(compute='_compute_return_counts', string='Detailed Study Returns')
    committee_return_count = fields.Integer(compute='_compute_return_counts', string='Committee Returns')
    return_to_lister_count = fields.Integer(compute='_compute_return_counts', string='Return to Lister')
    department_return_count = fields.Integer(compute='_compute_return_counts', string='Department Returns')
    negotiator_return_count = fields.Integer(compute='_compute_return_counts', string='Negotiator Returns')
    data_completer_return_count = fields.Integer(compute='_compute_return_counts', string='Data Completer Returns')
    # User Role Groups
    is_studies_manager_group = fields.Boolean(compute='_compute_user_role_groups')
    is_analyst_group = fields.Boolean(compute='_compute_user_role_groups')
    is_sales_manager_group = fields.Boolean(compute='_compute_user_role_groups')
    is_assign_negotiator_group = fields.Boolean(compute='_compute_user_role_groups')
    is_auctions_manager_group = fields.Boolean(compute='_compute_user_role_groups')
    is_commercial_manager_group = fields.Boolean(compute='_compute_user_role_groups')
    is_negotiator_group = fields.Boolean(compute='_compute_user_role_groups')
    is_contract_manager_group = fields.Boolean(compute='_compute_user_role_groups')
    is_deputy_studies_manager_group = fields.Boolean(compute='_compute_user_role_groups')
    is_rnd_manager_group = fields.Boolean(compute='_compute_user_role_groups')
    is_committee_member_group = fields.Boolean(compute='_compute_user_role_groups')
    is_city_studies_manager_group = fields.Boolean(compute='_compute_user_role_groups')
    is_assigned_analyst = fields.Boolean(compute='_compute_assigned_users_permissions')
    is_assigned_detailed_analyst = fields.Boolean(compute='_compute_assigned_users_permissions')
    is_assigned_negotiator = fields.Boolean(compute='_compute_assigned_users_permissions')
    is_assigned_project_manager = fields.Boolean(compute='_compute_assigned_users_permissions')
    is_assigned_data_completer = fields.Boolean(compute='_compute_assigned_users_permissions')
    is_assigned_direct_sale_contract_manager = fields.Boolean(compute='_compute_assigned_users_permissions')
    is_assigned_auction_contract_manager = fields.Boolean(compute='_compute_assigned_users_permissions')

    # exported fields 
    sheet_date = fields.Datetime(string='Entrie Date')
    row_id = fields.Char(string='Row ID')
    row_number = fields.Char(string='Row Number')
    sheet_name = fields.Char(string='Sheet Name')
    deferred_opportunity_date = fields.Datetime(string='Deferred Opportunity Date')
    partner_name = fields.Char(string="Partner Name")
    partner_phone = fields.Char(string="Partner Phone")
    partner_decision = fields.Selection([('approved', 'Approved'),('rejected', 'Rejected'),('pending', 'Pending')],string="Partner Decision")
    partner_percentage_approval = fields.Char(string="Partner Percentage Approval")
    transfer_to_year = fields.Char(string="Transfer to Year")
    partner_page_date = fields.Datetime(string="Date Partners Page")
    commercial_sector_advisor_decision = fields.Char(string="Commercial Sector Advisor Decision")
    property_stage = fields.Selection([('transferred_to_zayed_platform', 'Transferred to Zayed Platform'),('transferred_to_commercial_sector_advisor', 'Transferred to Commercial Sector Advisor'),('transfer_to_sales_manager', 'Transfer to Sales Manager')],string="Property Stage",tracking=True)
    # old data fields (keep as is because used in data import) 
    old_data_deed_date = fields.Char(string="Deed Date")
    old_data_verified_analyst_income_amount = fields.Char(string="Amount of Income Verified by Analyst")
    old_data_owner_attached_rental_amount = fields.Char(string="Amount of Rent (Attached by Owner)")
    old_data_rental_amount = fields.Char(string="Amount of Rent")
    old_data_income_amount = fields.Char(string="Amount of Income")

    @api.depends('area_sqm', 'customer_price_per_sqm')
    def _compute_customer_total_price(self):
        for record in self:
            record.customer_total_price = (record.area_sqm or 0.0) * (record.customer_price_per_sqm or 0.0)

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields=allfields, attributes=attributes)
        if res and 'active' in res:
            res['active']['readonly'] = True
            res['active']['invisible'] = True
        return res
    
    @api.constrains('committee_approved_users', 'committee_rejected_users', 'committee_postponed_users')
    def _check_committee_users_uniqueness(self):
        for rec in self:
            approved = set(rec.committee_approved_users.ids)
            rejected = set(rec.committee_rejected_users.ids)
            postponed = set(rec.committee_postponed_users.ids)
            overlap = (approved & rejected) | (approved & postponed) | (rejected & postponed)
            if overlap:
                user_names = self.env['res.users'].browse(list(overlap)).mapped('name')
                raise ValidationError(_(
                    "A user can only belong to one committee decision list. Duplicated user(s): %s"
                ) % ", ".join(user_names))

    def _get_property_type_domain(self):
        return [('active', '=', True)]

    @api.depends('property_type', 'property_type.is_land')
    def _compute_is_land_property_type(self):
        for rec in self:
            rec.is_land_property_type = bool(rec.property_type and rec.property_type.is_land)

    @api.depends('partner_id')
    def _compute_client_details(self):
        for rec in self:
            if rec.partner_id:
                rec.contract_client_name = rec.partner_id.name
                rec.contract_client_mobile = rec.partner_id.phone or rec.partner_id.mobile
            else:
                rec.contract_client_name = False
                rec.contract_client_mobile = False

    @api.depends('final_owner_price', 'manager_negotiator_final_owner_price', 'is_manager_negotiator')
    def _compute_contract_agreed_price(self):
        for rec in self:
            if rec.is_manager_negotiator:
                rec.contract_agreed_price = rec.manager_negotiator_final_owner_price
            else:
                rec.contract_agreed_price = rec.final_owner_price

    def _compute_user_role_groups(self):
        is_studies_manager = self.env.user.has_group('bussma_system.group_studies_manager')
        is_deputy_studies_manager = self.env.user.has_group('bussma_system.group_deputy_studies_manager')
        is_rnd_manager = self.env.user.has_group('bussma_system.group_rnd_manager')
        is_analyst = self.env.user.has_group('bussma_system.group_analyst')
        is_sales = self.env.user.has_group('bussma_system.group_sales_manager')
        is_assign_negotiator = self.env.user.has_group('bussma_system.group_assign_negotiator')
        is_auctions = self.env.user.has_group('bussma_system.group_auctions_manager')
        is_commercial = self.env.user.has_group('bussma_system.group_commercial_sector_manager')
        is_negotiator = self.env.user.has_group('bussma_system.group_negotiator')
        is_contract_manager = self.env.user.has_group('bussma_system.group_contract_manager')
        is_committee_member = self.env.user.has_group('bussma_system.group_committee_member')
        is_city_studies_manager = self.env.user.has_group('bussma_system.group_city_studies_manager')

        for rec in self:
            rec.is_studies_manager_group = is_studies_manager
            rec.is_deputy_studies_manager_group = is_deputy_studies_manager
            rec.is_rnd_manager_group = is_rnd_manager
            rec.is_analyst_group = is_analyst
            rec.is_sales_manager_group = is_sales
            rec.is_assign_negotiator_group = is_assign_negotiator
            rec.is_auctions_manager_group = is_auctions
            rec.is_commercial_manager_group = is_commercial
            rec.is_negotiator_group = is_negotiator
            rec.is_contract_manager_group = is_contract_manager
            rec.is_committee_member_group = is_committee_member
            rec.is_city_studies_manager_group = is_city_studies_manager

    @api.depends('analyst_id', 'detailed_analyst_id', 'city_analyst_id', 'assigned_negotiator', 'assigned_project_manager', 'direct_sale_assigned_contract_manager', 'auction_assigned_contract_manager', 'project_path')
    @api.depends_context('uid')
    def _compute_assigned_users_permissions(self):
        user_id = self.env.user.id
        for rec in self:
            assigned_analyst = rec.city_analyst_id if rec.project_path == 'cities' else rec.analyst_id
            rec.is_assigned_analyst = bool(assigned_analyst) and assigned_analyst.id == user_id
            rec.is_assigned_detailed_analyst = bool(rec.detailed_analyst_id) and rec.detailed_analyst_id.id == user_id
            rec.is_assigned_negotiator = bool(rec.assigned_negotiator) and rec.assigned_negotiator.id == user_id
            rec.is_assigned_project_manager = bool(rec.assigned_project_manager) and rec.assigned_project_manager.id == user_id
            rec.is_assigned_data_completer = bool(rec.data_completer_id) and rec.data_completer_id.id == user_id
            rec.is_assigned_direct_sale_contract_manager = bool(rec.direct_sale_assigned_contract_manager) and rec.direct_sale_assigned_contract_manager.id == user_id
            rec.is_assigned_auction_contract_manager = bool(rec.auction_assigned_contract_manager) and rec.auction_assigned_contract_manager.id == user_id


    @api.onchange('coordinates_kmz_name', 'current_income_file_name', 'contract_agency_deed_attachment_name', 'entrie_name')
    def _onchange_attachment_names(self):
        fields_to_check = ['coordinates_kmz_name', 'current_income_file_name', 'contract_agency_deed_attachment_name']
        if self.entrie_name:
            for field in fields_to_check:
                name_val = getattr(self, field)
                if name_val and self.entrie_name not in name_val:
                    setattr(self, field, f"{self.entrie_name} - {name_val}")

    @api.depends('partner_id')
    def _compute_partner_mobile(self):
        for rec in self:
            if rec.partner_id:
                rec.partner_mobile = rec.partner_id.mobile
            elif not rec.partner_mobile:
                rec.partner_mobile = False

    @api.onchange('partner_id')
    def _onchange_partner_id_set_mobile(self):
        if self.partner_id:
            self.partner_mobile = self.partner_id.mobile
        else:
            self.partner_mobile = False

    @api.depends('entered_by_email')
    def _compute_assigned_negotiator(self):
        for rec in self:
            if rec.entered_by_email:
                email = rec.entered_by_email.strip()
                user = self.env['res.users'].sudo().search([('email', '=ilike', email)], limit=1)
                if not user:
                    user = self.env['res.users'].sudo().search([('login', '=ilike', email)], limit=1)
                if user:
                    rec.assigned_negotiator = user
                else:
                    rec.assigned_negotiator = rec.assigned_negotiator
            else:
                rec.assigned_negotiator = rec.assigned_negotiator

    @api.onchange('entered_by_email')
    def _onchange_entered_by_email(self):
        if self.entered_by_email:
            email = self.entered_by_email.strip()
            user = self.env['res.users'].sudo().search([('email', '=ilike', email)], limit=1)
            if not user:
                user = self.env['res.users'].sudo().search([('login', '=ilike', email)], limit=1)
            if user:
                self.assigned_negotiator = user

    @api.onchange('entered_by_id')
    def _onchange_entered_by_id(self):
        if self.entered_by_id:
            self.entered_by_email = self.entered_by_id.email
        else:
            self.entered_by_email = False

    def init(self):
        super().init()
        # Backfill standard_study_manager_approval_rel from standard_study_manager_approval
        self.env.cr.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'standard_study_manager_approval'
                ) AND EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'entries' AND column_name = 'standard_study_manager_approval_rel'
                ) THEN
                    UPDATE entries e
                    SET standard_study_manager_approval_rel = s.id
                    FROM standard_study_manager_approval s
                    WHERE e.standard_study_manager_approval = s.code
                      AND e.standard_study_manager_approval_rel IS NULL;
                END IF;

                -- Backfill city_analyst_id from analyst_id for city studies
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'entries' AND column_name = 'city_analyst_id'
                ) AND EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'entries' AND column_name = 'analyst_id'
                ) THEN
                    UPDATE entries e
                    SET city_analyst_id = e.analyst_id
                    FROM (
                        SELECT e2.id
                        FROM entries e2
                        LEFT JOIN project_path pp ON pp.id = e2.project_path_rel
                        LEFT JOIN request_type rt ON rt.id = e2.request_type_id
                        WHERE e2.city_analyst_id IS NULL
                          AND e2.analyst_id IS NOT NULL
                          AND (
                              e2.project_path = 'cities'
                              OR (pp.id IS NOT NULL AND (pp.code = 'cities' OR pp.name::text ILIKE '%cities%' OR pp.name::text ILIKE '%\u0645\u062f\u0646%'))
                              OR (rt.id IS NOT NULL AND (rt.name::text ILIKE '%city%' OR rt.name::text ILIKE '%\u0645\u062f\u0646%'))
                          )
                    ) sub
                    WHERE e.id = sub.id;
                END IF;
            END $$;
        """)
    @api.model
    def _migrate_detailed_study_stages(self):
        self.env.flush_all()
        self.env.cr.execute("""
            DO $$
            DECLARE
                v_det_analyst_id INTEGER;
                v_det_approval_id INTEGER;
                v_old_analyst_id INTEGER;
                v_old_approval_id INTEGER;
                v_det_req_type_id INTEGER;
            BEGIN
                SELECT res_id INTO v_det_analyst_id FROM ir_model_data WHERE module = 'bussma_system' AND name = 'detailed_study_analyst' LIMIT 1;
                SELECT res_id INTO v_det_approval_id FROM ir_model_data WHERE module = 'bussma_system' AND name = 'detailed_study_approval' LIMIT 1;
                SELECT res_id INTO v_old_analyst_id FROM ir_model_data WHERE module = 'bussma_system' AND name = 'analyst' LIMIT 1;
                SELECT res_id INTO v_old_approval_id FROM ir_model_data WHERE module = 'bussma_system' AND name = 'study_approval' LIMIT 1;
                SELECT res_id INTO v_det_req_type_id FROM ir_model_data WHERE module = 'bussma_system' AND name = 'detailed_study' LIMIT 1;

                IF v_det_analyst_id IS NOT NULL AND v_old_analyst_id IS NOT NULL THEN
                    IF to_regclass('entries_stage_history') IS NOT NULL THEN
                        UPDATE entries_stage_history h
                        SET stage_id = v_det_analyst_id
                        FROM entries e
                        WHERE h.entry_id = e.id
                          AND h.stage_id = v_old_analyst_id
                          AND (
                              h.is_assign_detailed_study IS TRUE
                              OR e.project_path = 'specialized'
                              OR (h.end_date IS NULL AND e.is_assign_detailed_study IS TRUE)
                          );
                    END IF;

                    UPDATE entries
                    SET stage_id = v_det_analyst_id,
                        project_stage_selection = 'detailed_study_analyst'
                    WHERE stage_id = v_old_analyst_id
                      AND (is_assign_detailed_study IS TRUE OR project_path = 'specialized');
                END IF;

                IF v_det_approval_id IS NOT NULL AND v_old_approval_id IS NOT NULL THEN
                    IF to_regclass('entries_stage_history') IS NOT NULL THEN
                        UPDATE entries_stage_history h
                        SET stage_id = v_det_approval_id
                        FROM entries e
                        WHERE h.entry_id = e.id
                          AND h.stage_id = v_old_approval_id
                          AND (
                              h.is_assign_detailed_study IS TRUE
                              OR e.project_path = 'specialized'
                              OR (h.end_date IS NULL AND e.is_assign_detailed_study IS TRUE)
                          );
                    END IF;

                    UPDATE entries
                    SET stage_id = v_det_approval_id,
                        project_stage_selection = 'detailed_study_approval'
                    WHERE stage_id = v_old_approval_id
                      AND (is_assign_detailed_study IS TRUE OR project_path = 'specialized');
                END IF;

                IF v_det_analyst_id IS NOT NULL THEN
                    UPDATE entries
                    SET project_stage_selection = 'detailed_study_analyst'
                    WHERE stage_id = v_det_analyst_id
                      AND (project_stage_selection IS NULL OR project_stage_selection != 'detailed_study_analyst');
                END IF;

                IF v_det_approval_id IS NOT NULL THEN
                    UPDATE entries
                    SET project_stage_selection = 'detailed_study_approval'
                    WHERE stage_id = v_det_approval_id
                      AND (project_stage_selection IS NULL OR project_stage_selection != 'detailed_study_approval');
                END IF;

                IF v_det_req_type_id IS NOT NULL THEN
                    UPDATE entries
                    SET request_type_id = v_det_req_type_id
                    WHERE project_path = 'specialized'
                      AND (request_type_id IS NULL OR request_type_id != v_det_req_type_id);
                END IF;
            END $$;
        """)
        self.env.invalidate_all()

    @api.model
    def _migrate_department_manager_stages(self):
        self.env.flush_all()
        sales_stage = self.env.ref('bussma_system.sale_manager_decision', raise_if_not_found=False)
        auctions_stage = self.env.ref('bussma_system.auctions_manager_decision', raise_if_not_found=False)
        if not sales_stage or not auctions_stage:
            return

        self.env.cr.execute("""
            SELECT to_regclass('entries_stage_history')
        """)
        has_history = bool(self.env.cr.fetchone()[0])

        if has_history:
            self.env.cr.execute("""
                UPDATE entries_stage_history h
                SET stage_id = %s
                FROM entries e
                WHERE h.entry_id = e.id
                  AND h.stage_id = %s
                  AND (
                      COALESCE(h.committee_decision, e.committee_decision) = 'auction'
                      OR (
                          COALESCE(h.committee_decision, e.committee_decision) = 'exclusion'
                          AND e.customer_intent = 'auction'
                      )
                  )
            """, (auctions_stage.id, sales_stage.id))

        self.env.cr.execute("""
            UPDATE entries
            SET stage_id = %s,
                project_stage_selection = 'auctions_manager_decision'
            WHERE stage_id = %s
              AND (
                  committee_decision = 'auction'
                  OR (committee_decision = 'exclusion' AND customer_intent = 'auction')
                  OR (
                      committee_decision = 'exclusion'
                      AND customer_intent IN ('select_all', 'studies_recommendation')
                      AND COALESCE(sales_manager_approval, '') != ''
                  )
              )
            RETURNING id
        """, (auctions_stage.id, sales_stage.id))
        moved_to_auctions_ids = [row[0] for row in self.env.cr.fetchall()]

        self.env.cr.execute("""
            UPDATE entries
            SET project_stage_selection = 'sales_manager_decision'
            WHERE stage_id = %s
              AND (project_stage_selection IS NULL OR project_stage_selection != 'sales_manager_decision')
            RETURNING id
        """, (sales_stage.id,))
        updated_to_sales_ids = [row[0] for row in self.env.cr.fetchall()]

        self.env.cr.execute("""
            UPDATE entries
            SET project_stage_selection = 'auctions_manager_decision'
            WHERE stage_id = %s
              AND (project_stage_selection IS NULL OR project_stage_selection != 'auctions_manager_decision')
        """, (auctions_stage.id,))

        self.env.invalidate_all()
        refreshed_ids = moved_to_auctions_ids + updated_to_sales_ids
        if refreshed_ids:
            for rec in self.browse(refreshed_ids):
                rec._notify_stage_authorized_users()

    def _sync_relation_selection_vals(self, vals):
        sync_map = {
            'project_path_rel': ('project_path', 'project.path', ['cities', 'specialized', 'standard']),
            'customer_intent_rel': ('customer_intent', 'customer.intent', ['direct_sale', 'auction', 'select_all', 'studies_recommendation']),
            'committee_decision_rel': ('committee_decision', 'committee.decision.type', ['direct_sale', 'auction', 'exclusion']),
            'auctions_manager_approval_rel': ('auctions_manager_approval', 'auction.manager.approval', ['committee_decision_accepted', 'committee_decision_rejected', 'request_transfer_auction']),
            'sales_manager_approval_rel': ('sales_manager_approval', 'sales.manager.approval', ['committee_decision_accepted', 'committee_decision_rejected', 'request_transfer_direct_sale']),
            'commercial_sector_manager_approval_rel': ('commercial_sector_manager_approval', 'commercial.sector.manager.approval', ['approval', 'return_committee', 'transfer', 'declined', 'postponed']),
            'final_owner_decision_rel': ('final_owner_decision', 'final.owner.decision', ['committee_price', 'higher_price', 'rejected']),
            'standard_study_manager_approval_rel': ('standard_study_manager_approval', 'standard.study.manager.approval', ['completed', 'incomplete', 'reject_and_archive']),
        }
        for rel_field, (sel_field, comodel, valid_codes) in sync_map.items():
            if rel_field in vals:
                rel_id = vals.get(rel_field)
                if rel_id:
                    rel = self.env[comodel].browse(rel_id)
                    vals[sel_field] = rel.code if rel.code in valid_codes else False
                else:
                    vals[sel_field] = False
            elif sel_field in vals:
                code = vals.get(sel_field)
                if code:
                    rel = self.env[comodel].search([('code', '=', code)], limit=1)
                    vals[rel_field] = rel.id if rel else False
                else:
                    vals[rel_field] = False
        return vals

    @api.depends('stage_history_ids', 'stage_history_filter_stage_id')
    def _compute_stage_history_filtered_ids(self):
        for rec in self:
            if rec.stage_history_filter_stage_id:
                rec.stage_history_filtered_ids = rec.stage_history_ids.filtered(
                    lambda h: h.stage_id == rec.stage_history_filter_stage_id
                )
            else:
                rec.stage_history_filtered_ids = rec.stage_history_ids

    @api.depends('stage_id', 'stage_history_ids', 'stage_history_ids.start_date', 'stage_history_ids.end_date', 'stage_history_ids.duration_days', 'stage_history_ids.stage_id', 'stage_history_ids.stage_id.project_stage_selection')
    def _compute_stage_durations(self):
        now = fields.Datetime.now()
        for rec in self:
            rec.stage_history_ids._compute_duration()

            if rec.stage_id and rec.stage_id.project_stage_selection not in ['completed', 'city_study_completed']:
                current_stage_histories = rec.stage_history_ids.filtered(lambda h: h.stage_id == rec.stage_id)
                rec.current_stage_duration_days = round(sum(current_stage_histories.mapped('duration_days')), 2)
            else:
                rec.current_stage_duration_days = 0.0

            valid_histories = rec.stage_history_ids.filtered(lambda h: h.stage_id.project_stage_selection not in ['completed', 'city_study_completed'])
            rec.total_stage_duration_days = round(sum(valid_histories.mapped('duration_days')), 2)

            stage_sums = {}
            preliminary_analyst_sum = 0.0
            detailed_analyst_sum = 0.0
            preliminary_study_approval_sum = 0.0
            detailed_study_approval_sum = 0.0
            sales_manager_decision_sum = 0.0
            auctions_manager_decision_sum = 0.0

            for h in valid_histories:
                sel = h.stage_id.project_stage_selection if h.stage_id else False
                if not sel or sel in ['completed', 'city_study_completed']:
                    continue

                stage_sums[sel] = stage_sums.get(sel, 0.0) + h.duration_days

                # 1. Analyst Stages
                if sel == 'detailed_study_analyst':
                    detailed_analyst_sum += h.duration_days
                elif sel == 'analyst':
                    is_detailed = (
                        rec.project_path == 'specialized'
                        or (rec.project_path == 'standard' and bool(getattr(h, 'is_assign_detailed_study', False)))
                    )
                    if is_detailed:
                        detailed_analyst_sum += h.duration_days
                    else:
                        preliminary_analyst_sum += h.duration_days

                # 2. Study Approval Stages
                elif sel == 'detailed_study_approval':
                    detailed_study_approval_sum += h.duration_days
                elif sel == 'study_approval':
                    is_detailed = (
                        rec.project_path == 'specialized'
                        or (rec.project_path == 'standard' and bool(getattr(h, 'is_assign_detailed_study', False)))
                    )
                    if is_detailed:
                        detailed_study_approval_sum += h.duration_days
                    else:
                        preliminary_study_approval_sum += h.duration_days

                # 3. Department Manager Decision Stages
                elif sel == 'sales_manager_decision':
                    sales_manager_decision_sum += h.duration_days
                elif sel == 'auctions_manager_decision':
                    auctions_manager_decision_sum += h.duration_days

            rec.duration_entry_screen_days = round(stage_sums.get('entry_screen', 0.0), 2)
            rec.duration_data_completion_days = round(stage_sums.get('data_completion', 0.0), 2)
            rec.duration_define_path_days = round(stage_sums.get('define_project_path_assign_analyst', 0.0), 2)

            rec.duration_preliminary_analyst_days = round(preliminary_analyst_sum, 2)
            rec.duration_detailed_analyst_days = round(detailed_analyst_sum, 2)

            rec.duration_preliminary_study_approval_days = round(preliminary_study_approval_sum, 2)
            rec.duration_detailed_study_approval_days = round(detailed_study_approval_sum, 2)
            rec.duration_study_approval_days = round(stage_sums.get('study_approval', 0.0), 2)

            rec.duration_committee_decision_days = round(stage_sums.get('committee_decision', 0.0), 2)

            rec.duration_sales_manager_decision_days = round(sales_manager_decision_sum, 2)
            rec.duration_sale_manager_decision_days = round(sales_manager_decision_sum, 2)
            rec.duration_auctions_manager_decision_days = round(auctions_manager_decision_sum, 2)

            rec.duration_commercial_approval_days = round(stage_sums.get('commercial_manager_approval', 0.0), 2)
            rec.duration_assign_negotiator_days = round(stage_sums.get('assign_negotiator', 0.0), 2)
            rec.duration_negotiator_days = round(stage_sums.get('negotiator', 0.0), 2)
            rec.duration_manager_contract_approval_days = round(stage_sums.get('manager_contract_approval', 0.0), 2)
            rec.duration_contract_followup_days = round(stage_sums.get('contract_followup', 0.0), 2)
            rec.duration_negotiation_approval_days = round(stage_sums.get('negotiation_approval', 0.0), 2)
            rec.duration_contract_completion_days = round(stage_sums.get('contract_completion', 0.0), 2)
            rec.duration_city_study_analyst_days = round(stage_sums.get('city_study_analyst', 0.0), 2)
            rec.duration_city_study_approval_days = round(stage_sums.get('city_study_approval', 0.0), 2)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('entrie_name', _('New')) == _('New'):
                vals['entrie_name'] = self.env['ir.sequence'].next_by_code('bussma.entries.sequence') or _('New')
            self._sync_relation_selection_vals(vals)
        records = super(Entries, self).create(vals_list)
        now = fields.Datetime.now()
        for rec in records:
            if rec.stage_id and rec.stage_id.project_stage_selection not in ['completed', 'city_study_completed']:
                self.env['entries.stage.history'].create({
                    'entry_id': rec.id,
                    'stage_id': rec.stage_id.id,
                    'start_date': now,
                    'is_assign_detailed_study': rec.is_assign_detailed_study,
                    'committee_decision': rec.committee_decision,
                })
            if rec.stage_id:
                rec._notify_stage_authorized_users()
            if rec.data_completer_id:
                rec._notify_data_completer_assigned()
        return records

    @api.depends('entrie_name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.entrie_name

    @api.depends('stage_id', 'stage_id.project_stage_selection', 'return_log_ids', 'return_log_ids.return_type', 'stage_history_ids', 'stage_history_ids.stage_id')
    def _compute_has_data_completion(self):
        for rec in self:
            if rec.has_data_completion:
                continue
            is_data_comp = (
                (rec.stage_id and rec.stage_id.project_stage_selection == 'data_completion') or
                any(log.return_type == 'data_completion' for log in rec.return_log_ids) or
                any(h.stage_id.project_stage_selection == 'data_completion' for h in rec.stage_history_ids)
            )
            rec.has_data_completion = is_data_comp

    @api.depends('return_log_ids')
    def _compute_return_counts(self):
        for rec in self:
            study_logs = rec.return_log_ids.filtered(lambda l: l.return_type == 'study_to_analyst')
            rec.study_return_count = len(study_logs.filtered(lambda l: l.study_type_detail != 'specialized'))
            rec.detailed_study_return_count = len(study_logs.filtered(lambda l: l.study_type_detail == 'specialized'))
            rec.committee_return_count = len(rec.return_log_ids.filtered(lambda l: l.return_type == 'manager_to_committee'))
            rec.department_return_count = len(rec.return_log_ids.filtered(lambda l: l.return_type == 'manager_to_department'))
            rec.return_to_lister_count = len(rec.return_log_ids.filtered(lambda l: l.return_type == 'return_to_lister'))
            rec.negotiator_return_count = len(rec.return_log_ids.filtered(lambda l: l.return_type in ['contract_to_negotiator', 'deputy_to_negotiator']))
            rec.data_completer_return_count = len(rec.return_log_ids.filtered(lambda l: l.return_type == 'data_completion'))

    def action_view_lister_returns(self):
        self.ensure_one()
        return {
            'name': _('Return to Lister'),
            'view_mode': 'list,form',
            'res_model': 'entries.return.log',
            'domain': [('entry_id', '=', self.id), ('return_type', '=', 'return_to_lister')],
            'context': {'default_entry_id': self.id, 'default_return_type': 'return_to_lister'},
            'type': 'ir.actions.act_window',
        }

    def action_view_study_returns(self):
        self.ensure_one()
        is_detailed = self.env.context.get('is_detailed_study')
        return {
            'name': _('Detailed Study Returns') if is_detailed else _('Preliminary Study Returns'),
            'view_mode': 'list,form',
            'res_model': 'entries.return.log',
            'domain': [
                ('entry_id', '=', self.id),
                ('return_type', '=', 'study_to_analyst'),
                ('study_type_detail', '=' if is_detailed else '!=', 'specialized'),
            ],
            'context': {
                'default_entry_id': self.id,
                'default_return_type': 'study_to_analyst',
                'hide_study_type': False,
            },
            'type': 'ir.actions.act_window',
        }

    def action_view_committee_returns(self):
        self.ensure_one()
        return {
            'name': _('Committee Returns'),
            'view_mode': 'list,form',
            'res_model': 'entries.return.log',
            'domain': [('entry_id', '=', self.id), ('return_type', '=', 'manager_to_committee')],
            'context': {'default_entry_id': self.id, 'default_return_type': 'manager_to_committee'},
            'type': 'ir.actions.act_window',
        }

    def action_view_department_returns(self):
        self.ensure_one()
        return {
            'name': _('Department Returns'),
            'view_mode': 'list,form',
            'res_model': 'entries.return.log',
            'domain': [('entry_id', '=', self.id), ('return_type', '=', 'manager_to_department')],
            'context': {'default_entry_id': self.id, 'default_return_type': 'manager_to_department'},
            'type': 'ir.actions.act_window',
        }

    def action_view_negotiator_returns(self):
        self.ensure_one()
        return {
            'name': _('Negotiator Returns'),
            'view_mode': 'list,form',
            'res_model': 'entries.return.log',
            'domain': [('entry_id', '=', self.id), ('return_type', 'in', ['contract_to_negotiator', 'deputy_to_negotiator'])],
            'context': {'default_entry_id': self.id, 'default_return_type': 'contract_to_negotiator'},
            'type': 'ir.actions.act_window',
        }

    def action_view_data_completer_returns(self):
        self.ensure_one()
        return {
            'name': _('Data Completer Returns'),
            'view_mode': 'list,form',
            'res_model': 'entries.return.log',
            'domain': [('entry_id', '=', self.id), ('return_type', '=', 'data_completion')],
            'context': {'default_entry_id': self.id, 'default_return_type': 'data_completion'},
            'type': 'ir.actions.act_window',
        }
    def _compute_is_from_deferred_archive_menu(self):
        for rec in self:
            rec.is_from_deferred_archive_menu = self.env.context.get('is_deferred_opportunities_archive_menu', False)

    
    @api.constrains('partner_mobile', 'investor_contact_number', 'project_stage_selection')
    def _check_phone_numbers(self):
        for record in self:
            phone = ''
            if record.project_stage_selection in ('entry_screen', 'data_completion') and record.partner_mobile:
                phone = record.partner_mobile.strip().replace(' ', '')
            elif record.project_stage_selection == 'city_study_analyst' and record.investor_contact_number:
                phone = record.investor_contact_number.strip().replace(' ', '')
            
            if phone:
                # Normalize: Remove leading plus, double zero, or Saudi prefix to check core mobile number
                normalized = phone
                if phone.startswith('+966'):
                    normalized = phone[4:]
                elif phone.startswith('00966'):
                    normalized = phone[5:]
                elif phone.startswith('966'):
                    normalized = phone[3:]
                elif phone.startswith('05'):
                    normalized = phone[1:]
                elif phone.startswith('5') and len(phone) == 9:
                    normalized = phone # Already normalized (without leading zero)
                
                # A valid Saudi mobile number should be Exactly 9 digits starting with '5' (the part after 0 or +966)
                if not normalized.isdigit() or not normalized.startswith('5') or len(normalized) != 9:
                    raise UserError(_("The phone number must be a valid Saudi mobile (e.g., 05xxxxxxxx, +9665xxxxxxxx, or 009665xxxxxxxx)."))

    @api.constrains('finishing_ratio')
    def _check_finishing_ratio(self):
        for record in self:
            if record.finishing_ratio < 0 or record.finishing_ratio > 100:
                raise UserError(_("The finishing ratio must be between 0 and 100."))

    @api.onchange('area_sqm', 'detailed_price_per_meter')
    def _onchange_detailed_price_per_meter(self):
        """When price-per-meter changes → compute total final price."""
        for record in self:
            if record.area_sqm and record.detailed_price_per_meter:
                record.detailed_final_property_price = record.area_sqm * record.detailed_price_per_meter

    @api.onchange('detailed_final_property_price')
    def _onchange_detailed_final_property_price(self):
        """When total final price changes → back-compute price-per-meter."""
        for record in self:
            if record.area_sqm and record.detailed_final_property_price:
                record.detailed_price_per_meter = record.detailed_final_property_price / record.area_sqm

    @api.onchange('area_sqm', 'price_per_meter')
    def _onchange_price_per_meter(self):
        """Preliminary Study: when price-per-meter changes → compute final property price."""
        for record in self:
            if record.area_sqm and record.price_per_meter:
                record.final_property_price = record.area_sqm * record.price_per_meter

    @api.onchange('final_property_price')
    def _onchange_final_property_price(self):
        """Preliminary Study: when final price changes → back-compute price-per-meter."""
        for record in self:
            if record.area_sqm and record.final_property_price:
                record.price_per_meter = record.final_property_price / record.area_sqm

    @api.onchange('area_sqm', 'direct_sale_price_per_meter', 'auction_price_per_meter')
    def _onchange_committee_meter_prices(self):
        for rec in self:
            if rec.area_sqm:
                if rec.direct_sale_price_per_meter:
                    rec.direct_sale_total_price = rec.area_sqm * rec.direct_sale_price_per_meter
                if rec.auction_price_per_meter:
                    rec.auction_total_price = rec.area_sqm * rec.auction_price_per_meter

    @api.onchange('direct_sale_total_price', 'auction_total_price')
    def _onchange_committee_total_prices(self):
        for rec in self:
            if rec.area_sqm:
                if rec.direct_sale_total_price:
                    rec.direct_sale_price_per_meter = rec.direct_sale_total_price / rec.area_sqm
                if rec.auction_total_price:
                    rec.auction_price_per_meter = rec.auction_total_price / rec.area_sqm

    def _get_committee_price(self):
        self.ensure_one()
        comm_dec = self.committee_decision or (self.committee_decision_rel.code if self.committee_decision_rel else False)
        if comm_dec == 'direct_sale':
            return self.direct_sale_total_price or 0.0
        elif comm_dec == 'auction':
            return self.auction_total_price or 0.0
        elif comm_dec == 'exclusion':
            intent = self.customer_intent or (self.customer_intent_rel.code if self.customer_intent_rel else False)
            if intent == 'auction':
                return self.auction_total_price or 0.0
            else:  # direct_sale, select_all, studies_recommendation, or default
                return self.direct_sale_total_price or 0.0
        else:
            return 0.0

    @api.depends(
        'final_owner_price',
        'manager_negotiator_final_owner_price',
        'committee_decision',
        'direct_sale_total_price',
        'auction_total_price'
    )
    def _compute_negotiation_price_diff_percentages(self):
        for rec in self:
            committee_price = rec._get_committee_price()
            if committee_price > 0:
                rec.final_owner_price_diff_percentage = (
                    (rec.final_owner_price - committee_price) / committee_price
                ) * 100.0 if rec.final_owner_price else 0.0
                rec.manager_negotiator_price_diff_percentage = (
                    (rec.manager_negotiator_final_owner_price - committee_price) / committee_price
                ) * 100.0 if rec.manager_negotiator_final_owner_price else 0.0
            else:
                rec.final_owner_price_diff_percentage = 0.0
                rec.manager_negotiator_price_diff_percentage = 0.0

    @api.onchange('area_sqm','final_owner_price_per_meter')
    def _onchange_final_owner_price_per_meter(self):
        """Negotiation: when negotiator price-per-meter changes → compute total owner price."""
        for record in self:
            if record.area_sqm and record.final_owner_price_per_meter:
                record.final_owner_price = record.area_sqm * record.final_owner_price_per_meter
                record._compute_negotiation_price_diff_percentages()

    @api.onchange('area_sqm','final_owner_price')
    def _onchange_final_owner_price(self):
        """Negotiation: when negotiator total owner price changes → back-compute price-per-meter."""
        for record in self:
            if record.area_sqm and record.final_owner_price:
                record.final_owner_price_per_meter = record.final_owner_price / record.area_sqm
                record._compute_negotiation_price_diff_percentages()

    @api.onchange('area_sqm','manager_negotiator_final_owner_price_per_meter')
    def _onchange_manager_negotiator_final_owner_price_per_meter(self):
        """Negotiation: when manager negotiator price-per-meter changes → compute total owner price."""
        for record in self:
            if record.area_sqm and record.manager_negotiator_final_owner_price_per_meter:
                record.manager_negotiator_final_owner_price = record.area_sqm * record.manager_negotiator_final_owner_price_per_meter
                record._compute_negotiation_price_diff_percentages()

    @api.onchange('area_sqm','manager_negotiator_final_owner_price')
    def _onchange_manager_negotiator_final_owner_price(self):
        """Negotiation: when manager negotiator total owner price changes → back-compute price-per-meter."""
        for record in self:
            if record.area_sqm and record.manager_negotiator_final_owner_price:
                record.manager_negotiator_final_owner_price_per_meter = record.manager_negotiator_final_owner_price / record.area_sqm
                record._compute_negotiation_price_diff_percentages()

    def _get_missing_numeric_fields(self):
        """ Helper method to check mandatory fields at each stage """
        self.ensure_one()
        fields_to_check = []
        
        # 0. Entry Stage (Listing & Data Completion)
        if self.project_stage_selection in ('entry_screen', 'data_completion'):
            fields_to_check = ['area_sqm']

        # 1. Preliminary Study
        elif self.project_stage_selection == 'analyst' and self.project_path == 'standard' and not self.is_assign_detailed_study:
            if self.preliminary_study_status != 'rejected':
                fields_to_check = [
                    'justice_index_average', 'comparison_average', 
                    'final_property_price', 'properties_count','price_per_meter'
                ]
                if not self.is_land_property_type:
                    fields_to_check.append('rooms_count')

        # 2. Detailed Study (detailed_study_analyst OR specialized path / standard with detailed study assigned)
        elif self.project_stage_selection == 'detailed_study_analyst' or (self.project_stage_selection == 'analyst' and (self.project_path == 'specialized' or self.is_assign_detailed_study)):
            fields_to_check = [
                'length_east', 'length_west', 'length_north', 'length_south',
                'expected_total_income_full_rent',
                'detailed_comparison_average', 'justice_ministry_index_average',
                'lowest_price_per_meter_total_property', 'highest_price_per_meter_total_property',
                'approximate_land_value_per_meter',
                'detailed_price_per_meter', 'detailed_final_property_price', 'finishing_ratio'
            ]
            if not self.is_land_property_type:
                fields_to_check.extend([
                    'building_area',
                    'floors_count', 'units_count', 'rooms_count',
                    'electricity_meters_count', 'water_meters_count',
                    'approximate_building_value_per_meter',
                ])
            
        # 3. Cities Study
        elif self.project_stage_selection == 'city_study_analyst':
            fields_to_check = [
                'area'
            ]
            
        # 4. Committee Decision
        elif self.project_stage_selection == 'committee_decision':
            if self.committee_decision == 'direct_sale':
                fields_to_check = ['marketing_duration_months', 'direct_sale_price_per_meter']
            elif self.committee_decision == 'auction':
                fields_to_check = ['marketing_duration_months', 'auction_price_per_meter']
            elif self.committee_decision == 'exclusion':
                fields_to_check = []
            else:
                fields_to_check = ['marketing_duration_months']

        # 5. Negotiation
        elif self.project_stage_selection == 'negotiator':
            if self.is_manager_negotiator:
                if self.manager_negotiator_final_owner_decision != 'rejected':
                    fields_to_check.extend(['manager_negotiator_final_owner_price_per_meter', 'manager_negotiator_final_owner_price'])
            else:
                if self.final_owner_decision != 'rejected':
                    fields_to_check.extend(['final_owner_price_per_meter', 'final_owner_price'])

        missing = [f for f in fields_to_check if getattr(self, f) in (0, 0.0, False, '')]
        
        if missing:
            labels = [self.fields_get([f])[f]['string'] for f in missing]
            stage_name = self.stage_id.name or ''
            raise UserError(_("Stage: %s\n\nThe following fields are Must not be zero:\n- %s") % (stage_name, "\n- ".join(labels)))

    def _check_missing_string_fields(self):
        """ Helper method to check mandatory string fields before moving to next stage """
        self.ensure_one()
        fields_to_check = []
        error_msg = False
        
        # 0. Entry Stage (Listing & Data Completion)
        if self.project_stage_selection in ('entry_screen', 'data_completion'):
            fields_to_check = [
                'customer_intent', 'partner_id', 'customer_role_rel', 'partner_mobile',
                'entered_by_id', 'entered_by_email', 'company_id', 'country_id',
                'city', 'district_id', 'property_type', 'property_usage_rel',
                'currency_id', 'plot_number', 'location_url',
                'requires_technical_offer', 'owner_type', 'property_attachment_ids'
            ]
            error_msg = _("The following fields are mandatory before moving to the define project path stage:\n- %s")

        # 1. Preliminary Study
        elif self.project_stage_selection == 'analyst' and self.project_path == 'standard' and not self.is_assign_detailed_study:
            if self.preliminary_study_status != 'rejected':
                fields_to_check = [
                    'preliminary_study_status', 'analyst_recommendation_preliminary', 'building_requirements',
                    'plan_number', 'deed_number', 'deed_date', 'property_facade'
                ]
                error_msg = _("The following fields are required before moving to the study approval stage:\n- %s")

        # 2. Detailed Study (detailed_study_analyst OR specialized path / standard with detailed study assigned)
        elif self.project_stage_selection == 'detailed_study_analyst' or (self.project_stage_selection == 'analyst' and (self.project_path == 'specialized' or self.is_assign_detailed_study)):
            fields_to_check = [
                'analyst_recommendation_details',
                'limit_east', 'internal_strength_points', 'current_total_income',
                'precise_plot_location_link', 'limit_north',
                'street', 'best_property_use', 'limit_west',
                'nearest_main_road', 'external_weakness_points', 'property_description',
                'limit_south', 'external_strength_points',
                'internal_weakness_points',
                'property_facade'
            ]
            if not self.is_land_property_type:
                fields_to_check.extend([
                    'plan_number',
                    'deed_number',
                    'deed_date',
                    'land_nature',
                    'property_age_estimated',
                    'detailed_building_requirements',
                    'building_license_number', 'building_license_date',
                    'electricity_meters_numbers', 'water_meters_numbers',
                ])
            error_msg = _("The following fields are required before moving to the study approval stage:\n- %s")

        # 3. Cities Study
        elif self.project_stage_selection == 'city_study_analyst':
            fields_to_check = [
                'gps_coordinates', 'industrial_city',
                'facility_investor', 'has_movables',
                'coordinates_kmz'
            ]

            if getattr(self, 'has_movables', False) == 'yes':
                fields_to_check.extend(['equipment', 'vehicles', 'machinery', 'systems'])
            error_msg = _("The following fields are required before moving to the cities study approval stage:\n- %s")

        # 5. Negotiation
        elif self.project_stage_selection == 'negotiator':
            if not self.is_sent_to_deputy_studies_manager:
                if self.is_manager_negotiator:
                    fields_to_check = ['manager_negotiator_note']
                else:
                    fields_to_check = ['negotiator_note']
                error_msg = _("The following fields are required before moving from the negotiation stage:\n- %s")

        # 6. Contracting Stage
        elif self.project_stage_selection == 'contract_followup':
            fields_to_check = [
                'contract_client_name', 'contract_client_identity', 
                'contract_client_birthdate', 'contract_client_mobile', 
                'contract_client_role', 'contract_duration'
            ]
            if self.contract_client_role == 'agent':
                fields_to_check.extend([
                    'contract_owner_name', 'contract_owner_identity', 
                    'contract_owner_birthdate', 'contract_owner_mobile',
                    'contract_agency_deed_attachment'
                ])
            if self.committee_decision == 'direct_sale':
                fields_to_check.append('direct_sale_assigned_contract_manager')
            elif self.committee_decision == 'auction':
                fields_to_check.append('auction_assigned_contract_manager')
            error_msg = _("The following fields are required to complete the contracting details:\n- %s")

        # 7. Negotiation Approval Stage
        elif self.project_stage_selection == 'negotiation_approval':
            fields_to_check = ['negotiation_commercial_manager_approval']
            if self.committee_decision == 'direct_sale':
                fields_to_check.append('negotiation_studies_manager_approval')
            error_msg = _("The following approvals are required before moving to contract completion stage:\n- %s")

        missing = [f for f in fields_to_check if not getattr(self, f) or getattr(self, f) == '']
        if missing:
            labels = [self.fields_get([f])[f]['string'] for f in missing]
            stage_name = self.stage_id.name or ''
            raise UserError(_("Stage: %s\n%s") % (stage_name, error_msg % "\n- ".join(labels)))
            
    def defining_project_path(self):
        for record in self:
            if not record.project_path:
                return
            
            xml_id_map = {
                'standard': 'bussma_system.preliminary_study',
                'specialized': 'bussma_system.detailed_study',
                'cities': 'bussma_system.city_study',
            }
            xml_id = xml_id_map.get(record.project_path)
            if xml_id:
                record.request_type_id = self.env.ref(xml_id, raise_if_not_found=False)
    
    def move_to_entry_archive(self):
        for rec in self:
            rec.is_entry_archive = True

    def action_standard_study_reject_and_archive(self):
        for rec in self:
            if not rec.standard_study_manager_note:
                raise UserError(_("Please provide a note before rejecting and archiving the listing."))
            rec.move_to_entry_archive()
    
    def move_to_deferred_opportunities_archive(self):
        for rec in self:
            rec.is_deferred_opportunities_archive = True
    
    def reactivate_deferred_opportunity(self):
        for rec in self:
            rec.is_deferred_opportunities_archive = False 
            
    def move_to_partners_screen(self):
        for rec in self:
            rec.is_partners_screen = True
            rec.partner_page_date = fields.Datetime.now()
    # ─────────────────────────────────────────────────────────────────────────
    # Email Helper
    # ─────────────────────────────────────────────────────────────────────────
    def _send_negotiation_email(self, template_xml_id, recipients, note=None):
        """Send a mail template to one or more users.
        Args:
            template_xml_id (str): XML ID of the mail.template record.
            recipients (res.users): A recordset of one or more users to email.
            note (str, optional): Return reason appended to email body.
        """
        if not recipients:
            return
        template = self.env.ref(template_xml_id, raise_if_not_found=False)
        if not template:
            _logger.warning("[Email] Template not found: %s", template_xml_id)
            return
        extra_html = ''
        if note:
            extra_html = '<p>%s</p>' % note
        for rec in self:
            # Pre-render body once per record (avoid repeated rendering per recipient)
            rendered_body = None
            if extra_html:
                rendered_body = template._render_field('body_html', [rec.id])[rec.id] + extra_html
            for user in recipients:
                if not user.email:
                    continue
                email_values = {
                    'email_to': user.email,
                    'email_from': self.env.user.email or self.env.company.email,
                    'model': False,
                    'res_id': False,
                }
                if rendered_body:
                    email_values['body_html'] = rendered_body
                try:
                    template.send_mail(rec.id, force_send=True, email_values=email_values)
                except Exception as e:
                    _logger.error("[Email] Failed sending '%s' to %s: %s", template_xml_id, user.email, e)

    def rejecte_owner_decision(self):
        for rec in self:
            if rec.project_stage_selection == 'manager_contract_approval':
                self.env['entries.return.log'].create({
                    'entry_id': rec.id,
                    'return_type': 'contract_to_negotiator',
                    'note': rec.commercial_sector_manager_contract_notes,
                })
                negotiator_stage = self.env.ref('bussma_system.negotiator')
                rec.write({'stage_id': negotiator_stage.id, 'is_sent_to_deputy_studies_manager': False, 'is_manager_negotiator': True})
                # Send return email to ALL users in the responsible group
                if rec.committee_decision == 'direct_sale':
                    sales_group = self.env.ref('bussma_system.group_sales_manager', raise_if_not_found=False)
                    recipients = sales_group.users if sales_group else self.env['res.users']
                elif rec.committee_decision == 'auction':
                    auctions_group = self.env.ref('bussma_system.group_auctions_manager', raise_if_not_found=False)
                    recipients = auctions_group.users if auctions_group else self.env['res.users']
                else:
                    recipients = self.env['res.users']
                if recipients:
                    rec._send_negotiation_email(
                        'bussma_system.email_template_returned_to_negotiator',
                        recipients,
                        note=rec.commercial_sector_manager_contract_notes,
                    )

    def action_send_to_deputy_studies_manager(self):
        """Send negotiation result to Deputy Studies Manager for approval."""
        for rec in self:
            self._check_missing_string_fields()
            if rec.project_stage_selection == 'negotiator':
                if rec.is_manager_negotiator:
                    if not rec.manager_negotiator_final_owner_decision:
                        raise UserError(_("Please set the owner's final decision before sending to Deputy Studies Manager."))
                    if rec.manager_negotiator_final_owner_decision != 'rejected':
                        if not rec.manager_negotiator_final_owner_price_per_meter or rec.manager_negotiator_final_owner_price_per_meter <= 0:
                            raise UserError(_("Please set the owner's final price per meter before sending to Deputy Studies Manager."))
                        if not rec.manager_negotiator_final_owner_price or rec.manager_negotiator_final_owner_price <= 0:
                            raise UserError(_("Please set the owner's final price before sending to Deputy Studies Manager."))
                else:
                    if not rec.final_owner_decision:
                        raise UserError(_("Please set the owner's final decision before sending to Deputy Studies Manager."))
                    if rec.final_owner_decision != 'rejected':
                        if not rec.final_owner_price_per_meter or rec.final_owner_price_per_meter <= 0:
                            raise UserError(_("Please set the owner's final price per meter before sending to Deputy Studies Manager."))
                        if not rec.final_owner_price or rec.final_owner_price <= 0:
                            raise UserError(_("Please set the owner's final price before sending to Deputy Studies Manager."))
                # Open the sub-step
                rec.write({'is_sent_to_deputy_studies_manager': True})
                # Find deputy studies manager users and send email to each
                deputy_group = self.env.ref('bussma_system.group_deputy_studies_manager', raise_if_not_found=False)
                if deputy_group:
                    for deputy_user in deputy_group.users:
                        rec._send_negotiation_email(
                            'bussma_system.email_template_sent_to_deputy_studies_manager',
                            deputy_user,
                        )
        return True

    def action_deputy_return_to_negotiator(self):
        """Deputy Studies Manager rejects and returns to negotiator.
        The gate (is_sent_to_deputy_studies_manager) is reset to False,
        forcing a re-negotiate + re-send cycle before deputy can review again.
        Notes stay so the warning banner shows the reason.
        """
        for rec in self:
            if rec.project_stage_selection == 'negotiator':
                if not rec.deputy_studies_manager_notes:
                    raise UserError(_("Please provide a note/reason for returning to negotiator."))
                self.env['entries.return.log'].create({
                    'entry_id': rec.id,
                    'return_type': 'deputy_to_negotiator',
                    'note': rec.deputy_studies_manager_notes,
                })
                # Reset the gate — notes stay for the warning banner
                rec.write({'is_sent_to_deputy_studies_manager': False})
                # Determine recipients based on who is the negotiator
                if rec.is_manager_negotiator:
                    # Returned to ALL users in the sales or auctions manager group
                    if rec.committee_decision == 'direct_sale':
                        sales_group = self.env.ref('bussma_system.group_sales_manager', raise_if_not_found=False)
                        recipients = sales_group.users if sales_group else self.env['res.users']
                    elif rec.committee_decision == 'auction':
                        auctions_group = self.env.ref('bussma_system.group_auctions_manager', raise_if_not_found=False)
                        recipients = auctions_group.users if auctions_group else self.env['res.users']
                    else:
                        recipients = self.env['res.users']
                else:
                    # Returned to the SINGLE assigned negotiator only
                    recipients = rec.assigned_negotiator
                if recipients:
                    rec._send_negotiation_email(
                        'bussma_system.email_template_returned_to_negotiator',
                        recipients,
                        note=rec.deputy_studies_manager_notes,
                    )
        return True
            
    def return_to_analyst(self):
        for rec in self:
            if rec.project_stage_selection in ['study_approval', 'detailed_study_approval', 'city_study_approval']:
                note = False
                study_type_detail = False
                if rec.project_stage_selection == 'detailed_study_approval' or rec.project_path == 'specialized' or (rec.project_path == 'standard' and rec.is_assign_detailed_study):
                    if not rec.specialized_study_manager_approval:
                        raise UserError(_("Please fill in the Study Manager Approval decision before returning."))
                    if rec.specialized_study_manager_approval != 'incomplete':
                        raise UserError(_("You cannot return the study when the approval decision is 'Completed'. The approval decision must be 'Incomplete'."))
                    if not rec.specialized_study_manager_note or not str(rec.specialized_study_manager_note).strip():
                        raise UserError(_("Please enter the Study Manager Notes explaining the return reason before returning."))
                    note = rec.specialized_study_manager_note
                    study_type_detail = 'specialized'
                elif rec.project_path == 'standard' and not rec.is_assign_detailed_study:
                    if not rec.standard_study_manager_approval:
                        raise UserError(_("Please fill in the Study Manager Approval decision before returning."))
                    if rec.standard_study_manager_approval != 'incomplete':
                        raise UserError(_("You cannot return the study when the approval decision is not 'Incomplete'."))
                    if not rec.standard_study_manager_note or not str(rec.standard_study_manager_note).strip():
                        raise UserError(_("Please enter the Study Manager Notes explaining the return reason before returning."))
                    note = rec.standard_study_manager_note
                    study_type_detail = 'standard'
                elif rec.project_path == 'cities' or rec.project_stage_selection == 'city_study_approval':
                    if not rec.cities_study_manager_approval:
                        raise UserError(_("Please fill in the Study Manager Approval decision before returning."))
                    if rec.cities_study_manager_approval != 'incomplete':
                        raise UserError(_("You cannot return the study when the approval decision is 'Completed'. The approval decision must be 'Incomplete'."))
                    if not rec.cities_study_manager_note or not str(rec.cities_study_manager_note).strip():
                        raise UserError(_("Please enter the Study Manager Notes explaining the return reason before returning."))
                    note = rec.cities_study_manager_note
                    study_type_detail = 'cities'
                    
                self.env['entries.return.log'].create({
                    'entry_id': rec.id,
                    'return_type': 'study_to_analyst',
                    'study_type_detail': study_type_detail,
                    'note': note,
                })

                if rec.project_stage_selection == 'detailed_study_approval' or (rec.project_stage_selection == 'study_approval' and (rec.project_path == 'specialized' or rec.is_assign_detailed_study)):
                    detailed_analyst_stage = self.env.ref('bussma_system.detailed_study_analyst', raise_if_not_found=False)
                    target_stage = detailed_analyst_stage or self.env.ref('bussma_system.analyst')
                    rec.write({'stage_id': target_stage.id})
                elif rec.project_path == 'cities':
                    analyst_stage = self.env.ref('bussma_system.city_study_analyst')
                    rec.write({'stage_id': analyst_stage.id})
                else:
                    analyst_stage = self.env.ref('bussma_system.analyst')
                    rec.write({'stage_id': analyst_stage.id})
    
    def commercial_sector_manager_approval_path(self):
        for rec in self:
            if rec.project_stage_selection == 'commercial_manager_approval':
                if rec.commercial_sector_manager_approval == 'approval':
                    assign_negotiator_stage = self.env.ref('bussma_system.assign_negotiator', raise_if_not_found=False)
                    if assign_negotiator_stage:
                        rec.write({'stage_id': assign_negotiator_stage.id})
                elif rec.commercial_sector_manager_approval == 'return_committee':
                    self.env['entries.return.log'].create({
                        'entry_id': rec.id,
                        'return_type': 'manager_to_committee',
                        'note': rec.commercial_sector_manager_notes or rec.commercial_sector_manager_reason or '',
                    })
                    committee_stage = self.env.ref('bussma_system.committee_decision', raise_if_not_found=False)
                    if committee_stage:
                        rec.write({'stage_id': committee_stage.id})
                elif rec.commercial_sector_manager_approval == 'transfer':
                    rec.move_to_partners_screen()
                elif rec.commercial_sector_manager_approval == 'declined':
                    rec.move_to_entry_archive()
                elif rec.commercial_sector_manager_approval == 'postponed':
                    rec.move_to_deferred_opportunities_archive()
            elif rec.project_stage_selection == 'manager_contract_approval':
                if rec.commercial_sector_manager_contract_approval == 'transfer':
                    rec.move_to_partners_screen()
                    
    def commercial_sector_manager_declined(self):
        return self.commercial_sector_manager_approval_path()
    
    def send_email_to_detailed_study(self):
        for rec in self:
            if rec.project_stage_selection in ['detailed_study_analyst', 'analyst']:
                if not rec.detailed_analyst_id:
                    raise UserError(_("Please select a detailed analyst"))
                if not rec.detailed_analyst_id.email:
                    raise UserError(_("The selected detailed analyst has no email address."))
                rec.write({'is_send_email_to_detailed_study': True})
                template = self.env.ref('bussma_system.email_template_analyst_assigned', raise_if_not_found=False)
                email_values = {
                    'email_to': rec.detailed_analyst_id.email,
                    'email_from': rec.env.user.email or rec.env.company.email,
                    'model': False,
                    'res_id': False,
                }
                if template and rec.detailed_analyst_id and rec.detailed_analyst_id.email:
                    try:
                        template.send_mail(rec.id, force_send=True, email_values=email_values)
                        _logger.info("[Email] Sent successfully to %s", rec.detailed_analyst_id.email)
                        notification_msg = _("Email has been sent to the Analyst")
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'reload',
                        }
                    except Exception as e:
                        _logger.error("[Email] Send failed: %s", str(e))
                else:
                    _logger.warning("[Email] Not sent — Template: %s | Analyst: %s | Email: %s",
                                    template.name if template else "MISSING",
                                    rec.detailed_analyst_id.name if rec.detailed_analyst_id else "MISSING",
                                    rec.detailed_analyst_id.email if rec.detailed_analyst_id and rec.detailed_analyst_id.email else "MISSING")
                    
    def action_return_to_lister(self):
        """Return the entry record to the Entry Screen stage with lister note."""
        for rec in self:
            if rec.is_authorized_property != 'return_to_lister':
                raise UserError(_("Please select 'Return to Lister' under Is Authorized Property first."))
            if not rec.return_to_lister_note:
                raise UserError(_("Please enter a Return to Lister Note before proceeding."))

            entry_screen_stage = self.env.ref('bussma_system.entry_screen', raise_if_not_found=False)
            if not entry_screen_stage:
                raise UserError(_("Entry Screen stage could not be found."))

            self.env['entries.return.log'].create({
                'entry_id': rec.id,
                'return_type': 'return_to_lister',
                'note': rec.return_to_lister_note,
            })

            rec.write({
                'stage_id': entry_screen_stage.id,
            })

            # Send email notification to the lister (entered_by_id or create_uid)
            lister_user = rec.entered_by_id or rec.create_uid
            lister_email = rec.entered_by_email or (lister_user.email if lister_user else False)
            if lister_user and lister_email:
                template = self.env.ref('bussma_system.email_template_entry_returned_to_lister', raise_if_not_found=False)
                if template:
                    try:
                        template.send_mail(
                            rec.id,
                            force_send=True,
                            email_values={
                                'email_to': lister_email,
                                'email_from': rec.env.user.email or rec.env.company.email,
                                'model': False,
                                'res_id': False,
                            }
                        )
                    except Exception as e:
                        _logger.error("[Entries] Failed to send return to lister email: %s", str(e))

    def action_send_to_data_completion(self):
        """Send the entry record to Data Completion stage and notify the assigned completer."""
        for rec in self:
            if rec.is_authorized_property != 'data_completion':
                raise UserError(_("Please select 'Data Completion' under Is Authorized Property first."))
            missing_fields = [f for f in ('data_completer_id', 'data_completion_note') if not getattr(rec, f)]
            if missing_fields:
                labels = [rec.fields_get([f])[f]['string'] for f in missing_fields]
                stage_name = rec.stage_id.name or ''
                error_msg = _("The following fields are required before sending to data completion:\n- %s")
                raise UserError(_("Stage: %s\n%s") % (stage_name, error_msg % "\n- ".join(labels)))

            data_completion_stage = self.env.ref('bussma_system.data_completion', raise_if_not_found=False)
            if not data_completion_stage:
                raise UserError(_("Data Completion stage could not be found."))

            is_return = bool(
                rec.has_data_completion or
                rec.stage_history_ids.filtered(lambda h: h.stage_id.project_stage_selection == 'data_completion')
            )
            if is_return:
                self.env['entries.return.log'].create({
                    'entry_id': rec.id,
                    'return_type': 'data_completion',
                    'note': rec.data_completion_note,
                })

            rec.write({
                'stage_id': data_completion_stage.id,
                'has_data_completion': True,
            })

    def action_accept(self):
        notification_msg = False
        for rec in self:
            rec._get_missing_numeric_fields()
            rec._check_missing_string_fields()
            rec.defining_project_path()

            if rec.project_stage_selection in ('entry_screen', 'data_completion'):
                if rec.project_stage_selection == 'data_completion' and rec.data_completer_id != self.env.user:
                    raise UserError(_("Only the assigned Data Completer can submit this entry."))
                target_stage = self.env.ref('bussma_system.define_project_path_assign_analyst', raise_if_not_found=False)
                if not target_stage:
                    raise UserError(_("Define Project Path stage not found. Please contact administrator."))
                rec.write({
                    'stage_id': target_stage.id,
                    'is_authorized_property': False,
                })
                return True

            # ── Stage: Define Project Path & Assign Analyst ──────────────────────
            elif rec.project_stage_selection == 'define_project_path_assign_analyst':
                if rec.is_authorized_property in ['no', 'return_to_lister', 'data_completion']:
                    raise UserError(_("Cannot proceed: Property is not authorized. Please take the appropriate action (Archive, Return to Lister, or Data Completion)."))
                if not rec.project_path:
                    raise UserError(_("Please select the Project Path before proceeding."))
                
                if rec.project_path == 'specialized':
                    if not rec.detailed_analyst_id:
                        raise UserError(_("Please assign a Detailed Analyst before proceeding."))
                    assigned_user = rec.detailed_analyst_id
                elif rec.project_path == 'cities':
                    if not rec.city_analyst_id:
                        raise UserError(_("Please assign a City Analyst before proceeding."))
                    assigned_user = rec.city_analyst_id
                else:
                    if not rec.analyst_id:
                        raise UserError(_("Please assign an Analyst before proceeding."))
                    assigned_user = rec.analyst_id
                
                # Send email notification to the assigned analyst
                template = self.env.ref('bussma_system.email_template_analyst_assigned', raise_if_not_found=False)
                email_values = {
                    'email_to': assigned_user.email if assigned_user else False,
                    'email_from': rec.env.user.email,
                    'model': False,
                    'res_id': False,
                }
                if rec.project_path == 'cities':
                    analyst_stage = self.env.ref('bussma_system.city_study_analyst', raise_if_not_found=False)
                elif rec.project_path == 'specialized':
                    analyst_stage = self.env.ref('bussma_system.detailed_study_analyst', raise_if_not_found=False)
                else:
                    analyst_stage = self.env.ref('bussma_system.analyst', raise_if_not_found=False)

                if analyst_stage:
                    rec.write({'stage_id': analyst_stage.id})

                if template and assigned_user and assigned_user.email:
                    try:
                        template.send_mail(rec.id, force_send=True, email_values=email_values)
                        _logger.info("[Email] Sent successfully to %s", assigned_user.email)
                        notification_msg = _("Email has been sent to the Analyst")
                    except Exception as e:
                        _logger.error("[Email] Send failed: %s", str(e))
                else:
                    _logger.warning("[Email] Not sent — Template: %s | Analyst: %s | Email: %s",
                        bool(template), bool(assigned_user),
                        assigned_user.email if assigned_user else 'MISSING'
                    )
                return True

            # ── Validation: Analyst → Study Approval (Preliminary Study / Legacy) ───────────
            elif rec.project_stage_selection == 'analyst':
                if rec.is_assign_detailed_study == "yes" or rec.is_assign_detailed_study is True:
                    if not rec.detailed_analyst_id:
                        raise UserError(_("Please assign a Detailed Assigned Analyst before proceeding."))
                    target_stage = self.env.ref('bussma_system.detailed_study_approval', raise_if_not_found=False) or self.env.ref('bussma_system.study_approval', raise_if_not_found=False)
                else:
                    target_stage = self.env.ref('bussma_system.study_approval', raise_if_not_found=False)
                if not target_stage:
                    raise UserError(_("Preliminary Study Approval stage not found. Please contact administrator."))
                rec.write({'stage_id': target_stage.id})
                return True

            # ── Stage: Detailed Study Analyst → Detailed Study Approval ───────
            elif rec.project_stage_selection == 'detailed_study_analyst':
                if not rec.detailed_analyst_id:
                    raise UserError(_("Please assign a Detailed Assigned Analyst before proceeding."))
                detailed_fields_to_check = [
                    'limit_east', 'limit_west', 'limit_north', 'limit_south',
                    'street', 'nearest_main_road', 'precise_plot_location_link',
                    'internal_strength_points', 'internal_weakness_points',
                    'external_strength_points', 'external_weakness_points',
                    'best_property_use', 'analyst_recommendation_details',
                    'property_description',
                ]
                if not rec.is_land_property_type:
                    detailed_fields_to_check.extend([
                        'land_nature',
                        'building_license_number',
                        'building_license_date',
                        'detailed_building_requirements',
                        'electricity_meters_numbers',
                        'water_meters_numbers',
                    ])
                missing_detailed = [
                    f for f in detailed_fields_to_check
                    if getattr(rec, f) in (0, 0.0, False, '')
                ]
                if missing_detailed:
                    field_labels = [rec.fields_get([f])[f]['string'] for f in missing_detailed]
                    stage_name = rec.stage_id.name or ''
                    raise UserError(
                        _("Stage: %s\n\nThe following fields are required:\n- %s")
                        % (stage_name, "\n- ".join(field_labels))
                    )
                target_stage = self.env.ref('bussma_system.detailed_study_approval', raise_if_not_found=False)
                if not target_stage:
                    raise UserError(_("Detailed Study Approval stage not found. Please contact administrator."))
                rec.write({'stage_id': target_stage.id})
                return True

            # ── Stage: City Study Analyst → Send to City Study Approval ───────
            elif rec.project_stage_selection == 'city_study_analyst':
                target_stage = self.env.ref('bussma_system.city_study_approval', raise_if_not_found=False)
                if not target_stage:
                    raise UserError(_("City Study Approval stage not found. Please contact administrator."))
                rec.write({'stage_id': target_stage.id})
                return True
            elif rec.project_stage_selection == 'city_study_approval':
                target_stage = self.env.ref('bussma_system.city_study_completed', raise_if_not_found=False)
                if not target_stage:
                    raise UserError(_("City Study Completed stage not found. Please contact administrator."))
                rec.write({'stage_id': target_stage.id})
                return True

            elif rec.project_stage_selection == 'study_approval':
                is_studies_mgr = (
                    self.env.user.has_group('bussma_system.group_studies_manager') or
                    self.env.user.has_group('bussma_system.group_deputy_studies_manager') or
                    self.env.user.has_group('bussma_system.group_rnd_manager')
                )
                if rec.is_assign_detailed_study:
                    if not is_studies_mgr:
                        raise UserError(_("Only the Studies Manager can mark this project as completed."))

                    if rec.specialized_study_manager_approval != 'completed':
                        raise UserError(_("Dose not confirm detailed study"))
                    turn_to_completed = self.env.ref('bussma_system.completed')
                    rec.write({'stage_id': turn_to_completed.id})
                    return True
                else:
                    if not is_studies_mgr:
                        raise UserError(_("Only the Studies Manager can send this study to the committee."))

                    if rec.project_path == 'standard' and rec.standard_study_manager_approval != 'completed':
                        raise UserError(_("Standard Study Manager Approval must be completed before sending to the committee."))
                    elif rec.project_path == 'specialized' and rec.specialized_study_manager_approval != 'completed':
                        raise UserError(_("Specialized Study Manager Approval must be completed before sending to the committee."))

                    committee_stage = self.env.ref('bussma_system.committee_decision', raise_if_not_found=False)
                    if not committee_stage:
                        raise UserError(_("Committee Decision stage not found. Please contact administrator."))
                    rec.write({'stage_id': committee_stage.id})
                    return True

            # ── Stage: Detailed Study Approval ────────────────────────────────────
            elif rec.project_stage_selection == 'detailed_study_approval':
                is_studies_mgr = (
                    self.env.user.has_group('bussma_system.group_studies_manager') or
                    self.env.user.has_group('bussma_system.group_deputy_studies_manager') or
                    self.env.user.has_group('bussma_system.group_rnd_manager')
                )
                if not is_studies_mgr:
                    raise UserError(_("Only the Studies Manager can approve the detailed study."))

                if rec.specialized_study_manager_approval != 'completed':
                    raise UserError(_("Specialized Study Manager Approval must be completed before proceeding."))

                if rec.project_path == 'specialized':
                    committee_stage = self.env.ref('bussma_system.committee_decision', raise_if_not_found=False)
                    if not committee_stage:
                        raise UserError(_("Committee Decision stage not found. Please contact administrator."))
                    rec.write({'stage_id': committee_stage.id})
                    return True
                else:
                    completed_stage = self.env.ref('bussma_system.completed', raise_if_not_found=False)
                    if not completed_stage:
                        raise UserError(_("Completed stage not found. Please contact administrator."))
                    rec.write({'stage_id': completed_stage.id})
                    return True

            # ── Stage: Committee Decision ─────────────────────────────────────────
            elif rec.project_stage_selection == 'committee_decision':
                if rec.is_returned_from_commercial_manager:
                    if not rec.committee_decision:
                        raise UserError(_("Please select the Committee Decision (Direct Sale / Auction / Exclusion) before proceeding."))
                    owner_decision = (
                        rec.manager_negotiator_final_owner_decision
                        if rec.is_manager_negotiator
                        else rec.final_owner_decision
                    )
                    if owner_decision and owner_decision == 'higher_price':
                        contract_approval_stage = self.env.ref('bussma_system.manager_contract_approval', raise_if_not_found=False)
                        if contract_approval_stage:
                            rec.write({'stage_id': contract_approval_stage.id,
                                       'is_returned_from_commercial_manager': False,})
                        return True
                else:
                    if rec.committee_decision == 'auction' or (
                        rec.committee_decision == 'exclusion' and rec.customer_intent == 'auction'
                    ):
                        target_stage = self.env.ref('bussma_system.auctions_manager_decision', raise_if_not_found=False)
                        error_msg = _("Auctions Manager Decision stage not found.")
                    else:
                        target_stage = self.env.ref('bussma_system.sale_manager_decision', raise_if_not_found=False)
                        error_msg = _("Sales Manager Decision stage not found.")
                    if not target_stage:
                        raise UserError(error_msg)
                    rec.write({'stage_id': target_stage.id})
                    return True

            elif rec.project_stage_selection == 'sales_manager_decision':
                if not rec.sales_manager_approval:
                    raise UserError(_("The Sales Manager must submit their decision before proceeding."))
                if (
                    rec.committee_decision == 'exclusion'
                    and rec.customer_intent in ('select_all', 'studies_recommendation')
                ):
                    target_stage = self.env.ref('bussma_system.auctions_manager_decision', raise_if_not_found=False)
                    if not target_stage:
                        raise UserError(_("Auctions Manager Decision stage not found."))
                else:
                    target_stage = self.env.ref('bussma_system.commercial_manager_approval', raise_if_not_found=False)
                    if not target_stage:
                        raise UserError(_("The commercial sector manager approval stage is not found. Please contact the administrator."))
                rec.write({'stage_id': target_stage.id})
                return True

            elif rec.project_stage_selection == 'auctions_manager_decision':
                if not rec.auctions_manager_approval:
                    raise UserError(_("The Auctions Manager must submit their decision before proceeding."))
                target_stage = self.env.ref('bussma_system.commercial_manager_approval', raise_if_not_found=False)
                if not target_stage:
                    raise UserError(_("The commercial sector manager approval stage is not found. Please contact the administrator."))
                rec.write({'stage_id': target_stage.id})
                return True

            # ── Stage: Assign Negotiator
            elif rec.project_stage_selection == 'assign_negotiator':
                if not self.env.user.has_group('bussma_system.group_assign_negotiator'):
                    raise UserError(_("Only users with 'Assign Negotiator' permission can perform this action."))
                if not rec.assigned_negotiator:
                    raise UserError(_("Please assign a Negotiator before proceeding."))

                negotiator_stage = self.env.ref('bussma_system.negotiator', raise_if_not_found=False)
                if not negotiator_stage:
                    raise UserError(_("The negotiator stage is not found. Please contact the administrator."))
                rec.write({'stage_id': negotiator_stage.id})
                rec._notify_negotiator_assigned()
                return True

            # ── Stage: Negotiator ───────────────────────────────────────────────
            elif rec.project_stage_selection == 'negotiator':
                owner_decision = (
                    rec.manager_negotiator_final_owner_decision
                    if rec.is_manager_negotiator
                    else rec.final_owner_decision
                )
                if owner_decision == 'higher_price':
                    committee_stage = self.env.ref('bussma_system.committee_decision')
                    self.env['entries.return.log'].create({
                        'entry_id': rec.id,
                        'return_type': 'manager_to_committee',
                        'note': rec.negotiator_note if not rec.is_manager_negotiator else rec.manager_negotiator_note,
                    })
                    rec.write({'stage_id': committee_stage.id,
                                'is_returned_from_commercial_manager': True,
                               })
                    return True
                if rec.is_sent_to_deputy_studies_manager:
                    if rec.deputy_studies_manager_approval != 'accepted':
                        raise UserError(_("Approval from the Deputy Studies Manager is required before sending to Contract Approval."))
                    if not self.env.user.has_group('bussma_system.group_deputy_studies_manager'):
                        raise UserError(_("Only the Deputy Studies Manager can send this entry to Contract Approval."))
                    manager_contract_approval_stage = self.env.ref('bussma_system.manager_contract_approval', raise_if_not_found=False)
                    if not manager_contract_approval_stage:
                        raise UserError(_("The manager contract approval stage is not found. Please contact the administrator."))
                    rec.write({'stage_id': manager_contract_approval_stage.id})
                    return True

            elif rec.project_stage_selection == 'manager_contract_approval':
                owner_decision = (
                    rec.manager_negotiator_final_owner_decision
                    if rec.is_manager_negotiator
                    else rec.final_owner_decision
                )
                if (
                    rec.commercial_sector_manager_contract_approval != 'accepted'
                    or owner_decision not in ['committee_price', 'higher_price']
                ):
                    raise UserError(_("You cannot proceed to the Contract Stage.\n" "Approval from both the Sector Manager and the Owner is required first."))
                contract_followup_stage = self.env.ref('bussma_system.contract_followup', raise_if_not_found=False)
                if not contract_followup_stage:
                    raise UserError(_("Contract Followup Stage not found. Please contact the administrator."))
                rec.write({'stage_id': contract_followup_stage.id})
                return True

            elif rec.project_stage_selection == 'contract_followup':
                if not rec.is_assigned_project_manager:
                    raise UserError(_("Only the assigned Project Manager can move this entry to the next stage."))
                if rec.committee_decision == 'auction':
                    target_stage = self.env.ref('bussma_system.negotiation_approval', raise_if_not_found=False)
                    if not target_stage:
                        raise UserError(_("Negotiation Approval stage not found. Please contact the administrator."))
                elif rec.committee_decision == 'direct_sale':
                    target_stage = self.env.ref('bussma_system.contract_completion', raise_if_not_found=False)
                    if not target_stage:
                        raise UserError(_("Contract Completion stage not found. Please contact the administrator."))
                rec.write({'stage_id': target_stage.id})
                return True

            elif rec.project_stage_selection == 'negotiation_approval':
                if rec.negotiation_commercial_manager_approval != 'approval':
                    raise UserError(_("Commercial Sector Manager Approval is required to complete negotiation approval."))
                if rec.committee_decision != 'auction' and rec.negotiation_studies_manager_approval != 'approval':
                    raise UserError(_("Studies Manager Approval is required to complete negotiation approval."))
                contract_completion_stage = self.env.ref('bussma_system.contract_completion', raise_if_not_found=False)
                if not contract_completion_stage:
                    raise UserError(_("Contract Completion stage not found. Please contact the administrator."))
                rec.write({'stage_id': contract_completion_stage.id})
                return True

            elif rec.project_stage_selection == 'contract_completion':
                if rec.project_path == 'specialized':
                    if not self.env.user.has_group('bussma_system.group_auctions_manager'):
                        raise UserError(_("Only the Auctions Manager can mark this project as completed."))
                    completed_stage = self.env.ref('bussma_system.completed')
                    rec.write({'stage_id': completed_stage.id})
                    return True
                if rec.project_path == 'standard':
                    if rec.committee_decision == 'direct_sale' and rec.direct_sale_contract_status == 'yes':
                        rec.assign_detailed_study()
                        return True
                    if rec.committee_decision == 'auction' and rec.auction_contract_status == 'yes':
                        rec.assign_detailed_study()
                        return True

        result = super(Entries, self).action_accept()
        if notification_msg:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Notification'),
                    'message': notification_msg,
                    'sticky': True,
                    'type': 'success',
                    'next': result if isinstance(result, dict) else False,
                }
            }
        return result

    def _get_mail_thread_data_attachments(self):
        """ Exclude attachments belonging to explicit model fields from the Chatter attachment popover (📎 button). """
        res = super(Entries, self)._get_mail_thread_data_attachments()
        if self:
            self.ensure_one()
            field_attachment_ids = set()
            for field_name in [
                'property_attachment_ids',
                'facility_photo_ids',
                'rent_contract_ids',
                'direct_sale_contract_attachments',
                'auction_contract_attachments',
            ]:
                if hasattr(self, field_name):
                    attachments = getattr(self, field_name)
                    if attachments:
                        field_attachment_ids.update(attachments.ids)

            if field_attachment_ids:
                res = res.filtered(lambda a: a.id not in field_attachment_ids)
        return res

    def action_send(self):
        for rec in self:
            rec._get_missing_numeric_fields()
            rec._check_missing_string_fields()
        return super(Entries, self).action_send()

    @api.depends(
        "stage_id",
        "is_authorized_property",
        "project_path",
        "project_stage_selection",
        "cities_study_manager_approval",
        "specialized_study_manager_approval",
        "standard_study_manager_approval",
        "committee_decision",
        "sales_manager_approval",
        "auctions_manager_approval",
        "commercial_sector_manager_contract_approval",
        "deputy_studies_manager_approval",
        "is_sent_to_deputy_studies_manager",
        "final_owner_decision",
        "is_manager_negotiator",
        "manager_negotiator_final_owner_decision",
        "direct_sale_contract_status",
        "auction_contract_status",
        # Numeric fields to trigger recompute
        "verified_income", "expected_full_lease_income", "final_property_price",
        "building_area",
        "area", "marketing_duration_months", "direct_sale_price_per_meter", 
        "auction_price_per_meter", "final_owner_price", "manager_negotiator_final_owner_price",
        # Char boundary fields to trigger recompute
        "limit_east", "limit_west", "limit_north", "limit_south",
    )
    def _compute_display_button(self):
        super()._compute_display_button()
        status = self.env.ref(
            'bussma_system.define_project_path_assign_analyst',
            raise_if_not_found=False
        )
        for rec in self:
            rec.display_button_refuse = False
            hide_accept = False
            if (
                rec.is_entry_archive
                or rec.is_deferred_opportunities_archive
                or rec.is_listing_archive_2023
                or rec.is_technical_offers_archive
                or rec.is_partners_screen
            ):
                rec.display_button_accept = False
                continue
            if (
                status
                and rec.stage_id == status
                and rec.is_authorized_property in ['no', 'return_to_lister', 'data_completion']
            ):
                hide_accept = True
            # 2️ Cities
            if (
                rec.project_path == 'cities'
                and rec.project_stage_selection == 'city_study_approval'
                and rec.cities_study_manager_approval == 'incomplete'
            ):
                hide_accept = True
            # 3️ Specialized / Detailed Study Approval
            if (
                rec.project_stage_selection in ['detailed_study_approval', 'study_approval']
                and rec.specialized_study_manager_approval == 'incomplete'
            ):
                hide_accept = True
            # 4️ Standard
            if (
                rec.project_path == 'standard'
                and rec.project_stage_selection == 'study_approval'
                and rec.standard_study_manager_approval in ['incomplete', 'reject_and_archive']
            ):
                hide_accept = True
            # 5️ Commercial Manager Approval logic
            if rec.project_stage_selection == 'commercial_manager_approval':
                rec.display_button_accept = False
                continue
            # Negotiator Stage Deputy Approval check
            if rec.project_stage_selection == 'negotiator':
                # Hide main advance button if sub-step not completed
                if not rec.is_sent_to_deputy_studies_manager or rec.deputy_studies_manager_approval != 'accepted':
                    hide_accept = True
            # 6️ Manager Contract Approval (NEW LOGIC)
            if rec.project_stage_selection == 'manager_contract_approval':
                hide_accept = True
                if rec.commercial_sector_manager_contract_approval == 'accepted':
                    if (
                        not rec.is_manager_negotiator
                        and rec.final_owner_decision in ['committee_price', 'higher_price']
                    ):
                        hide_accept = False
                    elif (
                        rec.is_manager_negotiator
                        and rec.manager_negotiator_final_owner_decision in ['committee_price', 'higher_price']
                    ):
                        hide_accept = False
            # 7️ Contract Followup
            if rec.project_stage_selection == 'contract_followup':
                hide_accept = False
                if (
                    (rec.committee_decision == 'direct_sale'
                     and rec.direct_sale_contract_status == 'no')
                    or
                    (rec.committee_decision == 'auction'
                     and rec.auction_contract_status == 'no')
                ):
                    hide_accept = True
            if hide_accept:
                rec.display_button_accept = False

    def assign_detailed_study(self):
        for rec in self:
            if rec.project_path == 'standard':
                rec.is_assign_detailed_study = True
                assign_detailed_study_analyst = self.env.ref('bussma_system.detailed_study_analyst', raise_if_not_found=False)
                if not assign_detailed_study_analyst:
                    assign_detailed_study_analyst = self.env.ref('bussma_system.analyst')
                rec.write({'stage_id': assign_detailed_study_analyst.id})

    def write(self, vals):
        if not (vals.get('is_entry_archive') is False) and not self.env.context.get('bypass_archive_check'):
            exempt_keys = {
                'message_follower_ids',
                'message_ids',
                'activity_ids',
                'message_partner_ids',
                'message_main_attachment_id',
                'is_entry_archive',
                'enable_portfolio_batch_action',
                'batch_portfolio_entry_ids',
                'batch_allowed_entry_ids',
                'batch_peer_count',
                'batch_selected_count',
            }
            business_keys = set(vals.keys()) - exempt_keys
            if business_keys:
                for rec in self:
                    if rec.is_entry_archive and not self.env.context.get('bypass_archive_check'):
                        raise UserError(_("This entry is archived. Editing or filling fields is blocked until the entry is unarchived."))
                        
        if vals.get('is_partners_screen') and 'partner_page_date' not in vals:
            vals['partner_page_date'] = fields.Datetime.now()
        if 'stage_id' in vals:
            now = fields.Datetime.now()
            new_stage = self.env['request.stage'].browse(vals['stage_id'])
            new_stage_sel = new_stage.project_stage_selection if new_stage else False
            for rec in self:
                if rec.stage_id and rec.stage_id.id != new_stage.id:
                    open_histories = rec.stage_history_ids.filtered(lambda h: not h.end_date)
                    if open_histories:
                        open_histories.write({'end_date': now})
                    if new_stage_sel not in ['completed', 'city_study_completed']:
                        # Detect return: moving BACKWARDS to any stage (new_stage.sequence < rec.stage_id.sequence)
                        is_return = False
                        if new_stage and rec.stage_id and new_stage.sequence < rec.stage_id.sequence:
                            old_sel = rec.stage_id.project_stage_selection
                            if (
                                (old_sel == 'contract_completion' and new_stage_sel == 'detailed_study_analyst')
                                or (old_sel == 'detailed_study_approval' and new_stage_sel == 'committee_decision')
                                or (new_stage_sel == 'data_completion' and not (rec.has_data_completion or rec.stage_history_ids.filtered(lambda h: h.stage_id.project_stage_selection == 'data_completion')))
                            ):
                                is_return = False
                            else:
                                is_return = True
                        self.env['entries.stage.history'].create({
                            'entry_id': rec.id,
                            'stage_id': new_stage.id,
                            'start_date': now,
                            'is_return': is_return,
                            'returned_by_user_id': self.env.uid if is_return else False,
                            'is_assign_detailed_study': vals.get('is_assign_detailed_study', rec.is_assign_detailed_study),
                            'committee_decision': vals.get('committee_decision', rec.committee_decision),
                        })
        # Capture original stages before writing to detect changes
        vals = self._sync_relation_selection_vals(dict(vals))
        original_stages = {rec.id: rec.stage_id.id for rec in self}
        original_pms = {rec.id: rec.assigned_project_manager.id for rec in self}
        original_direct_cms = {rec.id: rec.direct_sale_assigned_contract_manager.id for rec in self}
        original_auction_cms = {rec.id: rec.auction_assigned_contract_manager.id for rec in self}
        original_negotiators = {rec.id: rec.assigned_negotiator for rec in self}
        original_data_completers = {rec.id: rec.data_completer_id.id for rec in self}
        res = super().write(vals)
        # Notify authorized users when stage changes
        if 'stage_id' in vals:
            for rec in self:
                if rec.stage_id.id != original_stages.get(rec.id):
                    rec._notify_stage_authorized_users()
                    # When moved to negotiation_approval, notify the appropriate approval managers based on committee decision
                    if rec.project_stage_selection == 'negotiation_approval':
                        if rec.committee_decision == 'auction':
                            rec._notify_commercial_manager_auction_negotiation_approval()
                        else:
                            rec._notify_negotiation_approval_managers()
                    elif rec.project_stage_selection == 'contract_followup':
                        rec._notify_contract_followup_project_manager_assignment()
        if 'assigned_project_manager' in vals and vals.get('assigned_project_manager'):
            for rec in self:
                if rec.assigned_project_manager and rec.assigned_project_manager.id != original_pms.get(rec.id):
                    rec._notify_project_manager_assigned()
        if 'direct_sale_assigned_contract_manager' in vals and vals.get('direct_sale_assigned_contract_manager'):
            for rec in self:
                if rec.direct_sale_assigned_contract_manager and rec.direct_sale_assigned_contract_manager.id != original_direct_cms.get(rec.id):
                    rec._notify_contract_manager_assigned()
        if 'auction_assigned_contract_manager' in vals and vals.get('auction_assigned_contract_manager'):
            for rec in self:
                if rec.auction_assigned_contract_manager and rec.auction_assigned_contract_manager.id != original_auction_cms.get(rec.id):
                    rec._notify_contract_manager_assigned()
        if 'data_completer_id' in vals and vals.get('data_completer_id'):
            for rec in self:
                if rec.data_completer_id and rec.data_completer_id.id != original_data_completers.get(rec.id):
                    rec._notify_data_completer_assigned()
        for rec in self:
            old_neg = original_negotiators.get(rec.id)
            new_neg = rec.assigned_negotiator
            if old_neg != new_neg:
                if old_neg and new_neg and old_neg.id != new_neg.id:
                    rec._notify_negotiator_replaced(old_neg)
                    rec._notify_negotiator_assigned()
                elif not old_neg and new_neg:
                    rec._notify_negotiator_assigned()
                elif old_neg and not new_neg:
                    rec._notify_negotiator_replaced(old_neg)
        return res

    def _notify_stage_authorized_users(self):
        """Identify authorized users for the current stage and create activities for them."""
        self.ensure_one()
        if not self.stage_id:
            return

        # Always clear old activities when the stage changes
        self.create_mail_activity(users=False, is_done=True)

        # Exclude archive-flagged stages from creating new activities
        if self.is_entry_archive or self.is_deferred_opportunities_archive or self.is_listing_archive_2023 or self.is_technical_offers_archive:
            return

        users = self.env['res.users']

        # Notify only the assigned analyst for specific study stages
        if self.stage_id.project_stage_selection in ['detailed_study_eanfaz', 'detailed_study_analyst']:
            users = self.detailed_analyst_id
        elif self.stage_id.project_stage_selection == 'city_study_analyst':
            users = self.city_analyst_id
        elif self.stage_id.project_stage_selection == 'analyst':
            users = self.analyst_id
        elif self.stage_id.project_stage_selection == 'data_completion':
            users = self.data_completer_id
        elif self.stage_id.project_stage_selection == 'assign_negotiator':
            assign_neg_group = self.env.ref('bussma_system.group_assign_negotiator', raise_if_not_found=False)
            if assign_neg_group:
                users |= assign_neg_group.users
        else:
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

            self.create_mail_activity(users, summary=False, is_done=False)

    def create_mail_activity(self, users, summary=False, is_done=True):
        """Create Odoo activities for the specified users on this entry record."""
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
                self.env['mail.activity'].sudo().with_context(
                    mail_activity_quick_update=True,
                    mail_create_nosubscribe=True,
                ).create({
                    'summary': summary,
                    'activity_type_id': activity_type.id if activity_type else False,
                    'res_model_id': model_id,
                    'res_id': self.id,
                    'user_id': user.id,
                })
    
    @api.onchange('project_path_rel')
    def _onchange_project_path_rel(self):
        """Sync Many2one project_path_rel -> Selection project_path."""
        code = self.project_path_rel.code if self.project_path_rel else False
        self.project_path = code if code in ['cities', 'specialized', 'standard'] else False

    @api.onchange('project_path')
    def _onchange_project_path(self):
        """Sync Selection project_path -> Many2one project_path_rel."""
        if self.project_path:
            self.project_path_rel = self.env['project.path'].search([('code', '=', self.project_path)], limit=1)
        else:
            self.project_path_rel = False

    @api.onchange('customer_intent_rel')
    def _onchange_customer_intent_rel(self):
        """Sync Many2one customer_intent_rel -> Selection customer_intent."""
        code = self.customer_intent_rel.code if self.customer_intent_rel else False
        self.customer_intent = code if code in ['direct_sale', 'auction', 'select_all', 'studies_recommendation'] else False

    @api.onchange('customer_intent')
    def _onchange_customer_intent(self):
        """Sync Selection customer_intent -> Many2one customer_intent_rel."""
        if self.customer_intent:
            self.customer_intent_rel = self.env['customer.intent'].search([('code', '=', self.customer_intent)], limit=1)
        else:
            self.customer_intent_rel = False

    @api.onchange('committee_decision_rel')
    def _onchange_committee_decision_rel(self):
        """Sync Many2one committee_decision_rel -> Selection committee_decision."""
        code = self.committee_decision_rel.code if self.committee_decision_rel else False
        self.committee_decision = code if code in ['direct_sale', 'auction', 'exclusion'] else False
        if self.committee_decision_rel:
            self.committee_decision_date = fields.Date.today()

    @api.onchange('committee_decision')
    def _onchange_committee_decision(self):
        """Sync Selection committee_decision -> Many2one committee_decision_rel."""
        if self.committee_decision:
            self.committee_decision_rel = self.env['committee.decision.type'].search([('code', '=', self.committee_decision)], limit=1)
        else:
            self.committee_decision_rel = False

    @api.onchange('auctions_manager_approval_rel')
    def _onchange_auctions_manager_approval_rel(self):
        """Sync Many2one auctions_manager_approval_rel -> Selection auctions_manager_approval."""
        code = self.auctions_manager_approval_rel.code if self.auctions_manager_approval_rel else False
        self.auctions_manager_approval = code if code in ['committee_decision_accepted', 'committee_decision_rejected', 'request_transfer_auction'] else False

    @api.onchange('auctions_manager_approval')
    def _onchange_auctions_manager_approval(self):
        """Sync Selection auctions_manager_approval -> Many2one auctions_manager_approval_rel."""
        if self.auctions_manager_approval:
            self.auctions_manager_approval_rel = self.env['auction.manager.approval'].search([('code', '=', self.auctions_manager_approval)], limit=1)
        else:
            self.auctions_manager_approval_rel = False

    @api.onchange('sales_manager_approval_rel')
    def _onchange_sales_manager_approval_rel(self):
        """Sync Many2one sales_manager_approval_rel -> Selection sales_manager_approval."""
        code = self.sales_manager_approval_rel.code if self.sales_manager_approval_rel else False
        self.sales_manager_approval = code if code in ['committee_decision_accepted', 'committee_decision_rejected', 'request_transfer_direct_sale'] else False

    @api.onchange('sales_manager_approval')
    def _onchange_sales_manager_approval(self):
        """Sync Selection sales_manager_approval -> Many2one sales_manager_approval_rel."""
        if self.sales_manager_approval:
            self.sales_manager_approval_rel = self.env['sales.manager.approval'].search([('code', '=', self.sales_manager_approval)], limit=1)
        else:
            self.sales_manager_approval_rel = False

    @api.onchange('commercial_sector_manager_approval_rel')
    def _onchange_commercial_sector_manager_approval_rel(self):
        """Sync Many2one commercial_sector_manager_approval_rel -> Selection commercial_sector_manager_approval."""
        code = self.commercial_sector_manager_approval_rel.code if self.commercial_sector_manager_approval_rel else False
        self.commercial_sector_manager_approval = code if code in ['approval', 'return_committee', 'transfer', 'declined', 'postponed'] else False

    @api.onchange('commercial_sector_manager_approval')
    def _onchange_commercial_sector_manager_approval(self):
        """Sync Selection commercial_sector_manager_approval -> Many2one commercial_sector_manager_approval_rel."""
        if self.commercial_sector_manager_approval:
            self.commercial_sector_manager_approval_rel = self.env['commercial.sector.manager.approval'].search([('code', '=', self.commercial_sector_manager_approval)], limit=1)
        else:
            self.commercial_sector_manager_approval_rel = False

    def _apply_committee_prices_to_final_owner(self):
        for rec in self:
            if rec.final_owner_decision == 'committee_price':
                decision = rec.committee_decision or (rec.committee_decision_rel.code if rec.committee_decision_rel else False)
                if decision == 'direct_sale':
                    rec.final_owner_price_per_meter = rec.direct_sale_price_per_meter
                    rec.final_owner_price = rec.direct_sale_total_price
                elif decision == 'auction':
                    rec.final_owner_price_per_meter = rec.auction_price_per_meter
                    rec.final_owner_price = rec.auction_total_price

    @api.onchange('final_owner_decision_rel')
    def _onchange_final_owner_decision_rel(self):
        code = self.final_owner_decision_rel.code if self.final_owner_decision_rel else False
        self.final_owner_decision = code if code in ['committee_price', 'higher_price', 'rejected'] else False
        self._apply_committee_prices_to_final_owner()

    @api.onchange('standard_study_manager_approval_rel')
    def _onchange_standard_study_manager_approval_rel(self):
        code = self.standard_study_manager_approval_rel.code if self.standard_study_manager_approval_rel else False
        self.standard_study_manager_approval = code if code in ['completed', 'incomplete', 'reject_and_archive'] else False

    @api.onchange('standard_study_manager_approval')
    def _onchange_standard_study_manager_approval(self):
        if self.standard_study_manager_approval:
            self.standard_study_manager_approval_rel = self.env['standard.study.manager.approval'].search([('code', '=', self.standard_study_manager_approval)], limit=1)
        else:
            self.standard_study_manager_approval_rel = False

    @api.onchange('final_owner_decision')
    def _onchange_final_owner_decision(self):
        if self.final_owner_decision:
            self.final_owner_decision_rel = self.env['final.owner.decision'].search([('code', '=', self.final_owner_decision)], limit=1)
        else:
            self.final_owner_decision_rel = False
        self._apply_committee_prices_to_final_owner()

    @api.onchange('manager_negotiator_final_owner_decision')
    def _onchange_manager_negotiator_final_owner_decision(self):
        for rec in self:
            if rec.manager_negotiator_final_owner_decision == 'committee_price':
                decision = rec.committee_decision or (rec.committee_decision_rel.code if rec.committee_decision_rel else False)
                if decision == 'direct_sale':
                    rec.manager_negotiator_final_owner_price_per_meter = rec.direct_sale_price_per_meter
                    rec.manager_negotiator_final_owner_price = rec.direct_sale_total_price
                elif decision == 'auction':
                    rec.manager_negotiator_final_owner_price_per_meter = rec.auction_price_per_meter
                    rec.manager_negotiator_final_owner_price = rec.auction_total_price

    @api.model
    def _cron_check_direct_sale_contract_completion_timeout(self):
        """
        Cron job method to check entries in 'Contract Completion' stage with 'Direct Sale' decision.
        If the entry has been in 'Contract Completion' stage for more than 10 days,
        automatically return it to 'Negotiation Approval' stage and notify managers.
        """
        contract_completion_stage = self.env.ref('bussma_system.contract_completion', raise_if_not_found=False)
        negotiation_approval_stage = self.env.ref('bussma_system.negotiation_approval', raise_if_not_found=False)
        if not contract_completion_stage or not negotiation_approval_stage:
            _logger.warning("[Cron] Contract Completion or Negotiation Approval stage missing.")
            return
        now = fields.Datetime.now()
        threshold_date = now - timedelta(days=10)
        entries = self.search([
            ('stage_id', '=', contract_completion_stage.id),
            ('committee_decision', '=', 'direct_sale'),
            ('direct_sale_contract_status', '!=', 'yes'),
        ])
        for entry in entries:
            latest_history = entry.stage_history_ids.filtered(
                lambda h: h.stage_id.id == contract_completion_stage.id and not h.end_date
            )
            if not latest_history:
                latest_history = entry.stage_history_ids.filtered(
                    lambda h: h.stage_id.id == contract_completion_stage.id
                )

            start_dt = False
            if latest_history:
                start_dt = max(latest_history.mapped('start_date'))

            if start_dt and start_dt <= threshold_date:
                _logger.info(
                    "[Cron] Entry %s exceeded 10 days in Contract Completion stage. Returning to Negotiation Approval.",
                    entry.entrie_name
                )
                entry.write({
                    'stage_id': negotiation_approval_stage.id,
                    'negotiation_commercial_manager_approval': False,
                    'negotiation_studies_manager_approval': False,
                })
                # Notify Commercial Sector Manager and Studies Manager
                entry._notify_negotiation_approval_managers()

    def _notify_negotiation_approval_managers(self):
        """
        Notify Commercial Sector Manager and Studies Manager when a record is
        returned to 'Negotiation Approval' stage (either automatically or manually).
        Sends an email to each manager.
        """
        self.ensure_one()
        commercial_role = self.env.ref('bussma_system.role_commercial_sector_manager', raise_if_not_found=False)
        studies_role = self.env.ref('bussma_system.role_studies_manager', raise_if_not_found=False)

        role_ids = []
        if commercial_role:
            role_ids.append(commercial_role.id)
        if studies_role:
            role_ids.append(studies_role.id)
        if not role_ids:
            return
        role_lines = self.env['res.users.role.line'].sudo().search([
            ('role_id', 'in', role_ids)
        ])
        managers = role_lines.mapped('user_id')
        if not managers:
            return
        template = self.env.ref(
            'bussma_system.email_template_negotiation_approval_managers',
            raise_if_not_found=False
        )
        if not template:
            return
        for manager in managers:
            if not manager.email:
                continue
            try:
                template.send_mail(
                    self.id,
                    force_send=True,
                    email_values={
                        'email_to': manager.email,
                        'email_from': self.env.company.email or self.env.user.email,
                        'model': False,
                        'res_id': False,
                    }
                )
            except Exception as e:
                _logger.error("[Notify] Failed to send email to %s: %s", manager.email, str(e))

    def _notify_commercial_manager_auction_negotiation_approval(self):
        """
        Notify Commercial Sector Manager when an entry with 'auction' decision
        is moved to 'Negotiation Approval' stage.
        Sends an email using template email_template_auction_negotiation_approval_commercial_manager.
        """
        self.ensure_one()
        commercial_role = self.env.ref('bussma_system.role_commercial_sector_manager', raise_if_not_found=False)
        if not commercial_role:
            return

        role_lines = self.env['res.users.role.line'].sudo().search([
            ('role_id', '=', commercial_role.id)
        ])
        managers = role_lines.mapped('user_id')
        if not managers:
            return

        template = self.env.ref(
            'bussma_system.email_template_auction_negotiation_approval_commercial_manager',
            raise_if_not_found=False
        )
        if not template:
            _logger.warning("[Notify] Auction Negotiation Approval email template not found.")
            return

        for manager in managers:
            if not manager.email:
                continue
            try:
                template.send_mail(
                    self.id,
                    force_send=True,
                    email_values={
                        'email_to': manager.email,
                        'email_from': self.env.company.email or self.env.user.email,
                        'model': False,
                        'res_id': False,
                    }
                )
                _logger.info("[Notify] Auction Negotiation Approval email sent to Commercial Manager %s (%s)", manager.name, manager.email)
            except Exception as e:
                _logger.error("[Notify] Failed to send email to %s: %s", manager.email, str(e))

    def _notify_contract_followup_project_manager_assignment(self):
        """
        Notify Sales Manager or Auctions Manager (based on committee_decision)
        when an entry reaches the 'Contract Follow-up' stage to assign a Project Manager.
        Sends an email using template email_template_contract_followup_project_manager_assignment.
        """
        self.ensure_one()
        managers = self.env['res.users']
        if self.committee_decision == 'auction':
            auctions_group = self.env.ref('bussma_system.group_auctions_manager', raise_if_not_found=False)
            if auctions_group:
                managers |= auctions_group.users
        else:
            sales_group = self.env.ref('bussma_system.group_sales_manager', raise_if_not_found=False)
            if sales_group:
                managers |= sales_group.users

        if not managers:
            _logger.warning("[Notify] No manager found to notify for Project Manager assignment.")
            return

        # Create internal activity notification (shows badge counter in system)
        self.create_mail_activity(users=managers, summary=False, is_done=False)

        template = self.env.ref(
            'bussma_system.email_template_contract_followup_project_manager_assignment',
            raise_if_not_found=False
        )
        if not template:
            _logger.warning("[Notify] Project Manager Assignment email template not found.")
            return

        for manager in managers:
            if not manager.email:
                continue
            try:
                template.send_mail(
                    self.id,
                    force_send=True,
                    email_values={
                        'email_to': manager.email,
                        'email_from': self.env.company.email or self.env.user.email,
                        'model': False,
                        'res_id': False,
                    }
                )
                _logger.info("[Notify] Project Manager Assignment email sent to manager %s (%s)", manager.name, manager.email)
            except Exception as e:
                _logger.error("[Notify] Failed to send Project Manager Assignment email to %s: %s", manager.email, str(e))

    def _notify_data_completer_assigned(self):
        """
        Notify the assigned Data Completer when assigned or changed.
        Sends an email using template email_template_entry_data_completion.
        """
        for rec in self:
            completer = rec.data_completer_id
            if not completer:
                continue

            email_to = completer.email or completer.partner_id.email
            if not email_to:
                _logger.warning("[Notify] Data Completer %s has no email address.", completer.name)
                continue

            template = self.env.ref(
                'bussma_system.email_template_entry_data_completion',
                raise_if_not_found=False
            )
            if not template:
                _logger.warning("[Notify] Data Completion email template not found.")
                continue

            try:
                template.send_mail(
                    rec.id,
                    force_send=True,
                    email_values={
                        'email_to': email_to,
                        'email_from': rec.env.user.email or rec.env.company.email,
                        'model': False,
                        'res_id': False,
                    }
                )
                _logger.info("[Notify] Data Completion email sent to %s (%s)", completer.name, email_to)
            except Exception as e:
                _logger.error("[Notify] Failed to send Data Completion email to %s: %s", email_to, str(e))

    def _notify_project_manager_assigned(self):
        """
        Notify the assigned Project Manager when assigned to an entry.
        Sends an email using template email_template_project_manager_assigned
        and schedules an internal activity.
        """
        self.ensure_one()
        pm = self.assigned_project_manager
        if not pm:
            return

        # Create internal activity notification for assigned project manager
        self.create_mail_activity(users=pm, summary=False, is_done=False)

        if not pm.email:
            _logger.warning("[Notify] Project Manager %s has no email address.", pm.name)
            return

        template = self.env.ref(
            'bussma_system.email_template_project_manager_assigned',
            raise_if_not_found=False
        )
        if not template:
            _logger.warning("[Notify] Project Manager Assigned email template not found.")
            return

        try:
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': pm.email,
                    'email_from': self.env.company.email or self.env.user.email,
                    'model': False,
                    'res_id': False,
                }
            )
            _logger.info("[Notify] Project Manager Assigned email sent to %s (%s)", pm.name, pm.email)
        except Exception as e:
            _logger.error("[Notify] Failed to send Project Manager Assigned email to %s: %s", pm.email, str(e))

    def _notify_contract_manager_assigned(self):
        """
        Notify the assigned Contract Manager (direct sale or auction) when assigned to an entry.
        Sends an email using template email_template_contract_manager_assigned
        and schedules an internal activity.
        """
        self.ensure_one()
        cm = (
            self.auction_assigned_contract_manager
            if self.committee_decision == 'auction'
            else self.direct_sale_assigned_contract_manager
        )
        if not cm:
            return

        # Create internal activity notification for assigned contract manager
        self.create_mail_activity(users=cm, summary=False, is_done=False)

        if not cm.email:
            _logger.warning("[Notify] Contract Manager %s has no email address.", cm.name)
            return

        template = self.env.ref(
            'bussma_system.email_template_contract_manager_assigned',
            raise_if_not_found=False
        )
        if not template:
            _logger.warning("[Notify] Contract Manager Assigned email template not found.")
            return

        try:
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': cm.email,
                    'email_from': self.env.company.email or self.env.user.email,
                    'model': False,
                    'res_id': False,
                }
            )
            _logger.info("[Notify] Contract Manager Assigned email sent to %s (%s)", cm.name, cm.email)
        except Exception as e:
            _logger.error("[Notify] Failed to send Contract Manager Assigned email to %s: %s", cm.email, str(e))

    def _notify_negotiator_assigned(self):
        """
        Notify the assigned Negotiator when assigned to an entry.
        Sends an email using template email_template_negotiator_assigned
        and schedules an internal activity.
        """
        self.ensure_one()
        negotiator = self.assigned_negotiator
        if not negotiator:
            return

        # Create internal activity notification for assigned negotiator
        self.create_mail_activity(users=negotiator, summary=False, is_done=False)

        if not negotiator.email:
            _logger.warning("[Notify] Negotiator %s has no email address.", negotiator.name)
            return

        template = self.env.ref(
            'bussma_system.email_template_negotiator_assigned',
            raise_if_not_found=False
        )
        if not template:
            _logger.warning("[Notify] Negotiator Assigned email template not found.")
            return

        try:
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': negotiator.email,
                    'email_from': self.env.company.email or self.env.user.email,
                    'model': False,
                    'res_id': False,
                }
            )
            _logger.info("[Notify] Negotiator Assigned email sent to %s (%s)", negotiator.name, negotiator.email)
        except Exception as e:
            _logger.error("[Notify] Failed to send Negotiator Assigned email to %s: %s", negotiator.email, str(e))

    def _notify_negotiator_replaced(self, old_negotiator):
        """
        Notify the previous Negotiator that they have been replaced by another negotiator.
        Sends an email using template email_template_negotiator_replaced
        and clears their internal activity.
        """
        self.ensure_one()
        if not old_negotiator:
            return

        # Clear old negotiator's activities on this entry
        old_activities = self.env['mail.activity'].sudo().search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('user_id', '=', old_negotiator.id),
        ])
        if old_activities:
            old_activities.action_done()

        if not old_negotiator.email:
            _logger.warning("[Notify] Old Negotiator %s has no email address.", old_negotiator.name)
            return

        template = self.env.ref(
            'bussma_system.email_template_negotiator_replaced',
            raise_if_not_found=False
        )
        if not template:
            _logger.warning("[Notify] Negotiator Replaced email template not found.")
            return

        try:
            template.with_context(old_negotiator_name=old_negotiator.name).send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': old_negotiator.email,
                    'email_from': self.env.company.email or self.env.user.email,
                    'model': False,
                    'res_id': False,
                }
            )
            _logger.info("[Notify] Negotiator Replaced email sent to %s (%s)", old_negotiator.name, old_negotiator.email)
        except Exception as e:
            _logger.error("[Notify] Failed to send Negotiator Replaced email to %s: %s", old_negotiator.email, str(e))


    @api.model
    def web_search_read(self, domain=None, specification=None, offset=0, limit=None, order=None, count_limit=None):
        user = self.env.user
        domain = domain or []
        is_manager = user.has_group('base.group_system') or \
                     user.has_group('bussma_system.group_commercial_sector_manager') or \
                     user.has_group('bussma_system.group_auctions_manager') or \
                     user.has_group('bussma_system.group_sales_manager') or \
                     user.has_group('bussma_system.group_studies_manager') or \
                     user.has_group('bussma_system.group_deputy_studies_manager') or \
                     user.has_group('bussma_system.group_committee_member') or \
                     user.has_group('bussma_system.group_rnd_manager') or \
                     user.has_group('bussma_system.group_city_studies_manager') or \
                     user.has_group('bussma_system.group_assign_negotiator')

        if user.has_group('bussma_system.group_city_studies_manager') and not (
            user.has_group('bussma_system.group_studies_manager') or
            user.has_group('bussma_system.group_deputy_studies_manager') or
            user.has_group('base.group_system')
        ):
            domain = expression.AND([domain, [('project_path', '=', 'cities')]])

        if not self.env.context.get('bypass_entries_personal_domain'):
            is_entry_screen = self.env.context.get('is_entry_screen_action') or any(
                isinstance(term, (tuple, list)) and len(term) == 3 and term[0] == 'project_stage_selection' and term[2] == 'entry_screen'
                for term in (domain or [])
            )
            if is_entry_screen:
                if not user.has_group('base.group_system'):
                    domain = expression.AND([domain, [('create_uid', '=', user.id)]])
            else:
                is_study_menu = self.env.context.get('hide_personal_create_uid')
                if is_study_menu:
                    if not is_manager:
                        study_stages = [
                            'entry_screen',
                            'data_completion',
                            'define_project_path_assign_analyst',
                            'analyst',
                            'study_approval',
                            'detailed_study_analyst',
                            'detailed_study_approval',
                            'city_study_analyst',
                            'city_study_approval',
                        ]
                        eanfaz_stages = [
                            'studies_supervisor_eanfaz',
                            'detailed_study_eanfaz',
                            'detailed_study_approval_eanfaz',
                        ]
                        study_menu_domain = [
                            '|', '|', '|', '|', '|',
                            ('assigned_project_manager', '=', user.id),
                            '&', '&',
                            ('assigned_negotiator', '=', user.id),
                            ('project_stage_selection', '=', 'negotiator'),
                            ('is_sent_to_deputy_studies_manager', '=', False),
                            ('direct_sale_assigned_contract_manager', '=', user.id),
                            ('auction_assigned_contract_manager', '=', user.id),
                            '&',
                            ('project_stage_selection', 'in', study_stages),
                            '|', '|',
                            ('analyst_id', '=', user.id),
                            ('detailed_analyst_id', '=', user.id),
                            ('city_analyst_id', '=', user.id),
                            '&',
                            ('project_stage_selection', 'in', eanfaz_stages),
                            ('detailed_analyst_id', '=', user.id),
                        ]
                        domain = expression.AND([domain, study_menu_domain])
                else:
                    if not is_manager:
                        my_domain = [
                            '|', '|', '|', '|', '|',
                            ('assigned_project_manager', '=', user.id),
                            ('create_uid', '=', user.id),
                            '&',
                            ('data_completer_id', '=', user.id),
                            ('project_stage_selection', '=', 'data_completion'),
                            '&', '&',
                            ('assigned_negotiator', '=', user.id),
                            ('project_stage_selection', '=', 'negotiator'),
                            ('is_sent_to_deputy_studies_manager', '=', False),
                            ('direct_sale_assigned_contract_manager', '=', user.id),
                            ('auction_assigned_contract_manager', '=', user.id)
                        ]
                        domain = expression.AND([domain, my_domain])

        return super().web_search_read(
            domain=domain,
            specification=specification,
            offset=offset,
            limit=limit,
            order=order,
            count_limit=count_limit
        )

    def web_read(self, specification):
        user = self.env.user
        is_manager_or_analyst = user.has_group('bussma_system.group_analyst') or \
                                user.has_group('bussma_system.group_studies_manager') or \
                                user.has_group('bussma_system.group_deputy_studies_manager') or \
                                user.has_group('bussma_system.group_rnd_manager') or \
                                user.has_group('bussma_system.group_sales_manager') or \
                                user.has_group('bussma_system.group_auctions_manager') or \
                                user.has_group('bussma_system.group_commercial_sector_manager') or \
                                user.has_group('bussma_system.group_negotiator') or \
                                user.has_group('bussma_system.group_contract_manager') or \
                                user.has_group('bussma_system.group_assign_negotiator') or \
                                user.has_group('bussma_system.group_city_studies_manager') or \
                                user.has_group('base.group_system') or \
                                any(rec.assigned_project_manager == user or (rec.data_completer_id == user and rec.project_stage_selection == 'data_completion') for rec in self)

        if user.has_group('bussma_system.group_city_studies_manager') and not (
            user.has_group('bussma_system.group_studies_manager') or
            user.has_group('bussma_system.group_deputy_studies_manager') or
            user.has_group('base.group_system')
        ):
            if any(rec.project_path != 'cities' for rec in self):
                if self.env.context.get('view_type') == 'form' or self.env.context.get('params', {}).get('view_type') == 'form':
                    raise UserError(_("Don't have permission to open this record"))
        if not is_manager_or_analyst:
            if self.env.context.get('view_type') == 'form' or self.env.context.get('params', {}).get('view_type') == 'form':
                raise UserError(_("Don't have permission to open this record"))
        return super().web_read(specification)

    def unlink(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        if not is_admin:
            raise UserError(_("Don't have permission to delete this record"))
        return super().unlink()
