# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class BussmaProject(models.Model):
    _name = 'bussma.project'
    _inherit = ['request', 'mail.thread', 'mail.activity.mixin']
    _description = 'Bussma Project'
    _rec_names_search = ['name', 'code']

    def _default_request_type_id(self):
        ctx_type = self.env.context.get('default_project_type')
        type_xml_map = {
            'sales': 'sales_and_auction_management.bussma_project_type_sales',
            'auction_pvt': 'sales_and_auction_management.bussma_project_type_auction_pvt',
            'city': 'sales_and_auction_management.bussma_project_type_auction_city',
            'auction_enf': 'sales_and_auction_management.bussma_project_type_auction_enf',
        }
        if ctx_type and ctx_type in type_xml_map:
            return self.env.ref(type_xml_map[ctx_type], raise_if_not_found=False)
        return False

    def _default_stage_id(self):
        ctx_type = self.env.context.get('default_project_type')
        stage_xml_map = {
            'sales': 'sales_and_auction_management.bussma_project_stage_sales_pm',
            'auction_pvt': 'sales_and_auction_management.bussma_project_stage_pvt_pm',
            'city': 'sales_and_auction_management.bussma_project_stage_city_pm',
            'auction_enf': 'sales_and_auction_management.bussma_project_stage_enf_pm',
        }
        if ctx_type and ctx_type in stage_xml_map:
            return self.env.ref(stage_xml_map[ctx_type], raise_if_not_found=False)
        req_type = self._default_request_type_id()
        if req_type:
            return self.env['request.stage'].search(
                [('res_model', '=', 'bussma.project'), ('request_type_ids', 'in', req_type.id)],
                order='sequence asc', limit=1
            )
        return False

    @api.model
    def _read_group_stage_ids(self, stages, domain=None, order=None):
        all_stages = self.env['request.stage'].search(
            [('res_model', '=', 'bussma.project')], order='sequence asc'
        )
        request_type_id = None
        if domain:
            for leaf in domain:
                if isinstance(leaf, (list, tuple)) and len(leaf) == 3:
                    if leaf[0] == 'request_type_id' and leaf[1] == '=':
                        request_type_id = leaf[2]
                        break
        if request_type_id:
            return all_stages.filtered(
                lambda s: not s.hide_on_flag or request_type_id in s.request_type_ids.ids
            )
        return all_stages.filtered(lambda s: not s.hide_on_flag)

    request_type_id = fields.Many2one(
        'request.type',
        string='Request Type',
        default=_default_request_type_id,
        tracking=True
    )
    stage_id = fields.Many2one(
        'request.stage',
        string='Stage',
        default=_default_stage_id,
        group_expand='_read_group_stage_ids',
        domain=lambda self: (
            "[('res_model', '=', 'bussma.project'),"
            "'|', ('hide_on_flag', '=', False),"
            "     ('request_type_ids', '=', request_type_id)]"
        ),
        tracking=True
    )
    bussma_project_stage_selection = fields.Selection(
        related='stage_id.bussma_project_stage_selection',
        string='Bussma Project Stage Selection',
        store=True
    )
    name = fields.Char(string='Project Name', required=True, tracking=True)
    code = fields.Char(string='Project Code', required=True, copy=False, readonly=True, default=lambda self: '/')
    project_type = fields.Selection([
        ('sales', 'Sales'),
        ('auction_pvt', 'Auctions - Private'),
        ('auction_enf', 'Auctions - Eanfaz'),
        ('city', 'City'),
    ], string='Project Type', required=True)
    project_category = fields.Selection([
        ('portfolio', 'Portfolio'),
        ('scheme', 'Scheme'),
        ('single', 'Single'),
        ('cities', 'Cities'),
    ], tracking=True, string='Project Category')
    active = fields.Boolean(default=True)
    is_basic = fields.Boolean(string='Is Basic Portfolio', default=False)

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields=allfields, attributes=attributes)
        if res and 'active' in res:
            res['active']['readonly'] = True
            res['active']['invisible'] = True
        return res

    entry_ids = fields.One2many(
        'sales.auction.management',
        compute='_compute_entry_ids',
        string='Properties'
    )
    entries_count = fields.Integer(string='Properties Count', compute='_compute_entries_count')
    transferred_entry_ids = fields.Many2many(
        'sales.auction.management',
        'bussma_project_transferred_entries_rel',
        'project_id',
        'sales_id',
        string='Transferred Properties'
    )
    transferred_entries_count = fields.Integer(
        string='Transferred Properties Count',
        compute='_compute_transferred_entries_count'
    )
    project_manager_id = fields.Many2one('res.users', string='Project Manager')
    basic_project_type = fields.Selection([
        ('sales', 'Basic Sales'),
        ('auction_pvt', 'Basic Auctions Private'),
        ('auction_enf', 'Basic Auctions Eanfaz'),
        ('city', 'Basic City'),
    ], string='Basic Project Type', compute='_compute_basic_project_type')
    # ============================================================
    # Government Auction (Eanfaz) Information Fields
    # ============================================================
    # Auction Category
    auction_category = fields.Selection([
        ('vip', 'VIP'),
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
    ], string='Auction Category')
    # Does it require an ID?
    need_identity = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Need Identity')
    # Asset Number
    asset_number = fields.Char(string='Asset Number')
    # Court Decision Number
    court_decision_number = fields.Char(string='Court Decision Number')
    # Execution Applicant Name
    execution_applicant_name = fields.Char(string='Execution Applicant Name')
    # Execution Applicant Phone
    execution_applicant_phone = fields.Char(string='Execution Applicant Phone')
    # Deed Number
    deed_number = fields.Char(string='Deed Number')
    # Deed Date (Hijri)
    deed_date_hijri = fields.Char(string='Deed Date (Hijri)')
    # Deed Issuing Authority
    deed_issuer = fields.Char(string='Deed Issuer')
    # Plan Number
    plan_number = fields.Char(string='Plan Number')
    # Plot Number
    plot_number = fields.Char(string='Plot Number')
    # City
    city = fields.Many2one(
        'res.country.state',
        string='City',
        domain="[('country_id.code', '=', 'SA'), ('code', 'ilike', 'CT_')]"
    )
    # District
    district_id = fields.Many2one('res.city', string='District', domain="[('state_id', '=', city)]")
    # Property Type
    property_type = fields.Many2one('property.type', string='Property Type')
    # Area (SQM)
    area_sqm = fields.Float(string='Area (m²)')
    # Location URL
    location_url = fields.Char(string='Location URL')
    # Boundaries (North)
    limit_north = fields.Char(string='Limit (North)')
    length_north = fields.Float(string='Length (North)')
    # Boundaries (South)
    limit_south = fields.Char(string='Limit (South)')
    length_south = fields.Float(string='Length (South)')
    # Boundaries (East)
    limit_east = fields.Char(string='Limit (East)')
    length_east = fields.Float(string='Length (East)')
    # Boundaries (West)
    limit_west = fields.Char(string='Limit (West)')
    length_west = fields.Float(string='Length (West)')
    # Property Description
    property_description = fields.Text(string='Property Description')
    # Property Images URL
    property_images_url = fields.Char(string='Property Images URL')
    # Project Notes
    project_notes = fields.Text(string='Project Notes')
    # Lease Contract Type
    lease_contract_type = fields.Selection([
        ('electronic', 'Electronic'),
        ('normal', 'Normal'),
        ('not_applicable', 'Not Applicable'),
    ], string='Lease Contract Type')
    # Has Operation Contract
    has_operation_contract = fields.Boolean(string='Has Operation Contract')
    # Lease Contract Expiry Date
    lease_contract_expiry_date = fields.Date(string='Lease Contract Expiry Date')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    # Project Management Fields (Auction & Sales)
    project_cat = fields.Selection([
        ('vip', 'VIP'),
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
    ], string='Project Category')
    wallet_recharge_amount = fields.Monetary(string='Wallet Recharge Amount', currency_field='currency_id')
    auction_type = fields.Selection([
        ('onsite', 'Onsite'),
        ('online', 'Online'),
        ('hybrid', 'Hybrid'),
    ], string='Auction Type')
    auction_date = fields.Date(string='Auction Date')
    auction_start_time = fields.Datetime(string='Auction Start Time')
    auction_end_time = fields.Datetime(string='Auction End Time')
    platform_extra_notification = fields.Boolean(string='Platform Extra Notification')
    # Project Dates & Duration
    project_start_date = fields.Date(string="Project Start Date")
    project_end_date = fields.Date(string="Project End Date")
    project_duration = fields.Integer(string="Project Duration (Days)", compute="_compute_project_duration", store=True)
    # Direct Sales Project Status
    sales_project_status = fields.Selection([
        ('not_started', 'Not Started'),
        ('negotiating', 'Negotiating'),
        ('for_sale', 'For Sale'),
        ('reserved', 'Reserved'),
        ('fully_sold', 'Fully Sold'),
        ('partially_sold', 'Partially Sold'),
        ('excluded', 'Excluded'),
        ('on_hold', 'On Hold'),
    ], string='Sales Project Status', tracking=True)
    # Project Manager Notes
    project_manager_notes = fields.Text(string='Project Manager Notes')

    @api.depends('project_start_date', 'project_end_date')
    def _compute_project_duration(self):
        for rec in self:
            if rec.project_start_date and rec.project_end_date:
                delta = rec.project_end_date - rec.project_start_date
                rec.project_duration = delta.days
            else:
                rec.project_duration = 0

    @api.onchange('project_type')
    def _onchange_project_type_set_stage_type(self):
        type_xml_map = {
            'sales': 'sales_and_auction_management.bussma_project_type_sales',
            'auction_pvt': 'sales_and_auction_management.bussma_project_type_auction_pvt',
            'city': 'sales_and_auction_management.bussma_project_type_auction_city',
            'auction_enf': 'sales_and_auction_management.bussma_project_type_auction_enf',
        }
        stage_xml_map = {
            'sales': 'sales_and_auction_management.bussma_project_stage_sales_pm',
            'auction_pvt': 'sales_and_auction_management.bussma_project_stage_pvt_pm',
            'city': 'sales_and_auction_management.bussma_project_stage_city_pm',
            'auction_enf': 'sales_and_auction_management.bussma_project_stage_enf_pm',
        }
        if self.project_type and self.project_type in type_xml_map:
            req_type = self.env.ref(type_xml_map[self.project_type], raise_if_not_found=False)
            if req_type:
                self.request_type_id = req_type
            stage = self.env.ref(stage_xml_map[self.project_type], raise_if_not_found=False)
            if stage:
                self.stage_id = stage

    def _check_pm_stage_mandatory_fields(self):
        """
        Validate mandatory fields before advancing project to Sales & Finance stage.
        Separated validation method called by action_move_to_sales_fin.
        """
        self.ensure_one()
        mandatory = []
        if self.project_type == 'sales':
            mandatory = [
                'sales_project_status',
                'project_start_date',
                'project_end_date',
            ]
        else:
            mandatory = [
                'auction_category',
                'project_cat',
                'need_identity',
                'wallet_recharge_amount',
                'auction_date',
                'auction_type',
                'project_start_date',
                'project_end_date',
            ]
            if self.auction_type in ['online', 'hybrid']:
                mandatory.extend(['auction_start_time', 'auction_end_time'])

        missing = [f for f in mandatory if not getattr(self, f)]
        if missing:
            field_labels = self.fields_get(missing)
            labels = [field_labels[f]['string'] for f in missing]
            raise UserError(_(
                "Please fill in the following mandatory fields before proceeding:\n- %s"
            ) % "\n- ".join(labels))

    def _move_linked_properties_to_buyer_contracting(self):
        """
        Moves all linked properties currently in PM stage to Buyer Contracting stage (p2_stage_shared_buyer_contracting).
        """
        buyer_contracting_stage = self.env.ref(
            'sales_and_auction_management.p2_stage_shared_buyer_contracting',
            raise_if_not_found=False
        )
        if not buyer_contracting_stage:
            return
        
        pm_stage_selections = [
            'p2_auction_pvt_portfolio',
            'p2_auction_enf_pm_appr',
            'p2_auction_city_portfolio',
            'p2_sales_direct_mgmt'
        ]
        for project in self:
            properties_to_move = project.entry_ids.filtered(
                lambda p: p.sales_auction_stage_selection in pm_stage_selections
            )
            if properties_to_move:
                properties_to_move.write({
                    'stage_id': buyer_contracting_stage.id,
                    'is_not_move_to_sale_fin_notes': False
                })

    def action_move_to_sales_fin(self):
        """
        Move project to Sales and Finance stage after validating mandatory fields,
        and move all linked properties in PM stage to Buyer Contracting stage.
        """
        self.ensure_one()
        self._check_pm_stage_mandatory_fields()
        stage = self.env.ref(
            'sales_and_auction_management.bussma_project_stage_sales_fin',
            raise_if_not_found=False
        )
        if not stage:
            stage = self.env['request.stage'].search([
                ('res_model', '=', 'bussma.project'),
                ('bussma_project_stage_selection', '=', 'bussma_project_sales_fin')
            ], limit=1)
        if stage:
            self.stage_id = stage

        self._move_linked_properties_to_buyer_contracting()

    @api.model
    def _cron_move_project_to_buyer_contracting(self):
        """
        Cron method on bussma.project:
        Finds non-basic auction projects in PM stage where auction_date <= today,
        validates mandatory fields, moves project to Sales and Finance stage,
        and moves all linked properties in PM stage to Buyer Contracting stage.
        """
        today = fields.Date.today()
        pm_stage_selections = [
            'bussma_project_pvt_pm',
            'bussma_project_city_pm',
            'bussma_project_enf_pm'
        ]
        projects = self.search([
            ('is_basic', '=', False),
            ('project_type', 'in', ['auction_pvt', 'city', 'auction_enf']),
            ('bussma_project_stage_selection', 'in', pm_stage_selections),
            ('auction_date', '<=', today),
        ])
        for proj in projects:
            try:
                proj._check_pm_stage_mandatory_fields()
            except Exception:
                continue
            
            stage = self.env.ref(
                'sales_and_auction_management.bussma_project_stage_sales_fin',
                raise_if_not_found=False
            )
            if stage:
                proj.stage_id = stage
            proj._move_linked_properties_to_buyer_contracting()

    def action_move_to_completed(self):
        """
        Move project to Completed stage.
        """
        self.ensure_one()
        stage = self.env.ref(
            'sales_and_auction_management.bussma_project_stage_completed',
            raise_if_not_found=False
        )
        if not stage:
            stage = self.env['request.stage'].search([
                ('res_model', '=', 'bussma.project'),
                ('bussma_project_stage_selection', '=', 'bussma_project_completed')
            ], limit=1)
        if stage:
            self.stage_id = stage

    def action_return_to_project_management(self):
        """
        Return project from Sales & Finance stage back to its corresponding Project Management stage.
        """
        self.ensure_one()
        pm_stage_xml_map = {
            'sales': 'sales_and_auction_management.bussma_project_stage_sales_pm',
            'auction_pvt': 'sales_and_auction_management.bussma_project_stage_pvt_pm',
            'city': 'sales_and_auction_management.bussma_project_stage_city_pm',
            'auction_enf': 'sales_and_auction_management.bussma_project_stage_enf_pm',
        }
        xml_id = pm_stage_xml_map.get(self.project_type)
        stage = self.env.ref(xml_id, raise_if_not_found=False) if xml_id else False
        if not stage and self.request_type_id:
            stage = self.env['request.stage'].search([
                ('res_model', '=', 'bussma.project'),
                ('request_type_ids', 'in', self.request_type_id.id)
            ], order='sequence asc', limit=1)
        if stage:
            self.stage_id = stage

    def action_return_to_sales_fin(self):
        """
        Return project from Completed stage back to Sales & Finance stage.
        """
        self.ensure_one()
        stage = self.env.ref(
            'sales_and_auction_management.bussma_project_stage_sales_fin',
            raise_if_not_found=False
        )
        if not stage:
            stage = self.env['request.stage'].search([
                ('res_model', '=', 'bussma.project'),
                ('bussma_project_stage_selection', '=', 'bussma_project_sales_fin')
            ], limit=1)
        if stage:
            self.stage_id = stage

    @api.depends('name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name

    def _compute_entry_ids(self):
        sales_basic = self.env.ref('sales_and_auction_management.project_sales_basic', raise_if_not_found=False)
        pvt_basic = self.env.ref('sales_and_auction_management.project_auctions_pvt_basic', raise_if_not_found=False)
        enf_basic = self.env.ref('sales_and_auction_management.project_auctions_enf_basic', raise_if_not_found=False)
        city_basic = self.env.ref('sales_and_auction_management.project_cities_basic', raise_if_not_found=False)
        basic_projects = {
            'sales': sales_basic,
            'auction_pvt': pvt_basic,
            'auction_enf': enf_basic,
            'city': city_basic,
        }
        basic_ids = [p.id for p in basic_projects.values() if p]
        
        sales_type = self.env.ref('sales_and_auction_management.p2_type_sales', raise_if_not_found=False)
        enf_type = self.env.ref('sales_and_auction_management.p2_type_auction_enf', raise_if_not_found=False)
        pvt_type = self.env.ref('sales_and_auction_management.p2_type_auction_pvt', raise_if_not_found=False)
        city_type = self.env.ref('sales_and_auction_management.p2_type_auction_city', raise_if_not_found=False)
        
        for project in self:
            is_basic = project.id in basic_ids
            if is_basic:
                domain = [('project_id', '=', project.id), ('sales_auction_stage_selection', 'not in', ['p2_shared_archive', 'p2_sales_archive'])]
                project.entry_ids = self.env['sales.auction.management'].search(domain)
            else:
                project.entry_ids = self.env['sales.auction.management'].search([('project_id', '=', project.id)])

    def _compute_basic_project_type(self):
        sales_basic = self.env.ref('sales_and_auction_management.project_sales_basic', raise_if_not_found=False)
        pvt_basic = self.env.ref('sales_and_auction_management.project_auctions_pvt_basic', raise_if_not_found=False)
        enf_basic = self.env.ref('sales_and_auction_management.project_auctions_enf_basic', raise_if_not_found=False)
        city_basic = self.env.ref('sales_and_auction_management.project_cities_basic', raise_if_not_found=False)
        sales_id = sales_basic.id if sales_basic else False
        pvt_id = pvt_basic.id if pvt_basic else False
        enf_id = enf_basic.id if enf_basic else False
        city_id = city_basic.id if city_basic else False
        
        for rec in self:
            if rec.id == sales_id:
                rec.basic_project_type = 'sales'
            elif rec.id == pvt_id:
                rec.basic_project_type = 'auction_pvt'
            elif rec.id == enf_id:
                rec.basic_project_type = 'auction_enf'
            elif rec.id == city_id:
                rec.basic_project_type = 'city'
            else:
                rec.basic_project_type = False

    def action_send_all_to_supervisor(self):
        """
        Eanfaz Project: Validate mandatory fields on the project, then move
        all linked properties that are at stage p2_auction_enf_project_manager
        to the Studies Supervisor stage (p2_auction_enf_supervisor).
        Triggered from the project form by the Auctions PM role.
        """
        self.ensure_one()
        if self.project_type != 'auction_enf':
            raise UserError(_("This action is only for Eanfaz projects."))
        # ── Validate mandatory project-level fields ──────────────────────────
        self._check_pm_mandatory_fields()
        pm_stage = self.env.ref(
            'sales_and_auction_management.p2_auction_enf_project_manager', raise_if_not_found=False
        )
        supervisor_stage = self.env.ref(
            'sales_and_auction_management.p2_auction_enf_supervisor', raise_if_not_found=False
        )
        if not pm_stage or not supervisor_stage:
            raise UserError(_("Define stages not found. Please contact the admin."))
        # ── Find all linked properties at the PM stage or Portfolio stage ────
        properties = self.env['sales.auction.management'].search([
            ('project_id', '=', self.id),
            ('sales_auction_stage_selection', 'in', ['p2_auction_enf_project_manager', 'p2_auction_enf_portfolio']),
        ])
        if not properties:
            raise UserError(_("No properties found in stage 'Project Manager' or 'Portfolio' linked to this project."))
        # ── Advance stage for each property ─────────
        for prop in properties:
            prop._create_detailed_study_eanfaz()
            prop.write({
                # advance stage & clear return notes
                'stage_id':             supervisor_stage.id,
                'analyst_return_notes': False,
            })

    def _check_pm_mandatory_fields(self):
        """
        Validate that all Government Auction Information fields are filled
        on the project before sending properties to the Studies Supervisor.
        """
        self.ensure_one()
        mandatory = [
            'auction_category', 'need_identity',
            'asset_number', 'court_decision_number',
            'execution_applicant_name', 'execution_applicant_phone',
            'deed_number', 'deed_date_hijri', 'deed_issuer',
            'plan_number', 'plot_number',
            'city', 'district_id', 'property_type', 'area_sqm', 'location_url',
            'limit_north', 'length_north', 'limit_south', 'length_south',
            'limit_east', 'length_east', 'limit_west', 'length_west',
            'property_description', 'property_images_url', 'project_notes',
            'lease_contract_type', 'lease_contract_expiry_date',
            'project_manager_notes',
        ]
        missing = [f for f in mandatory if not getattr(self, f)]
        if missing:
            labels = [self.fields_get(missing)[f]['string'] for f in missing]
            raise UserError(_(
                "Please fill in the following fields in the project before sending:\n- %s"
            ) % "\n- ".join(labels))

    def action_add_new_eanfaz_property(self):
        self.ensure_one()
        enf_type = self.env.ref('sales_and_auction_management.p2_type_auction_enf', raise_if_not_found=False)
        enf_stage = self.env.ref('sales_and_auction_management.p2_auction_enf_portfolio', raise_if_not_found=False)
        view_id = self.env.ref('sales_and_auction_management.view_entries_eanfaz_form', raise_if_not_found=False)
        return {
            'name': _('Create New Enforcement Property'),
            'type': 'ir.actions.act_window',
            'res_model': 'sales.auction.management',
            'view_mode': 'form',
            'view_id': view_id.id if view_id else False,
            'views': [(view_id.id if view_id else False, 'form')],
            'context': {
                'default_project_id': self.id,
                'default_auction_project_path': 'enforcement',
                'default_amount_matches_selling_price': True,
                'default_request_type_id': enf_type.id if enf_type else False,
                'default_stage_id': enf_stage.id if enf_stage else False,
            },
            'target': 'current',
        }

    @api.depends('entry_ids')
    def _compute_entries_count(self):
        for rec in self:
            rec.entries_count = len(rec.entry_ids)

    def action_view_properties(self):
        self.ensure_one()
        sales_basic = self.env.ref('sales_and_auction_management.project_sales_basic', raise_if_not_found=False)
        pvt_basic = self.env.ref('sales_and_auction_management.project_auctions_pvt_basic', raise_if_not_found=False)
        enf_basic = self.env.ref('sales_and_auction_management.project_auctions_enf_basic', raise_if_not_found=False)
        city_basic = self.env.ref('sales_and_auction_management.project_cities_basic', raise_if_not_found=False)
        basic_ids = [p.id for p in [sales_basic, pvt_basic, enf_basic, city_basic] if p]
        is_basic = self.id in basic_ids
        
        action_xml_id = False
        if self.project_type == 'auction_enf':
            action_xml_id = 'sales_and_auction_management.action_entries_auctions_enf_portfolio' if is_basic else 'sales_and_auction_management.action_entries_auctions_enf'
        elif self.project_type == 'sales':
            action_xml_id = 'sales_and_auction_management.action_entries_sales_portfolio' if is_basic else 'sales_and_auction_management.action_entries_sales'
        elif self.project_type == 'auction_pvt':
            action_xml_id = 'sales_and_auction_management.action_entries_pvt_portfolio' if is_basic else 'sales_and_auction_management.action_entries_pvt'
        elif self.project_type == 'city':
            action_xml_id = 'sales_and_auction_management.action_entries_auctions_city_portfolio' if is_basic else 'sales_and_auction_management.action_entries_auctions_city'
        if action_xml_id:
            action = self.env['ir.actions.act_window']._for_xml_id(action_xml_id)
            # Safely evaluate domain
            current_domain = action.get('domain')
            if isinstance(current_domain, str):
                from odoo.tools.safe_eval import safe_eval
                try:
                    current_domain = safe_eval(current_domain, {'ref': self.env.ref, 'active_id': self.id})
                except Exception:
                    current_domain = []
            if not isinstance(current_domain, list):
                current_domain = []
            
            if is_basic:
                new_domain = expression.AND([current_domain, [('project_id', '=', self.id), ('sales_auction_stage_selection', 'not in', ['p2_shared_archive', 'p2_sales_archive'])]])
            else:
                new_domain = [('project_id', '=', self.id)]
            
            action['domain'] = new_domain
            
            # Safely evaluate context
            ctx = dict(self.env.context)
            action_ctx = action.get('context')
            if isinstance(action_ctx, str):
                from odoo.tools.safe_eval import safe_eval
                try:
                    action_ctx = safe_eval(action_ctx, {'ref': self.env.ref, 'active_id': self.id})
                except Exception:
                    action_ctx = {}
            if isinstance(action_ctx, dict):
                ctx.update(action_ctx)
                
            ctx.update({
                'default_project_id': self.id,
                'search_default_group_by_stage': 1,
            })
            action['context'] = ctx
            return action
            
        fallback_domain = [('project_id', '=', self.id)]

        return {
            'name': 'Properties',
            'type': 'ir.actions.act_window',
            'res_model': 'sales.auction.management',
            'view_mode': 'kanban,form',
            'domain': fallback_domain,
            'context': {'default_project_id': self.id, 'create': False, 'search_default_group_by_stage': 1},
            'target': 'current',
        }

    @api.depends('transferred_entry_ids')
    def _compute_transferred_entries_count(self):
        for rec in self:
            rec.transferred_entries_count = len(rec.transferred_entry_ids)

    def action_dummy_pass(self):
        """Dummy action for stat button that does nothing when clicked."""
        pass

    def action_view_transferred_entries(self):
        self.ensure_one()
        kanban_view = self.env.ref('sales_and_auction_management.view_transferred_entries_kanban', raise_if_not_found=False)
        list_view = self.env.ref('sales_and_auction_management.view_entries_assign_project_list', raise_if_not_found=False)

        views = []
        if kanban_view:
            views.append((kanban_view.id, 'kanban'))
        if list_view:
            views.append((list_view.id, 'list'))

        return {
            'name': _('Transferred / Referred Properties - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sales.auction.management',
            'view_mode': 'kanban,list,form',
            'views': views,
            'domain': [('id', 'in', self.transferred_entry_ids.ids)],
            'context': {
                'active_project_id': self.id,
                'create': False,
                'delete': False,
            },
            'target': 'current',
        }

    def action_open_assign_wizard(self):
        self.ensure_one()
        assign_list_view = self.env.ref(
            'sales_and_auction_management.view_entries_assign_project_list',
            raise_if_not_found=False,
        )
        # Build the domain depending on project_type
        domain = []
        if self.project_type == 'sales':
            sales_basic = self.env.ref('sales_and_auction_management.project_sales_basic', raise_if_not_found=False)
            sales_type = self.env.ref('sales_and_auction_management.p2_type_sales', raise_if_not_found=False)
            allowed_projects = [False]
            if sales_basic:
                allowed_projects.append(sales_basic.id)
            domain.extend([
                ('project_id', 'in', allowed_projects),
                ('request_type_id', '=', sales_type.id if sales_type else False),
            ])
        elif self.project_type == 'auction_pvt':
            pvt_basic = self.env.ref('sales_and_auction_management.project_auctions_pvt_basic', raise_if_not_found=False)
            pvt_type = self.env.ref('sales_and_auction_management.p2_type_auction_pvt', raise_if_not_found=False)
            allowed_projects = [False]
            if pvt_basic:
                allowed_projects.append(pvt_basic.id)
            domain.extend([
                ('project_id', 'in', allowed_projects),
                ('request_type_id', '=', pvt_type.id if pvt_type else False),
                ('auction_project_path', '=', 'private'),
                ('sales_auction_stage_selection', '=', 'p2_auction_pvt_portfolio')
            ])
        elif self.project_type == 'auction_enf':
            enf_basic = self.env.ref('sales_and_auction_management.project_auctions_enf_basic', raise_if_not_found=False)
            enf_type = self.env.ref('sales_and_auction_management.p2_type_auction_enf', raise_if_not_found=False)
            allowed_projects = [False]
            if enf_basic:
                allowed_projects.append(enf_basic.id)
            domain.extend([
                ('project_id', 'in', allowed_projects),
                ('request_type_id', '=', enf_type.id if enf_type else False),
                ('sales_auction_stage_selection', '=', 'p2_auction_enf_portfolio')
            ])
        elif self.project_type == 'city':
            city_basic = self.env.ref('sales_and_auction_management.project_cities_basic', raise_if_not_found=False)
            city_type = self.env.ref('sales_and_auction_management.p2_type_auction_city', raise_if_not_found=False)
            allowed_projects = [False]
            if city_basic:
                allowed_projects.append(city_basic.id)
            domain.extend([
                ('project_id', 'in', allowed_projects),
                ('request_type_id', '=', city_type.id if city_type else False),
                ('sales_auction_stage_selection', '=', 'p2_auction_city_portfolio')
            ])
                
        domain.append(('sales_auction_stage_selection', 'not in', ['p2_shared_archive', 'p2_sales_archive']))
                
        return {
            'type': 'ir.actions.act_window',
            'name': _('Select Properties to Assign to the Project'),
            'res_model': 'sales.auction.management',
            'view_mode': 'list',
            'views': [(assign_list_view.id if assign_list_view else False, 'list')],
            'domain': domain,
            'context': {
                'project_to_assign': self.id,
                'project_manager_id': self.project_manager_id.id,
            },
            'target': 'new',
        }

    @api.model_create_multi
    def create(self, vals_list):
        type_xml_map = {
            'sales': 'sales_and_auction_management.bussma_project_type_sales',
            'auction_pvt': 'sales_and_auction_management.bussma_project_type_auction_pvt',
            'city': 'sales_and_auction_management.bussma_project_type_auction_city',
            'auction_enf': 'sales_and_auction_management.bussma_project_type_auction_enf',
        }
        stage_xml_map = {
            'sales': 'sales_and_auction_management.bussma_project_stage_sales_pm',
            'auction_pvt': 'sales_and_auction_management.bussma_project_stage_pvt_pm',
            'city': 'sales_and_auction_management.bussma_project_stage_city_pm',
            'auction_enf': 'sales_and_auction_management.bussma_project_stage_enf_pm',
        }
        for vals in vals_list:
            if vals.get('code', '/') == '/':
                vals['code'] = self.env['ir.sequence'].next_by_code('bussma.project') or '/'
            p_type = vals.get('project_type')
            if p_type and p_type in type_xml_map:
                if not vals.get('request_type_id'):
                    req_type = self.env.ref(type_xml_map[p_type], raise_if_not_found=False)
                    if req_type:
                        vals['request_type_id'] = req_type.id
                if not vals.get('stage_id'):
                    stage = self.env.ref(stage_xml_map[p_type], raise_if_not_found=False)
                    if stage:
                        vals['stage_id'] = stage.id
        records = super(BussmaProject, self).create(vals_list)
        for record in records:
            if record.project_manager_id:
                record._send_manager_assigned_email()
        return records

    def write(self, vals):
        records_to_email = self.env['bussma.project']
        if 'project_manager_id' in vals and vals.get('project_manager_id'):
            new_manager_id = vals.get('project_manager_id')
            for record in self:
                if record.project_manager_id.id != new_manager_id:
                    records_to_email |= record
        
        res = super(BussmaProject, self).write(vals)

        for record in records_to_email:
            record._send_manager_assigned_email()
        return res

    def _send_manager_assigned_email(self):
        self.ensure_one()
        if not self.project_manager_id or not self.project_manager_id.email:
            _logger.warning(
                "[Project Manager Email] Skipped — no recipient or email for project: %s",
                self.name
            )
            return
        template = self.env.ref('sales_and_auction_management.email_template_sales_auction_project_manager_assigned', raise_if_not_found=False)
        if not template:
            _logger.warning(
                "[Project Manager Email] Template not found: sales_and_auction_management.email_template_sales_auction_project_manager_assigned"
            )
            return
        sender_name = _("Sales Department") if self.project_type == 'sales' else _("Auctions Department")
        base_email = self.env.user.email or self.env.company.email or ''
        email_from = f'"{sender_name}" <{base_email}>' if base_email else sender_name
        try:
            template.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.project_manager_id.email,
                    'email_from': email_from,
                    'model': False,
                    'res_id': False,
                },
            )
            _logger.info(
                "[Project Manager Email] Sent email to %s for project %s",
                self.project_manager_id.email, self.name
            )
        except Exception as e:
            _logger.error(
                "[Project Manager Email] Failed to send email: %s", str(e)
            )

    def unlink(self):
        sales_basic = self.env.ref('sales_and_auction_management.project_sales_basic', raise_if_not_found=False)
        pvt_basic = self.env.ref('sales_and_auction_management.project_auctions_pvt_basic', raise_if_not_found=False)
        enf_basic = self.env.ref('sales_and_auction_management.project_auctions_enf_basic', raise_if_not_found=False)
        city_basic = self.env.ref('sales_and_auction_management.project_cities_basic', raise_if_not_found=False)
        
        basic_ids = [r.id for r in [sales_basic, pvt_basic, enf_basic, city_basic] if r]
        
        for rec in self:
            if rec.id in basic_ids:
                raise UserError(_("You cannot delete basic system portfolios!"))
        
        return super(BussmaProject, self).unlink()

    def action_raise_marketing_request_wizard(self):
        self.ensure_one()
        properties = self.entry_ids or self.env['sales.auction.management'].search([('project_id', '=', self.id)])
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'bussma.project'),
            ('res_id', '=', self.id)
        ])
        return {
            'name': _('Create Marketing Request for Project'),
            'type': 'ir.actions.act_window',
            'res_model': 'sales.auction.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_project_id': self.id,
                'default_property_ids': [(6, 0, properties.ids)],
                'default_request_type': 'marketing',
                'default_name': self.name or '',
                'default_attachments_ids': [(6, 0, attachments.ids)],
            }
        }
