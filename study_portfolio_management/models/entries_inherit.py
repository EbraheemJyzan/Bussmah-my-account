# -*- coding: utf-8 -*-
from collections import defaultdict
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression

STAGE_FIELDS_MAP = {
    'entry_screen': [
        'customer_intent_rel', 'customer_intent', 'partner_id', 'customer_role_rel',
        'owner_type', 'partner_mobile', 'entered_by_id', 'entered_by_email',
        'requires_technical_offer', 'property_type', 'property_usage_rel',
        'customer_price_per_sqm', 'has_income', 'current_income',
        'city', 'district_id', 'location_url', 'plot_number', 'plan_number',
        'deed_number', 'deed_date', 'listing_date', 'entered_notes',
        'property_attachment_ids',
    ],
    'data_completion': [
        'customer_intent_rel', 'customer_intent', 'entered_notes',
        'requires_technical_offer',
    ],
    'define_project_path_assign_analyst': [
        'project_path', 'project_path_rel', 'is_authorized_property', 'rejection_reason',
        'return_to_lister_note', 'analyst_id', 'detailed_analyst_id', 'city_analyst_id',
    ],
    'analyst': [
        'property_usage_standard', 'building_requirements', 'price_per_meter',
        'final_property_price', 'justice_index_average', 'comparison_average',
        'expected_full_lease_income', 'analyst_notes', 'analyst_recommendation_preliminary',
        'analyst_recommendation_details', 'is_assign_detailed_study',
        'detailed_analyst_id', 'detailed_price_per_meter',
        'best_property_use', 'internal_strength_points', 'internal_weakness_points',
        'external_strength_points', 'external_weakness_points',
        'detailed_analyst_notes', 'property_description',
        'street_length', 'nearest_main_road', 'precise_plot_location_link',
        'land_nature', 'building_license_number', 'building_license_date',
        'detailed_building_requirements', 'electricity_meters_numbers', 'water_meters_numbers',
        'preliminary_study_status',
    ],
    'detailed_study_analyst': [
        'detailed_analyst_id', 'detailed_price_per_meter',
        'analyst_recommendation_details', 'best_property_use',
        'internal_strength_points', 'internal_weakness_points',
        'external_strength_points', 'external_weakness_points',
        'detailed_analyst_notes', 'property_description',
        'street_length', 'nearest_main_road', 'precise_plot_location_link',
        'land_nature', 'building_license_number', 'building_license_date',
        'detailed_building_requirements', 'electricity_meters_numbers', 'water_meters_numbers',
    ],
    'city_study_analyst': [
        'area', 'allocation_fees', 'annual_financial_fee',
        'gps_coordinates', 'industrial_city', 'previous_activity',
        'facility_investor', 'investor_contact_number', 'has_movables',
        'equipment', 'vehicles', 'machinery', 'systems', 'analyst_notes',
        'coordinates_kmz', 'coordinates_kmz_name',
        'current_income_file', 'current_income_file_name',
        'facility_photo_ids', 'rent_contract_ids',
    ],
    'study_approval': [
        'standard_study_manager_approval', 'standard_study_manager_approval_rel',
        'standard_study_manager_note', 'specialized_study_manager_approval',
        'specialized_study_manager_note', 'cities_study_manager_approval',
        'cities_study_manager_note',
    ],
    'detailed_study_approval': [
        'specialized_study_manager_approval', 'specialized_study_manager_note',
    ],
    'city_study_approval': [
        'cities_study_manager_approval', 'cities_study_manager_note',
    ],
    'committee_decision': [
        'committee_decision', 'committee_decision_rel', 'committee_decision_date',
        'marketing_duration_months', 'direct_sale_price_per_meter',
        'direct_sale_total_price', 'auction_price_per_meter', 'auction_total_price',
        'committe_notes', 'committee_approved_users', 'committee_rejected_users',
        'committee_postponed_users',
    ],
    'sales_manager_decision': [
        'sales_manager_approval', 'sales_manager_approval_rel', 'sales_manager_notes',
    ],
    'auctions_manager_decision': [
        'auctions_manager_approval', 'auctions_manager_approval_rel', 'auctions_manager_notes',
    ],
    'commercial_manager_approval': [
        'commercial_sector_manager_approval', 'commercial_sector_manager_approval_rel',
        'commercial_sector_manager_reason', 'commercial_sector_manager_notes',
        'commercial_sector_advisor_decision',
    ],
    'assign_negotiator': [
        'assigned_negotiator',
    ],
    'negotiator': [
        'final_owner_decision', 'final_owner_decision_rel',
        'final_owner_price_per_meter', 'final_owner_price',
        'owner_rejection_reasons', 'negotiator_note',
        'is_sent_to_deputy_studies_manager', 'deputy_studies_manager_approval',
        'manager_negotiator_final_owner_decision',
        'manager_negotiator_final_owner_price_per_meter',
        'manager_negotiator_final_owner_price',
        'manager_negotiator_owner_rejection_reasons', 'manager_negotiator_note',
    ],
    'manager_contract_approval': [
        'commercial_sector_manager_contract_approval',
        'commercial_sector_manager_contract_notes',
    ],
    'contract_followup': [
        'assigned_project_manager', 'contract_agreed_price',
        'contract_duration', 'contract_notes',
    ],
    'studies_supervisor_eanfaz': [
        'studies_supervisor_data_complete', 'notes_supervisor_study',
        'detailed_analyst_id',
    ],
    'detailed_study_eanfaz': [
        'detailed_final_property_price', 'current_total_income', 'expected_total_income_full_rent',
        'property_condition', 'land_nature', 'best_property_use',
        'internal_strength_points', 'internal_weakness_points',
        'external_strength_points', 'external_weakness_points',
        'analyst_recommendation_details', 'study_rejection_notes',
        'lowest_price_per_meter_total_property', 'highest_price_per_meter_total_property',
        'detailed_comparison_average', 'justice_ministry_index_average',
        'approximate_land_value_per_meter', 'approximate_building_value_per_meter',
        'finishing_ratio', 'building_area', 'floors_count', 'units_count',
        'electricity_meters_count', 'water_meters_count',
        'electricity_meters_numbers', 'water_meters_numbers',
        'property_usage_rel', 'building_license_number', 'building_license_date',
        'detailed_building_requirements', 'completion_certificate_issued',
        'property_description', 'street', 'street_length', 'nearest_main_road',
        'precise_plot_location_link', 'limit_east', 'limit_west', 'limit_north', 'limit_south',
        'length_east', 'length_west', 'length_north', 'length_south',
        'has_movables', 'is_estimated_more_than_50k', 'are_keys_available', 'key_location',
        'electricity_service', 'water_service', 'sewage_service',
        'telecom_service', 'lighting_service', 'pavement_service',
        'gas_service', 'security_service', 'internet_service',
        'cleaning_service', 'parking_service', 'garden_service',
        'pool_service', 'elevator_service', 'ac_service',
    ],
    'detailed_study_approval_eanfaz': [
        'specialized_study_manager_approval', 'specialized_study_manager_note',
    ],
}

EXCLUDE_BATCH_FIELDS = {
    # System & Audit
    'id', 'display_name', '__last_update', 'create_uid', 'create_date', 'write_uid', 'write_date',
    # Portfolio engine
    'enable_portfolio_batch_action', 'batch_portfolio_entry_ids', 'batch_allowed_entry_ids',
    'batch_peer_count', 'batch_selected_count', 'portfolio_id', 'has_portfolio', 'study_type',
    # Mail & Activities
    'message_follower_ids', 'message_ids', 'activity_ids', 'message_main_attachment_id', 'website_message_ids',
    # Property Identity & Physical attributes unique to each asset (excluded from batch overwrite)
    'name', 'entrie_name', 'reference', 'sequence', 'barcode',
    'latitude', 'longitude', 'map_link', 'national_address',
    'sale_auction_id', 'opportunity_id',
}


class Entries(models.Model):
    _inherit = 'entries'

    has_portfolio = fields.Boolean(
        string='Belongs to a Portfolio?',
        default=False,
        tracking=True,
    )
    portfolio_id = fields.Many2one(
        'study.portfolio',
        string='Study Portfolio',
        tracking=True,
        ondelete='set null',
    )

    # Batch Action Fields
    enable_portfolio_batch_action = fields.Boolean(
        string='Batch Action on Portfolio Properties',
        default=False,
        help='Enable to apply stage changes and actions to selected properties in the same portfolio and stage.',
    )
    batch_portfolio_entry_ids = fields.Many2many(
        'entries',
        'entries_portfolio_batch_rel',
        'source_entry_id',
        'target_entry_id',
        string='Target Properties for Batch Action',
    )
    batch_allowed_entry_ids = fields.Many2many(
        'entries',
        compute='_compute_batch_allowed_entry_ids',
        string='Allowed Peer Properties',
    )
    batch_peer_count = fields.Integer(
        string='Peer Properties Count',
        compute='_compute_batch_peer_info',
    )
    batch_selected_count = fields.Integer(
        string='Selected Properties Count',
        compute='_compute_batch_peer_info',
    )

    study_type = fields.Selection([
        ('preliminary', 'Preliminary Study'),
        ('detailed', 'Detailed Study'),
    ], string='Study Type', compute='_compute_study_type', store=True, index=True)

    can_manage_portfolio_assignment = fields.Boolean(
        string='Can Manage Portfolio Assignment',
        compute='_compute_can_manage_portfolio_assignment',
    )

    @api.model
    def _is_portfolio_assignment_manager(self, user=None):
        """Check if user has permission to assign or unassign properties to/from study portfolios."""
        user = user or self.env.user
        return bool(
            user.id == 1 or
            user.has_group('base.group_system') or
            user.has_group('bussma_system.group_sales_manager') or
            user.has_group('bussma_system.group_auctions_manager') or
            user.has_group('bussma_system.group_studies_manager') or
            user.has_group('bussma_system.group_deputy_studies_manager') or
            user.has_group('bussma_system.group_city_studies_manager')
        )

    def _compute_can_manage_portfolio_assignment(self):
        can_manage = self._is_portfolio_assignment_manager()
        for rec in self:
            rec.can_manage_portfolio_assignment = can_manage

    @api.depends(
        'stage_id', 'stage_id.project_stage_selection', 'project_stage_selection',
        'project_path', 'project_path_rel', 'project_path_rel.code', 'is_assign_detailed_study'
    )
    def _compute_study_type(self):
        for rec in self:
            stage_sel = rec.project_stage_selection or (rec.stage_id.project_stage_selection if rec.stage_id else '')
            if stage_sel not in ('analyst', 'detailed_study_analyst'):
                rec.study_type = False
                continue
            p_code = (rec.project_path_rel.code if rec.project_path_rel else False) or rec.project_path
            if p_code == 'standard' and not rec.is_assign_detailed_study:
                rec.study_type = 'preliminary'
            elif p_code == 'specialized' or (p_code == 'standard' and rec.is_assign_detailed_study):
                rec.study_type = 'detailed'
            else:
                rec.study_type = False

    def _is_preliminary_study(self):
        """Preliminary Study: standard path and not is_assign_detailed_study."""
        self.ensure_one()
        if self.study_type:
            return self.study_type == 'preliminary'
        p_code = (self.project_path_rel.code if self.project_path_rel else False) or self.project_path
        return p_code == 'standard' and not self.is_assign_detailed_study

    def _is_detailed_study(self):
        """Detailed Study: specialized path or (standard path and is_assign_detailed_study)."""
        self.ensure_one()
        if self.study_type:
            return self.study_type == 'detailed'
        p_code = (self.project_path_rel.code if self.project_path_rel else False) or self.project_path
        if p_code == 'specialized':
            return True
        if p_code == 'standard' and self.is_assign_detailed_study:
            return True
        return False

    def _get_batch_peer_entries(self, stage=None):
        self.ensure_one()
        if isinstance(stage, int):
            current_stage = self.env['request.stage'].browse(stage)
        else:
            current_stage = stage or self.stage_id
        if not self.portfolio_id or not current_stage:
            return self.env['entries']

        user = self.env.user
        is_admin = user._is_admin()
        stage_sel = current_stage.project_stage_selection or (self.project_stage_selection if current_stage == self.stage_id else '')

        # Base domain: same portfolio, same stage, not archived, not self
        domain = [
            ('portfolio_id', '=', self.portfolio_id.id),
            ('stage_id', '=', current_stage.id),
            ('id', '!=', self.id),
            ('is_entry_archive', '=', False),
        ]

        peers = self.env['entries'].search(domain)
        if self._is_eanfaz_study():
            peers = peers.filtered(lambda p: p._is_eanfaz_study())
        else:
            peers = peers.filtered(lambda p: not p._is_eanfaz_study())

        if not peers:
            return peers

        is_studies_mgr = (
            user.has_group('bussma_system.group_studies_manager') or
            user.has_group('bussma_system.group_deputy_studies_manager')
        )
        is_sales_mgr = user.has_group('bussma_system.group_sales_manager')
        is_auctions_mgr = user.has_group('bussma_system.group_auctions_manager')

        # -------------------------------------------------------------
        # 0. Define Project Path & Assign Analyst Stage
        # -------------------------------------------------------------
        if stage_sel == 'define_project_path_assign_analyst':
            is_def_path_mgr = (
                is_studies_mgr or
                user.has_group('bussma_system.group_rnd_manager')
            )
            if not is_admin and not is_def_path_mgr:
                return self.env['entries']
            assign_val = bool(self.is_assign_detailed_study)
            email_val = bool(self.is_send_email_to_detailed_study)
            peers = peers.filtered(
                lambda p: bool(p.is_assign_detailed_study) == assign_val and
                          bool(p.is_send_email_to_detailed_study) == email_val
            )
            return peers

        # -------------------------------------------------------------
        # 1. Analyst Stages: Preliminary vs Detailed
        # -------------------------------------------------------------
        elif stage_sel == 'detailed_study_analyst':
            if not is_admin and not is_studies_mgr:
                if not self.detailed_analyst_id or self.detailed_analyst_id.id != user.id:
                    return self.env['entries']
                target_analyst_id = self.detailed_analyst_id.id if self.detailed_analyst_id else False
                peers = peers.filtered(lambda p: p.detailed_analyst_id.id == target_analyst_id)

        elif stage_sel == 'analyst':
            if self._is_preliminary_study():
                # Preliminary Study: standard path & not is_assign_detailed_study
                if not is_admin and not is_studies_mgr:
                    if not self.analyst_id or self.analyst_id.id != user.id:
                        return self.env['entries']
                target_analyst_id = self.analyst_id.id if self.analyst_id else False
                if not (is_admin or is_studies_mgr):
                    peers = peers.filtered(lambda p: p._is_preliminary_study() and p.analyst_id.id == target_analyst_id)
                else:
                    peers = peers.filtered(lambda p: p._is_preliminary_study())

            elif self._is_detailed_study():
                # Detailed Study: specialized path or (standard & is_assign_detailed_study)
                if not is_admin and not is_studies_mgr:
                    if not self.detailed_analyst_id or self.detailed_analyst_id.id != user.id:
                        return self.env['entries']
                target_analyst_id = self.detailed_analyst_id.id if self.detailed_analyst_id else False
                if not (is_admin or is_studies_mgr):
                    peers = peers.filtered(lambda p: p._is_detailed_study() and p.detailed_analyst_id.id == target_analyst_id)
                else:
                    peers = peers.filtered(lambda p: p._is_detailed_study())
            else:
                if self.project_path:
                    peers = peers.filtered(lambda p: not p.project_path or p.project_path == self.project_path)

        # -------------------------------------------------------------
        # 1.1 City Study Analyst Stage
        # -------------------------------------------------------------
        elif stage_sel == 'city_study_analyst':
            is_city_mgr = user.has_group('bussma_system.group_city_studies_manager')
            if not is_admin and not is_studies_mgr and not is_city_mgr:
                assigned_analyst = self.city_analyst_id or self.analyst_id
                if not assigned_analyst or assigned_analyst.id != user.id:
                    return self.env['entries']
            target_analyst_id = (self.city_analyst_id.id if self.city_analyst_id else False) or (self.analyst_id.id if self.analyst_id else False)
            if not (is_admin or is_studies_mgr or is_city_mgr) and target_analyst_id:
                peers = peers.filtered(lambda p: ((p.city_analyst_id.id if p.city_analyst_id else p.analyst_id.id) if (p.city_analyst_id or p.analyst_id) else False) == target_analyst_id)

        # -------------------------------------------------------------
        # 2. Negotiator Stage: 3 Sub-procedures
        # -------------------------------------------------------------
        elif stage_sel == 'negotiator':
            # Sub-procedure A: Deputy Studies Manager Approval
            if self.is_sent_to_deputy_studies_manager:
                if not is_admin and not user.has_group('bussma_system.group_deputy_studies_manager'):
                    return self.env['entries']
                peers = peers.filtered(lambda p: p.is_sent_to_deputy_studies_manager)

            # Sub-procedure B: Department Manager Negotiator (returned from manager_contract_approval)
            elif self.is_manager_negotiator:
                comm_dec = self.committee_decision or (self.committee_decision_rel.code if self.committee_decision_rel else False)
                if comm_dec == 'direct_sale':
                    if not is_admin and not is_sales_mgr:
                        return self.env['entries']
                    peers = peers.filtered(lambda p: (
                        not p.is_sent_to_deputy_studies_manager and
                        p.is_manager_negotiator and
                        (p.committee_decision == 'direct_sale' or (p.committee_decision_rel and p.committee_decision_rel.code == 'direct_sale'))
                    ))
                elif comm_dec == 'auction':
                    if not is_admin and not is_auctions_mgr:
                        return self.env['entries']
                    peers = peers.filtered(lambda p: (
                        not p.is_sent_to_deputy_studies_manager and
                        p.is_manager_negotiator and
                        (p.committee_decision == 'auction' or (p.committee_decision_rel and p.committee_decision_rel.code == 'auction'))
                    ))
                else:
                    if not is_admin and not (is_sales_mgr or is_auctions_mgr):
                        return self.env['entries']
                    peers = peers.filtered(lambda p: not p.is_sent_to_deputy_studies_manager and p.is_manager_negotiator)

            # Sub-procedure C: Assigned Negotiator
            else:
                if not is_admin and not (is_sales_mgr or is_auctions_mgr):
                    if not self.assigned_negotiator or self.assigned_negotiator.id != user.id:
                        return self.env['entries']
                target_neg_id = self.assigned_negotiator.id if self.assigned_negotiator else False
                peers = peers.filtered(lambda p: (
                    not p.is_sent_to_deputy_studies_manager and
                    not p.is_manager_negotiator and
                    p.assigned_negotiator.id == target_neg_id
                ))

        # -------------------------------------------------------------
        # 3. Detailed Study Eanfaz Stage
        # -------------------------------------------------------------
        elif stage_sel == 'detailed_study_eanfaz' or (self._is_eanfaz_study() and 'detailed_study' in stage_sel):
            if not is_admin and not is_studies_mgr:
                if not self.detailed_analyst_id or self.detailed_analyst_id.id != user.id:
                    return self.env['entries']
                target_analyst_id = self.detailed_analyst_id.id if self.detailed_analyst_id else False
                peers = peers.filtered(lambda p: p.detailed_analyst_id.id == target_analyst_id)

        # -------------------------------------------------------------
        # 4. Study Approval Stages: Preliminary vs Detailed
        # -------------------------------------------------------------
        elif stage_sel == 'detailed_study_approval':
            if not is_admin and not is_studies_mgr:
                return self.env['entries']

        elif stage_sel == 'study_approval':
            if not is_admin and not is_studies_mgr:
                return self.env['entries']
            if self._is_preliminary_study():
                peers = peers.filtered(lambda p: p._is_preliminary_study())
            elif self._is_detailed_study():
                peers = peers.filtered(lambda p: p._is_detailed_study())
            elif self.project_path:
                peers = peers.filtered(lambda p: p.project_path == self.project_path)

        # -------------------------------------------------------------
        # 5. Department Manager Decision Stages: Sales vs Auctions
        # -------------------------------------------------------------
        elif stage_sel == 'sales_manager_decision':
            if not is_admin and not is_sales_mgr:
                return self.env['entries']

        elif stage_sel == 'auctions_manager_decision':
            if not is_admin and not is_auctions_mgr:
                return self.env['entries']

        elif stage_sel == 'city_study_approval':
            is_city_mgr = user.has_group('bussma_system.group_city_studies_manager')
            if not is_admin and not is_studies_mgr and not is_city_mgr:
                return self.env['entries']
            return peers

        elif stage_sel == 'committee_decision':
            return peers

        elif stage_sel == 'commercial_manager_approval':
            return peers
        elif stage_sel == 'assign_negotiator':
            return peers

        else:
            if self.project_path:
                peers = peers.filtered(lambda p: not p.project_path or p.project_path == self.project_path)

        return peers

    @api.depends(
        'portfolio_id', 'stage_id', 'project_path', 'project_path_rel',
        'is_assign_detailed_study', 'is_send_email_to_detailed_study',
        'analyst_id', 'detailed_analyst_id',
        'assigned_negotiator', 'is_sent_to_deputy_studies_manager',
        'is_manager_negotiator', 'committee_decision', 'committee_decision_rel',
        'customer_intent', 'customer_intent_rel'
    )
    def _compute_batch_allowed_entry_ids(self):
        for rec in self:
            if rec.portfolio_id and rec.stage_id:
                rec.batch_allowed_entry_ids = rec._get_batch_peer_entries()
            else:
                rec.batch_allowed_entry_ids = self.env['entries']

    @api.depends(
        'portfolio_id', 'stage_id', 'project_path', 'project_path_rel',
        'is_assign_detailed_study', 'is_send_email_to_detailed_study',
        'analyst_id', 'detailed_analyst_id',
        'assigned_negotiator', 'is_sent_to_deputy_studies_manager',
        'is_manager_negotiator', 'committee_decision', 'committee_decision_rel',
        'customer_intent', 'customer_intent_rel',
        'batch_portfolio_entry_ids'
    )
    def _compute_batch_peer_info(self):
        for rec in self:
            if rec.portfolio_id and rec.stage_id:
                rec.batch_peer_count = len(rec._get_batch_peer_entries())
            else:
                rec.batch_peer_count = 0
            rec.batch_selected_count = len(rec.batch_portfolio_entry_ids)

    @api.onchange('enable_portfolio_batch_action')
    def _onchange_enable_portfolio_batch_action(self):
        if not self.enable_portfolio_batch_action:
            self.batch_portfolio_entry_ids = False

    def action_batch_select_all(self):
        self.ensure_one()
        peers = self._get_batch_peer_entries()
        self.write({
            'enable_portfolio_batch_action': True,
            'batch_portfolio_entry_ids': [(6, 0, peers.ids)],
        })
        return True

    def action_batch_clear_all(self):
        self.ensure_one()
        self.write({
            'batch_portfolio_entry_ids': [(5, 0, 0)],
        })
        return True

    def _check_batch_portfolio_permissions(self, target):
        user = self.env.user
        if user._is_admin():
            return True

        stage_sel = target.project_stage_selection or (target.stage_id.project_stage_selection if target.stage_id else '')
        is_studies_mgr = (
            user.has_group('bussma_system.group_studies_manager') or
            user.has_group('bussma_system.group_deputy_studies_manager')
        )
        is_sales_mgr = user.has_group('bussma_system.group_sales_manager')
        is_auctions_mgr = user.has_group('bussma_system.group_auctions_manager')
        is_comm_mgr = user.has_group('bussma_system.group_commercial_sector_manager')

        # 0. Define project path stage
        if stage_sel == 'define_project_path_assign_analyst':
            is_def_path_mgr = (
                is_studies_mgr or
                user.has_group('bussma_system.group_rnd_manager')
            )
            if not is_def_path_mgr:
                raise UserError(_(
                    "You cannot execute batch action on property '%s': Only the Studies Manager or R&D Manager can define project path."
                ) % (target.entrie_name or target.id))

        # 1. Analyst stages
        if stage_sel == 'detailed_study_analyst':
            if not is_studies_mgr:
                if not target.detailed_analyst_id or target.detailed_analyst_id.id != user.id:
                    raise UserError(_(
                        "You cannot execute batch action on property '%s': You are not the assigned detailed analyst for this property."
                    ) % (target.entrie_name or target.id))

        elif stage_sel == 'analyst':
            if target._is_preliminary_study():
                if not is_studies_mgr:
                    if not target.analyst_id or target.analyst_id.id != user.id:
                        raise UserError(_(
                            "You cannot execute batch action on property '%s': You are not the assigned analyst for this property."
                        ) % (target.entrie_name or target.id))
            elif target._is_detailed_study():
                if not is_studies_mgr:
                    if not target.detailed_analyst_id or target.detailed_analyst_id.id != user.id:
                        raise UserError(_(
                            "You cannot execute batch action on property '%s': You are not the assigned detailed analyst for this property."
                        ) % (target.entrie_name or target.id))
            else:
                if not is_studies_mgr:
                    if not target.analyst_id or target.analyst_id.id != user.id:
                        raise UserError(_(
                            "You cannot execute batch action on property '%s': You are not the assigned analyst for this property."
                        ) % (target.entrie_name or target.id))

        elif stage_sel == 'city_study_analyst':
            if not is_studies_mgr:
                if not target.analyst_id or target.analyst_id.id != user.id:
                    raise UserError(_(
                        "You cannot execute batch action on property '%s': You are not the assigned analyst for this property."
                    ) % (target.entrie_name or target.id))

        elif stage_sel == 'detailed_study_eanfaz' or (target._is_eanfaz_study() and 'detailed_study' in stage_sel):
            if not is_studies_mgr:
                assigned = target.detailed_analyst_id or target.analyst_id
                if not assigned or assigned.id != user.id:
                    raise UserError(_(
                        "You cannot execute batch action on property '%s': You are not the assigned detailed analyst for this property."
                    ) % (target.entrie_name or target.id))

        # 2. Negotiator stage
        elif stage_sel == 'negotiator':
            if target.is_sent_to_deputy_studies_manager:
                if not user.has_group('bussma_system.group_deputy_studies_manager'):
                    raise UserError(_(
                        "You cannot execute batch action on property '%s': Only the Deputy Studies Manager can perform this action."
                    ) % (target.entrie_name or target.id))
            elif target.is_manager_negotiator:
                comm_dec = target.committee_decision or (target.committee_decision_rel.code if target.committee_decision_rel else False)
                if comm_dec == 'direct_sale' and not is_sales_mgr:
                    raise UserError(_(
                        "You cannot execute batch action on property '%s': Only the Sales Manager can perform this action."
                    ) % (target.entrie_name or target.id))
                elif comm_dec == 'auction' and not is_auctions_mgr:
                    raise UserError(_(
                        "You cannot execute batch action on property '%s': Only the Auctions Manager can perform this action."
                    ) % (target.entrie_name or target.id))
                elif not (is_sales_mgr or is_auctions_mgr):
                    raise UserError(_(
                        "You cannot execute batch action on property '%s': Only the Department Manager can perform this action."
                    ) % (target.entrie_name or target.id))
            else:
                if not (is_sales_mgr or is_auctions_mgr):
                    if not target.assigned_negotiator or target.assigned_negotiator.id != user.id:
                        raise UserError(_(
                            "You cannot execute batch action on property '%s': You are not the assigned negotiator for this property."
                        ) % (target.entrie_name or target.id))

        # 3. Study approval stages
        elif stage_sel in ('study_approval', 'detailed_study_approval', 'city_study_approval'):
            if not is_studies_mgr:
                raise UserError(_(
                    "You cannot execute batch action on property '%s': Only the Studies Manager can approve studies."
                ) % (target.entrie_name or target.id))

        # 4. Department manager decision stages
        elif stage_sel == 'sales_manager_decision':
            if not is_sales_mgr:
                raise UserError(_(
                    "You cannot execute batch action on property '%s': Only the Sales Manager can approve sales properties."
                ) % (target.entrie_name or target.id))

        elif stage_sel == 'auctions_manager_decision':
            if not is_auctions_mgr:
                raise UserError(_(
                    "You cannot execute batch action on property '%s': Only the Auctions Manager can approve auction properties."
                ) % (target.entrie_name or target.id))

        # 5. Contract followup stage
        elif stage_sel == 'contract_followup':
            if not is_comm_mgr:
                assigned_pm = target.assigned_project_manager or getattr(target, 'project_manager_id', False)
                if not assigned_pm or assigned_pm.id != user.id:
                    raise UserError(_(
                        "You cannot execute batch action on property '%s': You are not the assigned project manager for this property."
                    ) % (target.entrie_name or target.id))

        return True

    def _get_stage_batch_fields(self):
        self.ensure_one()
        stage_sel = self.project_stage_selection or (self.stage_id.project_stage_selection if self.stage_id else '')

        # 1. Analyst Stage
        if stage_sel in ('analyst', 'detailed_study_analyst'):
            if stage_sel == 'analyst' and self._is_preliminary_study():
                return [
                    'preliminary_study_status', 'price_per_meter', 'final_property_price',
                    'justice_index_average', 'comparison_average', 'market_value_per_sqm',
                    'market_value_per_meter', 'building_surface', 'building_height', 'number_of_floors',
                    'building_front_retreat', 'building_side_retreat', 'building_rear_retreat',
                    'analyst_recommendation', 'analyst_id'
                ]
            else:
                return [
                    'detailed_analyst_id', 'detailed_price_per_meter', 'detailed_final_property_price',
                    'detailed_comparison_average', 'justice_ministry_index_average',
                    'lowest_price_per_meter_total_property', 'highest_price_per_meter_total_property',
                    'approximate_building_value_per_meter', 'approximate_land_value_per_meter',
                    'expected_total_income_full_rent', 'building_area', 'finishing_ratio',
                    'floors_count', 'units_count', 'rooms_count',
                    'electricity_meters_count', 'water_meters_count',
                    'best_property_use', 'internal_strength_points', 'internal_weakness_points',
                    'external_strength_points', 'external_weakness_points',
                    'detailed_analyst_notes', 'property_description',
                    'street_length', 'nearest_main_road', 'precise_plot_location_link',
                    'land_nature', 'building_license_number', 'building_license_date',
                    'detailed_building_requirements', 'electricity_meters_numbers', 'water_meters_numbers',
                    'analyst_recommendation_details',
                ]

        # 2. Negotiator Stage
        elif stage_sel == 'negotiator':
            if self.is_sent_to_deputy_studies_manager:
                return ['deputy_studies_manager_approval', 'deputy_studies_manager_notes']
            elif self.is_manager_negotiator:
                return [
                    'manager_negotiator_final_owner_decision',
                    'manager_negotiator_final_owner_price_per_meter',
                    'manager_negotiator_final_owner_price',
                    'manager_negotiator_owner_rejection_reasons',
                    'manager_negotiator_note',
                ]
            else:
                return [
                    'final_owner_decision', 'final_owner_decision_rel',
                    'final_owner_price_per_meter', 'final_owner_price',
                    'owner_rejection_reasons', 'negotiator_note',
                ]

        # 3. Study Approval Stage
        elif stage_sel in ('study_approval', 'detailed_study_approval'):
            if stage_sel == 'study_approval' and self._is_preliminary_study():
                return [
                    'standard_study_manager_approval',
                    'standard_study_manager_approval_rel',
                    'standard_study_manager_note',
                ]
            else:
                return [
                    'specialized_study_manager_approval',
                    'specialized_study_manager_note',
                ]

        # 4. Department Manager Decision Stages
        elif stage_sel == 'sales_manager_decision':
            return [
                'sales_manager_approval',
                'sales_manager_approval_rel',
                'sales_manager_notes',
            ]
        elif stage_sel == 'auctions_manager_decision':
            return [
                'auctions_manager_approval',
                'auctions_manager_approval_rel',
                'auctions_manager_notes',
            ]

        return STAGE_FIELDS_MAP.get(stage_sel, [])

    def _get_replicated_field_values(self, target, vals=None):
        self.ensure_one()
        target_vals = {}
        if not vals:
            return target_vals

        # 1. Replicate ONLY fields explicitly modified in vals
        for k, v in vals.items():
            if k in EXCLUDE_BATCH_FIELDS:
                continue
            if k not in target._fields or k not in self._fields:
                continue
            field = self._fields[k]
            if field.type == 'one2many':
                continue
            if field.compute and not field.inverse and not field.store:
                continue
            if field.type == 'many2one':
                target_vals[k] = getattr(self, k).id or False
            elif field.type == 'many2many':
                target_vals[k] = [(6, 0, getattr(self, k).ids)]
            else:
                target_vals[k] = getattr(self, k)

        # 1.1 Synchronize paired relation/selection fields if either was in vals
        sync_pairs = {
            'project_path_rel': 'project_path',
            'project_path': 'project_path_rel',
            'customer_intent_rel': 'customer_intent',
            'customer_intent': 'customer_intent_rel',
            'committee_decision_rel': 'committee_decision',
            'committee_decision': 'committee_decision_rel',
            'sales_manager_approval_rel': 'sales_manager_approval',
            'sales_manager_approval': 'sales_manager_approval_rel',
            'auctions_manager_approval_rel': 'auctions_manager_approval',
            'auctions_manager_approval': 'auctions_manager_approval_rel',
            'commercial_sector_manager_approval_rel': 'commercial_sector_manager_approval',
            'commercial_sector_manager_approval': 'commercial_sector_manager_approval_rel',
            'final_owner_decision_rel': 'final_owner_decision',
            'final_owner_decision': 'final_owner_decision_rel',
            'standard_study_manager_approval_rel': 'standard_study_manager_approval',
            'standard_study_manager_approval': 'standard_study_manager_approval_rel',
        }
        for src_f, paired_f in sync_pairs.items():
            if src_f in vals and paired_f in target._fields and paired_f not in target_vals:
                paired_field = self._fields[paired_f]
                if paired_field.type == 'many2one':
                    target_vals[paired_f] = getattr(self, paired_f).id or False
                else:
                    target_vals[paired_f] = getattr(self, paired_f)

        # 1.2 Synchronize companion filename fields for binary attachments
        if 'coordinates_kmz' in vals and 'coordinates_kmz_name' in self._fields and 'coordinates_kmz_name' not in target_vals:
            target_vals['coordinates_kmz_name'] = getattr(self, 'coordinates_kmz_name')
        if 'current_income_file' in vals and 'current_income_file_name' in self._fields and 'current_income_file_name' not in target_vals:
            target_vals['current_income_file_name'] = getattr(self, 'current_income_file_name')

        # 1.3 In define_project_path stage, synchronize companion fields when path or authorization changes
        stage_sel = self.project_stage_selection or (self.stage_id.project_stage_selection if self.stage_id else '')
        if stage_sel == 'define_project_path_assign_analyst':
            if 'project_path_rel' in vals or 'project_path' in vals:
                p_code = (self.project_path_rel.code if self.project_path_rel else False) or self.project_path
                if p_code == 'specialized':
                    target_vals['analyst_id'] = False
                    if self.detailed_analyst_id and 'detailed_analyst_id' not in target_vals:
                        target_vals['detailed_analyst_id'] = self.detailed_analyst_id.id
                elif p_code in ('standard', 'cities'):
                    target_vals['detailed_analyst_id'] = False
                    if self.analyst_id and 'analyst_id' not in target_vals:
                        target_vals['analyst_id'] = self.analyst_id.id

            if 'is_authorized_property' in vals:
                if self.is_authorized_property == 'no':
                    if self.rejection_reason and 'rejection_reason' not in target_vals:
                        target_vals['rejection_reason'] = self.rejection_reason
                elif self.is_authorized_property == 'return_to_lister':
                    if self.return_to_lister_note and 'return_to_lister_note' not in target_vals:
                        target_vals['return_to_lister_note'] = self.return_to_lister_note
                elif self.is_authorized_property == 'yes':
                    target_vals['rejection_reason'] = False
                    target_vals['return_to_lister_note'] = False

        # 2. Dynamic area-based recalculation for price fields ONLY if meter price was modified in vals
        target_area = target.area_sqm or target.area or 0.0
        price_pairs = [
            ('price_per_meter', 'final_property_price'),
            ('detailed_price_per_meter', 'detailed_final_property_price'),
            ('direct_sale_price_per_meter', 'direct_sale_total_price'),
            ('auction_price_per_meter', 'auction_total_price'),
            ('final_owner_price_per_meter', 'final_owner_price'),
            ('manager_negotiator_final_owner_price_per_meter', 'manager_negotiator_final_owner_price'),
        ]
        for meter_field, total_field in price_pairs:
            if meter_field in vals:
                ppm = target_vals.get(meter_field, getattr(self, meter_field) or 0.0) or 0.0
                target_vals[meter_field] = ppm
                if total_field in target._fields:
                    target_vals[total_field] = target_area * ppm
            elif total_field in vals:
                source_ppm = getattr(self, meter_field, 0.0) or 0.0
                if source_ppm and total_field in target._fields:
                    target_vals[total_field] = target_area * source_ppm
                else:
                    if self._is_eanfaz_study():
                        target_vals[total_field] = getattr(self, total_field)
                    else:
                        target_vals.pop(total_field, None)

        # 3. Final safety check: strip any excluded fields
        for excl in EXCLUDE_BATCH_FIELDS:
            target_vals.pop(excl, None)

        return target_vals

    def _prepare_batch_stage_vals(self, target):
        return self._get_replicated_field_values(target, vals=None)

    def action_apply_batch_portfolio_changes(self):
        """Deprecated fallback method for batch applying changes."""
        self.ensure_one()
        return True

    def _replicate_batch_portfolio_action(self, method_name, *args, **kwargs):
        if self.env.context.get('bypass_portfolio_batch'):
            return self.env['entries']

        executed_targets = self.env['entries']
        action_labels = {
            'action_accept': _("Move to Next Stage"),
            'return_to_analyst': _("Return to Analyst"),
            'action_send_to_deputy_studies_manager': _("Send to Deputy Studies Manager"),
            'action_deputy_return_to_negotiator': _("Return to Negotiator"),
            'action_return_to_lister': _("Return to Lister"),
            'action_standard_study_reject_and_archive': _("Reject and Archive Study"),
            'send_email_to_detailed_study': _("Send to Detailed Study"),
            'commercial_sector_manager_approval_path': _("Commercial Manager Decision"),
            'commercial_sector_manager_declined': _("Commercial Manager Decline"),
            'move_to_entry_archive': _("Move to Archive"),
            'move_to_deferred_opportunities_archive': _("Move to Deferred Opportunities"),
            'move_to_partners_screen': _("Move to Partners"),
            'rejecte_owner_decision': _("Reject Owner Decision"),
            'reactivate_deferred_opportunity': _("Reactivate Opportunity"),
            'action_return_to_analyst_eanfaz': _("Return to Analyst (Eanfaz)"),
            'action_return_to_project_manager_eanfaz': _("Return to Project Manager (Eanfaz)"),
        }
        act_name = action_labels.get(method_name, method_name)

        for rec in self:
            if not rec.enable_portfolio_batch_action or not rec.batch_portfolio_entry_ids:
                continue

            valid_peers = rec._get_batch_peer_entries()
            targets = rec.batch_portfolio_entry_ids.filtered(lambda t: t.id in valid_peers.ids)

            if not targets:
                rec.write({
                    'enable_portfolio_batch_action': False,
                    'batch_portfolio_entry_ids': [(5, 0, 0)],
                })
                continue

            # 1. Permission checks on all targets before executing any action
            for target in targets:
                rec._check_batch_portfolio_permissions(target)

            # 1.1 Before executing stage action, ensure required transition fields are synced to targets
            stage_sel = rec.project_stage_selection or (rec.stage_id.project_stage_selection if rec.stage_id else '')
            if method_name == 'action_return_to_analyst_eanfaz' and stage_sel == 'detailed_study_approval_eanfaz':
                if not rec.specialized_study_manager_approval:
                    raise UserError(_("Please fill in the Study Manager Approval decision before returning."))
                if rec.specialized_study_manager_approval != 'incomplete':
                    raise UserError(_("You cannot return the study when the approval decision is 'Completed'. The approval decision must be 'Incomplete'."))
                if not rec.specialized_study_manager_note or not str(rec.specialized_study_manager_note).strip():
                    raise UserError(_("Please enter the Study Manager Notes explaining the return reason before returning."))

            elif method_name == 'return_to_analyst' and stage_sel in ('study_approval', 'detailed_study_approval', 'city_study_approval'):
                if stage_sel == 'detailed_study_approval' or rec.project_path == 'specialized' or (rec.project_path == 'standard' and rec.is_assign_detailed_study):
                    if not rec.specialized_study_manager_approval:
                        raise UserError(_("Please fill in the Study Manager Approval decision before returning."))
                    if rec.specialized_study_manager_approval != 'incomplete':
                        raise UserError(_("You cannot return the study when the approval decision is 'Completed'. The approval decision must be 'Incomplete'."))
                    if not rec.specialized_study_manager_note or not str(rec.specialized_study_manager_note).strip():
                        raise UserError(_("Please enter the Study Manager Notes explaining the return reason before returning."))
                elif rec.project_path == 'standard' and not rec.is_assign_detailed_study:
                    if not rec.standard_study_manager_approval:
                        raise UserError(_("Please fill in the Study Manager Approval decision before returning."))
                    if rec.standard_study_manager_approval != 'incomplete':
                        raise UserError(_("You cannot return the study when the approval decision is not 'Incomplete'."))
                    if not rec.standard_study_manager_note or not str(rec.standard_study_manager_note).strip():
                        raise UserError(_("Please enter the Study Manager Notes explaining the return reason before returning."))
                elif rec.project_path == 'cities' or stage_sel == 'city_study_approval':
                    if not rec.cities_study_manager_approval:
                        raise UserError(_("Please fill in the Study Manager Approval decision before returning."))
                    if rec.cities_study_manager_approval != 'incomplete':
                        raise UserError(_("You cannot return the study when the approval decision is 'Completed'. The approval decision must be 'Incomplete'."))
                    if not rec.cities_study_manager_note or not str(rec.cities_study_manager_note).strip():
                        raise UserError(_("Please enter the Study Manager Notes explaining the return reason before returning."))

            if method_name == 'action_accept':
                if stage_sel == 'entry_screen':
                    sync_vals = {}
                    fields_to_sync = [
                        'customer_intent', 'customer_intent_rel', 'partner_id', 'customer_role_rel',
                        'partner_mobile', 'entered_by_id', 'entered_by_email', 'city', 'district_id',
                        'property_type', 'property_usage_rel', 'location_url',
                        'requires_technical_offer', 'owner_type', 'customer_price_per_sqm',
                        'has_income', 'current_income', 'plan_number', 'listing_date', 'entered_notes',
                    ]
                    for fname in fields_to_sync:
                        if fname in rec._fields and getattr(rec, fname):
                            fld = rec._fields[fname]
                            if fld.type == 'many2one':
                                sync_vals[fname] = getattr(rec, fname).id
                            elif fld.type == 'many2many':
                                sync_vals[fname] = [(6, 0, getattr(rec, fname).ids)]
                            else:
                                sync_vals[fname] = getattr(rec, fname)
                    if rec.property_attachment_ids:
                        sync_vals['property_attachment_ids'] = [(6, 0, rec.property_attachment_ids.ids)]
                    if sync_vals:
                        targets.with_context(bypass_portfolio_batch=True).write(sync_vals)

                elif stage_sel == 'define_project_path_assign_analyst':
                    sync_vals = {}
                    if rec.project_path:
                        sync_vals['project_path'] = rec.project_path
                    if rec.project_path_rel:
                        sync_vals['project_path_rel'] = rec.project_path_rel.id
                    if rec.is_authorized_property:
                        sync_vals['is_authorized_property'] = rec.is_authorized_property
                    if rec.is_authorized_property == 'no' and rec.rejection_reason:
                        sync_vals['rejection_reason'] = rec.rejection_reason
                    elif rec.is_authorized_property == 'return_to_lister' and rec.return_to_lister_note:
                        sync_vals['return_to_lister_note'] = rec.return_to_lister_note
                    p_code = (rec.project_path_rel.code if rec.project_path_rel else False) or rec.project_path
                    if p_code == 'specialized':
                        if rec.detailed_analyst_id:
                            sync_vals['detailed_analyst_id'] = rec.detailed_analyst_id.id
                        sync_vals['analyst_id'] = False
                    elif p_code in ('standard', 'cities'):
                        if rec.analyst_id:
                            sync_vals['analyst_id'] = rec.analyst_id.id
                        sync_vals['detailed_analyst_id'] = False
                    if sync_vals:
                        targets.with_context(bypass_portfolio_batch=True).write(sync_vals)

                elif stage_sel == 'city_study_analyst':
                    sync_vals = {}
                    fields_to_sync = [
                        'area', 'gps_coordinates', 'industrial_city', 'allocation_fees',
                        'annual_financial_fee', 'previous_activity', 'facility_investor',
                        'investor_contact_number', 'has_movables', 'equipment', 'vehicles',
                        'machinery', 'systems', 'analyst_notes', 'coordinates_kmz',
                        'coordinates_kmz_name', 'current_income_file', 'current_income_file_name',
                    ]
                    for fname in fields_to_sync:
                        if fname in rec._fields and getattr(rec, fname):
                            fld = rec._fields[fname]
                            if fld.type == 'many2one':
                                sync_vals[fname] = getattr(rec, fname).id
                            elif fld.type == 'many2many':
                                sync_vals[fname] = [(6, 0, getattr(rec, fname).ids)]
                            else:
                                sync_vals[fname] = getattr(rec, fname)
                    if rec.facility_photo_ids:
                        sync_vals['facility_photo_ids'] = [(6, 0, rec.facility_photo_ids.ids)]
                    if rec.rent_contract_ids:
                        sync_vals['rent_contract_ids'] = [(6, 0, rec.rent_contract_ids.ids)]
                    if sync_vals:
                        targets.with_context(bypass_portfolio_batch=True).write(sync_vals)

                elif stage_sel in ('study_approval', 'detailed_study_approval_eanfaz'):
                    sync_vals = {}
                    if rec.standard_study_manager_approval:
                        sync_vals['standard_study_manager_approval'] = rec.standard_study_manager_approval
                    if rec.standard_study_manager_approval_rel:
                        sync_vals['standard_study_manager_approval_rel'] = rec.standard_study_manager_approval_rel.id
                    if rec.specialized_study_manager_approval:
                        sync_vals['specialized_study_manager_approval'] = rec.specialized_study_manager_approval
                    if rec.specialized_study_manager_note:
                        sync_vals['specialized_study_manager_note'] = rec.specialized_study_manager_note
                    if rec.standard_study_manager_note:
                        sync_vals['standard_study_manager_note'] = rec.standard_study_manager_note
                    if sync_vals:
                        targets.with_context(bypass_portfolio_batch=True).write(sync_vals)

                elif stage_sel == 'city_study_approval':
                    sync_vals = {}
                    if rec.cities_study_manager_approval:
                        sync_vals['cities_study_manager_approval'] = rec.cities_study_manager_approval
                    if rec.cities_study_manager_note:
                        sync_vals['cities_study_manager_note'] = rec.cities_study_manager_note
                    if sync_vals:
                        targets.with_context(bypass_portfolio_batch=True).write(sync_vals)

                elif stage_sel == 'committee_decision':
                    sync_vals = {}
                    if rec.committee_decision:
                        sync_vals['committee_decision'] = rec.committee_decision
                    if rec.committee_decision_rel:
                        sync_vals['committee_decision_rel'] = rec.committee_decision_rel.id
                    if sync_vals:
                        targets.with_context(bypass_portfolio_batch=True).write(sync_vals)

                elif stage_sel == 'sale_manager_decision':
                    sync_vals = {}
                    if rec.sales_manager_approval:
                        sync_vals['sales_manager_approval'] = rec.sales_manager_approval
                    if rec.sales_manager_approval_rel:
                        sync_vals['sales_manager_approval_rel'] = rec.sales_manager_approval_rel.id
                    if rec.auctions_manager_approval:
                        sync_vals['auctions_manager_approval'] = rec.auctions_manager_approval
                    if rec.auctions_manager_approval_rel:
                        sync_vals['auctions_manager_approval_rel'] = rec.auctions_manager_approval_rel.id
                    if sync_vals:
                        targets.with_context(bypass_portfolio_batch=True).write(sync_vals)

                elif stage_sel == 'contract_completion':
                    sync_vals = {}
                    if rec.direct_sale_contract_status:
                        sync_vals['direct_sale_contract_status'] = rec.direct_sale_contract_status
                    if rec.auction_contract_status:
                        sync_vals['auction_contract_status'] = rec.auction_contract_status
                    if sync_vals:
                        targets.with_context(bypass_portfolio_batch=True).write(sync_vals)

                elif stage_sel in ('detailed_study_analyst', 'studies_supervisor_eanfaz'):
                    sync_vals = {}
                    if rec.detailed_analyst_id:
                        sync_vals['detailed_analyst_id'] = rec.detailed_analyst_id.id
                    if rec.is_assign_detailed_study:
                        sync_vals['is_assign_detailed_study'] = rec.is_assign_detailed_study
                    if getattr(rec, 'studies_supervisor_data_complete', False):
                        sync_vals['studies_supervisor_data_complete'] = rec.studies_supervisor_data_complete
                    if sync_vals:
                        targets.with_context(bypass_portfolio_batch=True).write(sync_vals)

            elif method_name in ('move_to_entry_archive', 'action_standard_study_reject_and_archive'):
                sync_vals = {}
                if rec.is_authorized_property:
                    sync_vals['is_authorized_property'] = rec.is_authorized_property
                if rec.rejection_reason:
                    sync_vals['rejection_reason'] = rec.rejection_reason
                if getattr(rec, 'standard_study_manager_note', False):
                    sync_vals['standard_study_manager_note'] = rec.standard_study_manager_note
                if sync_vals:
                    targets.with_context(bypass_portfolio_batch=True, bypass_archive_check=True).write(sync_vals)

            elif method_name == 'move_to_deferred_opportunities_archive':
                sync_vals = {}
                if getattr(rec, 'deferred_opportunity_reason', False):
                    sync_vals['deferred_opportunity_reason'] = rec.deferred_opportunity_reason
                if sync_vals:
                    targets.with_context(bypass_portfolio_batch=True, bypass_archive_check=True).write(sync_vals)

            elif method_name == 'action_return_to_lister':
                sync_vals = {}
                if rec.is_authorized_property:
                    sync_vals['is_authorized_property'] = rec.is_authorized_property
                if rec.return_to_lister_note:
                    sync_vals['return_to_lister_note'] = rec.return_to_lister_note
                if sync_vals:
                    targets.with_context(bypass_portfolio_batch=True).write(sync_vals)


            elif method_name == 'action_return_to_project_manager_eanfaz':
                sync_vals = {}
                if getattr(rec, 'notes_supervisor_study', False):
                    sync_vals['notes_supervisor_study'] = rec.notes_supervisor_study
                if getattr(rec, 'studies_supervisor_data_complete', False):
                    sync_vals['studies_supervisor_data_complete'] = rec.studies_supervisor_data_complete
                if sync_vals:
                    targets.with_context(bypass_portfolio_batch=True).write(sync_vals)

            elif method_name == 'send_email_to_detailed_study':
                sync_vals = {}
                if rec.detailed_analyst_id:
                    sync_vals['detailed_analyst_id'] = rec.detailed_analyst_id.id
                if rec.is_assign_detailed_study:
                    sync_vals['is_assign_detailed_study'] = rec.is_assign_detailed_study
                if sync_vals:
                    targets.with_context(bypass_portfolio_batch=True).write(sync_vals)

            # 2. Call method on each target
            for target in targets:
                target_method = getattr(target.with_context(bypass_portfolio_batch=True), method_name, None)
                if target_method and callable(target_method):
                    try:
                        target_method(*args, **kwargs)
                        executed_targets |= target
                        target.message_post(body=_(
                            "Batch Portfolio Action executed from property '%s' (%s). Action: %s"
                        ) % (rec.entrie_name or rec.id, rec.portfolio_id.name or '', act_name))
                    except Exception as e:
                        error_msg = e.args[0] if (e.args and isinstance(e.args[0], str)) else str(e)
                        raise UserError(_(
                            "Cannot complete action '%(action)s' on batch property '%(property)s':\n\n%(error)s"
                        ) % {
                            'action': act_name,
                            'property': target.entrie_name or target.id,
                            'error': error_msg,
                        })

            # 3. Clean up batch fields on targets as well as master
            for target in executed_targets:
                target.with_context(bypass_portfolio_batch=True, bypass_archive_check=True).write({
                    'enable_portfolio_batch_action': False,
                    'batch_portfolio_entry_ids': [(5, 0, 0)],
                })

            # 4. Log chatter on portfolio
            if rec.portfolio_id and executed_targets:
                target_names = ", ".join(filter(None, executed_targets.mapped('entrie_name')))
                rec.portfolio_id.message_post(body=_(
                    "Batch Portfolio Action '%s' executed on %d properties (Source: %s, Targets: %s)."
                ) % (act_name, len(executed_targets) + 1, rec.entrie_name or rec.id, target_names))

            # 5. Clean up batch fields on source record
            rec.with_context(bypass_portfolio_batch=True, bypass_archive_check=True).write({
                'enable_portfolio_batch_action': False,
                'batch_portfolio_entry_ids': [(5, 0, 0)],
            })

        return executed_targets

    def _execute_with_portfolio_batch(self, method_name, super_method, *args, **kwargs):
        executed_targets = self._replicate_batch_portfolio_action(method_name, *args, **kwargs)
        res = super_method(*args, **kwargs) if callable(super_method) else True
        if executed_targets and res is True and len(self) == 1:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Batch Action Completed"),
                    'message': _("Successfully applied action to %d properties in portfolio '%s'.") % (
                        len(executed_targets) + 1, self.portfolio_id.name or ''
                    ),
                    'type': 'success',
                    'sticky': False,
                }
            }
        return res

    def action_accept(self):
        super_method = getattr(super(), 'action_accept', None)
        return self._execute_with_portfolio_batch('action_accept', super_method)

    def action_send_to_deputy_studies_manager(self):
        super_method = getattr(super(), 'action_send_to_deputy_studies_manager', None)
        return self._execute_with_portfolio_batch('action_send_to_deputy_studies_manager', super_method)

    def action_deputy_return_to_negotiator(self):
        super_method = getattr(super(), 'action_deputy_return_to_negotiator', None)
        return self._execute_with_portfolio_batch('action_deputy_return_to_negotiator', super_method)

    def return_to_analyst(self):
        super_method = getattr(super(), 'return_to_analyst', None)
        return self._execute_with_portfolio_batch('return_to_analyst', super_method)

    def action_return_to_lister(self):
        super_method = getattr(super(), 'action_return_to_lister', None)
        return self._execute_with_portfolio_batch('action_return_to_lister', super_method)

    def action_standard_study_reject_and_archive(self):
        super_method = getattr(super(), 'action_standard_study_reject_and_archive', None)
        return self._execute_with_portfolio_batch('action_standard_study_reject_and_archive', super_method)

    def send_email_to_detailed_study(self):
        super_method = getattr(super(), 'send_email_to_detailed_study', None)
        return self._execute_with_portfolio_batch('send_email_to_detailed_study', super_method)

    def commercial_sector_manager_approval_path(self):
        super_method = getattr(super(), 'commercial_sector_manager_approval_path', None)
        return self._execute_with_portfolio_batch('commercial_sector_manager_approval_path', super_method)

    def commercial_sector_manager_declined(self):
        super_method = getattr(super(), 'commercial_sector_manager_declined', None)
        return self._execute_with_portfolio_batch('commercial_sector_manager_declined', super_method)

    def move_to_entry_archive(self):
        super_method = getattr(super(), 'move_to_entry_archive', None)
        return self._execute_with_portfolio_batch('move_to_entry_archive', super_method)

    def move_to_deferred_opportunities_archive(self):
        super_method = getattr(super(), 'move_to_deferred_opportunities_archive', None)
        return self._execute_with_portfolio_batch('move_to_deferred_opportunities_archive', super_method)

    def move_to_partners_screen(self):
        super_method = getattr(super(), 'move_to_partners_screen', None)
        return self._execute_with_portfolio_batch('move_to_partners_screen', super_method)

    def rejecte_owner_decision(self):
        super_method = getattr(super(), 'rejecte_owner_decision', None)
        return self._execute_with_portfolio_batch('rejecte_owner_decision', super_method)

    def reactivate_deferred_opportunity(self):
        super_method = getattr(super(), 'reactivate_deferred_opportunity', None)
        return self._execute_with_portfolio_batch('reactivate_deferred_opportunity', super_method)

    def action_return_to_analyst_eanfaz(self):
        super_method = getattr(super(), 'action_return_to_analyst_eanfaz', None)
        return self._execute_with_portfolio_batch('action_return_to_analyst_eanfaz', super_method)

    def action_return_to_project_manager_eanfaz(self):
        super_method = getattr(super(), 'action_return_to_project_manager_eanfaz', None)
        return self._execute_with_portfolio_batch('action_return_to_project_manager_eanfaz', super_method)

    @api.onchange('has_portfolio')
    def _onchange_has_portfolio(self):
        if not self.has_portfolio:
            self.portfolio_id = False

    @api.onchange('portfolio_id')
    def _onchange_portfolio_id(self):
        if self.portfolio_id:
            self.has_portfolio = True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('portfolio_id') and not vals.get('has_portfolio'):
                vals['has_portfolio'] = True
            elif vals.get('has_portfolio') is False:
                vals['portfolio_id'] = False
        records = super().create(vals_list)

        ports = records.mapped('portfolio_id')
        if ports:
            ports._compute_stage_ids()

        if not self.env.context.get('bypass_portfolio_notify'):
            new_port_props = defaultdict(list)
            for rec in records:
                if rec.portfolio_id:
                    prop_name = rec.entrie_name or f"Listing #{rec.id}"
                    new_port_props[rec.portfolio_id].append((rec, prop_name))

            for new_port, items in new_port_props.items():
                prop_names = [item[1] for item in items]
                combined_names = ", ".join(filter(None, prop_names))
                new_port.message_post(body=_("Property (%s) was added to portfolio properties.") % combined_names)
                for entry, p_name in items:
                    entry.message_post(body=_("Property was added to study portfolio (%s).") % (new_port.name or new_port.reference))

        return records

    def write(self, vals):
        if vals.get('has_portfolio') is False:
            vals['portfolio_id'] = False
        elif vals.get('portfolio_id') and 'has_portfolio' not in vals:
            vals['has_portfolio'] = True

        old_ports = {rec.id: rec.portfolio_id for rec in self} if ('portfolio_id' in vals or 'stage_id' in vals) else {}
        old_stages = {rec.id: rec.stage_id for rec in self}

        res = super().write(vals)

        # Ensure total price consistency on records if meter price is updated
        if not self.env.context.get('bypass_portfolio_price_calc'):
            for rec in self:
                price_updates = {}
                rec_area = rec.area_sqm or rec.area or 0.0
                if 'price_per_meter' in vals and 'final_property_price' not in vals:
                    price_updates['final_property_price'] = rec_area * (vals['price_per_meter'] or 0.0)
                if 'detailed_price_per_meter' in vals and 'detailed_final_property_price' not in vals:
                    price_updates['detailed_final_property_price'] = rec_area * (vals['detailed_price_per_meter'] or 0.0)
                if 'final_owner_price_per_meter' in vals and 'final_owner_price' not in vals:
                    price_updates['final_owner_price'] = rec_area * (vals['final_owner_price_per_meter'] or 0.0)
                if 'manager_negotiator_final_owner_price_per_meter' in vals and 'manager_negotiator_final_owner_price' not in vals:
                    price_updates['manager_negotiator_final_owner_price'] = rec_area * (vals['manager_negotiator_final_owner_price_per_meter'] or 0.0)
                if price_updates:
                    super(Entries, rec.with_context(bypass_portfolio_price_calc=True)).write(price_updates)

        # Batch replication to selected portfolio properties upon save
        if not self.env.context.get('bypass_portfolio_batch'):
            for rec in self:
                if rec.enable_portfolio_batch_action and rec.batch_portfolio_entry_ids:
                    old_stage = old_stages.get(rec.id)
                    valid_peers = rec._get_batch_peer_entries(stage=old_stage)
                    targets = rec.batch_portfolio_entry_ids.filtered(lambda t: t.id in valid_peers.ids)
                    if not targets:
                        continue

                    # 1. Check permissions on all targets
                    for target in targets:
                        rec._check_batch_portfolio_permissions(target)

                    # 2. Replicate modified / stage fields
                    replicated_count = 0
                    for target in targets:
                        target_vals = rec._get_replicated_field_values(target, vals=vals)
                        if target_vals:
                            target.with_context(bypass_portfolio_batch=True, bypass_archive_check=True).write(target_vals)
                            if 'stage_id' in target_vals:
                                target.message_post(body=_(
                                    "Stage updated to '%s' via batch action from property '%s'."
                                ) % (target.stage_id.name or '', rec.entrie_name or rec.id))
                            replicated_count += 1

                    # 3. Notification on chatter
                    if replicated_count and not self.env.context.get('bypass_portfolio_notify') and rec.portfolio_id:
                        target_names = ", ".join(filter(None, targets.mapped('entrie_name')))
                        rec.portfolio_id.message_post(body=_(
                            "Batch save: Changes from property '%s' replicated to %d properties: %s"
                        ) % (rec.entrie_name or rec.id, len(targets), target_names))

                    # 4. If stage_id changed, clean up batch fields on targets and source
                    if 'stage_id' in vals and replicated_count:
                        for target in targets:
                            target.with_context(bypass_portfolio_batch=True, bypass_archive_check=True).write({
                                'enable_portfolio_batch_action': False,
                                'batch_portfolio_entry_ids': [(5, 0, 0)],
                            })
                        super(Entries, rec.with_context(bypass_portfolio_batch=True, bypass_archive_check=True)).write({
                            'enable_portfolio_batch_action': False,
                            'batch_portfolio_entry_ids': [(5, 0, 0)],
                        })

        if 'stage_id' in vals or 'portfolio_id' in vals:
            affected_ports = self.env['study.portfolio']
            for port in old_ports.values():
                if port:
                    affected_ports |= port
            affected_ports |= self.mapped('portfolio_id')
            if affected_ports:
                affected_ports.exists()._compute_stage_ids()

        if 'stage_id' in vals:
            completed_stage = self.env.ref('bussma_system.completed', raise_if_not_found=False)
            city_study_completed_stage = self.env.ref('bussma_system.city_study_completed', raise_if_not_found=False)
            if (completed_stage and vals.get('stage_id') == completed_stage.id) or \
               (city_study_completed_stage and vals.get('stage_id') == city_study_completed_stage.id):
                for rec in self:
                    if rec.sale_auction_id and rec.portfolio_id:
                        rec._sync_sale_auction_portfolio_project()

        if 'portfolio_id' in vals:
            for rec in self:
                if rec.sale_auction_id:
                    if rec.sale_auction_id.portfolio_id != rec.portfolio_id:
                        rec.sale_auction_id.write({
                            'has_portfolio': bool(rec.portfolio_id),
                            'portfolio_id': rec.portfolio_id.id if rec.portfolio_id else False,
                        })
                    rec._sync_sale_auction_portfolio_project()

            if not self.env.context.get('bypass_portfolio_notify'):
                old_port_props = defaultdict(list)
                new_port_props = defaultdict(list)

                for rec in self:
                    old_port = old_ports.get(rec.id)
                    new_port = rec.portfolio_id
                    prop_name = rec.entrie_name or f"Listing #{rec.id}"

                    if old_port and old_port != new_port:
                        old_port_props[old_port].append((rec, prop_name))
                    if new_port and old_port != new_port:
                        new_port_props[new_port].append((rec, prop_name))

                for old_port, items in old_port_props.items():
                    prop_names = [item[1] for item in items]
                    combined_names = ", ".join(filter(None, prop_names))
                    old_port.message_post(body=_("Property (%s) was removed from portfolio properties.") % combined_names)
                    for entry, p_name in items:
                        entry.message_post(body=_("Property was removed from study portfolio (%s).") % (old_port.name or old_port.reference))

                for new_port, items in new_port_props.items():
                    prop_names = [item[1] for item in items]
                    combined_names = ", ".join(filter(None, prop_names))
                    new_port.message_post(body=_("Property (%s) was added to portfolio properties.") % combined_names)
                    for entry, p_name in items:
                        entry.message_post(body=_("Property was added to study portfolio (%s).") % (new_port.name or new_port.reference))

        return res

    def action_assign_to_portfolio(self):
        if not self._is_portfolio_assignment_manager():
            raise UserError(_("You do not have permission to assign properties to a study portfolio."))
        portfolio_id = self.env.context.get('portfolio_to_assign')
        if portfolio_id and self:
            self.with_context(bypass_portfolio_assignment_check=True).write({
                'has_portfolio': True,
                'portfolio_id': portfolio_id,
            })
        return {'type': 'ir.actions.act_window_close'}

    def _is_city_entry(self):
        """Check if entry belongs to the Cities path."""
        self.ensure_one()
        city_req_types = [
            self.env.ref('bussma_system.city_study', raise_if_not_found=False),
            self.env.ref('bussma_system.direct_sale_city_study', raise_if_not_found=False),
        ]
        city_req_type_ids = [t.id for t in city_req_types if t]
        p_code = (self.project_path_rel.code if hasattr(self, 'project_path_rel') and self.project_path_rel else False) or self.project_path

        if p_code == 'cities':
            return True
        if self.request_type_id:
            if self.request_type_id.id in city_req_type_ids:
                return True
            req_name = (self.request_type_id.with_context(lang='en_US').name or self.request_type_id.name or '').strip().lower()
            if req_name in ['city study', 'cities', 'city studies']:
                return True
        if self.stage_id and self.stage_id.project_stage_selection in ['city_study_analyst', 'city_study_approval', 'city_study_completed']:
            return True
        return False

    def _find_matching_bussma_project(self, target_project_type=False):
        """Find a bussma.project matching the study portfolio name of this entry."""
        self.ensure_one()
        portfolio = self.portfolio_id
        if not portfolio or not portfolio.name:
            return False
        portfolio_name = portfolio.name.strip()
        if not portfolio_name:
            return False

        if target_project_type:
            # 1. Exact name and matching project_type
            proj = self.env['bussma.project'].search([
                ('name', '=', portfolio_name),
                ('project_type', '=', target_project_type),
            ], limit=1)
            if proj:
                return proj

            # 2. Case-insensitive name and matching project_type
            proj = self.env['bussma.project'].search([
                ('name', '=ilike', portfolio_name),
                ('project_type', '=', target_project_type),
            ], limit=1)
            if proj:
                return proj

            # When target_project_type is provided, NEVER match a project with a different project_type!
            return False

        # Fallback if no target_project_type specified:
        proj = self.env['bussma.project'].search([
            ('name', '=', portfolio_name),
        ], limit=1)
        if proj:
            return proj

        proj = self.env['bussma.project'].search([
            ('name', '=ilike', portfolio_name),
        ], limit=1)
        return proj or False

    def _sync_sale_auction_portfolio_project(self):
        """Update existing sale_auction_id project to matching portfolio project if in basic project."""
        self.ensure_one()
        if not self.sale_auction_id:
            return
        portfolio = self.portfolio_id
        current_project = self.sale_auction_id.project_id
        is_basic = not current_project or current_project.is_basic

        comm_decision = (self.committee_decision_rel.code if hasattr(self, 'committee_decision_rel') and self.committee_decision_rel else False) or self.committee_decision

        target_project_type = False
        basic_xml_id = False
        if self._is_city_entry():
            target_project_type = 'city'
            basic_xml_id = 'sales_and_auction_management.project_cities_basic'
            city_type = self.env.ref('sales_and_auction_management.p2_type_auction_city', raise_if_not_found=False)
            city_stage = self.env.ref('sales_and_auction_management.p2_stage_auction_city_portfolio', raise_if_not_found=False)
            if city_type and self.sale_auction_id.request_type_id != city_type:
                vals_to_write['request_type_id'] = city_type.id
                vals_to_write['auction_project_path'] = 'city'
            if city_stage and not self.sale_auction_id.stage_id:
                vals_to_write['stage_id'] = city_stage.id
        elif comm_decision == 'auction':
            target_project_type = 'auction_pvt'
            basic_xml_id = 'sales_and_auction_management.project_auctions_pvt_basic'
            pvt_type = self.env.ref('sales_and_auction_management.p2_type_auction_pvt', raise_if_not_found=False)
            pvt_stage = self.env.ref('sales_and_auction_management.p2_stage_auction_pvt_portfolio', raise_if_not_found=False)
            if pvt_type and self.sale_auction_id.request_type_id != pvt_type:
                vals_to_write['request_type_id'] = pvt_type.id
                vals_to_write['auction_project_path'] = 'private'
            if pvt_stage and not self.sale_auction_id.stage_id:
                vals_to_write['stage_id'] = pvt_stage.id
        elif comm_decision == 'direct_sale':
            target_project_type = 'sales'
            basic_xml_id = 'sales_and_auction_management.project_sales_basic'
            sales_type = self.env.ref('sales_and_auction_management.p2_type_sales', raise_if_not_found=False)
            sales_stage = self.env.ref('sales_and_auction_management.p2_stage_sales_direct_mgmt', raise_if_not_found=False)
            if sales_type and self.sale_auction_id.request_type_id != sales_type:
                vals_to_write['request_type_id'] = sales_type.id
            if sales_stage and not self.sale_auction_id.stage_id:
                vals_to_write['stage_id'] = sales_stage.id

        if not target_project_type and self.sale_auction_id:
            sa = self.sale_auction_id
            target_project_type = sa.project_type_selection
            type_basic_map = {
                'sales': 'sales_and_auction_management.project_sales_basic',
                'auction_pvt': 'sales_and_auction_management.project_auctions_pvt_basic',
                'city': 'sales_and_auction_management.project_cities_basic',
                'auction_enf': 'sales_and_auction_management.project_auctions_enf_basic',
            }
            if target_project_type:
                basic_xml_id = type_basic_map.get(target_project_type)

        vals_to_write = {}
        if hasattr(self.sale_auction_id, 'portfolio_id'):
            if portfolio and self.sale_auction_id.portfolio_id != portfolio:
                vals_to_write['portfolio_id'] = portfolio.id
                vals_to_write['has_portfolio'] = True
            elif not portfolio and self.sale_auction_id.portfolio_id:
                vals_to_write['portfolio_id'] = False
                vals_to_write['has_portfolio'] = False

        if target_project_type:
            matched_project = self._find_matching_bussma_project(target_project_type=target_project_type) if (portfolio and portfolio.name) else False
            if matched_project:
                if current_project != matched_project:
                    vals_to_write['project_id'] = matched_project.id
            else:
                # If no matching project found, or current project is of the wrong project_type, or basic:
                # assign to the basic project corresponding to target_project_type!
                if not current_project or is_basic or (current_project.project_type != target_project_type):
                    basic_proj = self.env.ref(basic_xml_id, raise_if_not_found=False) if basic_xml_id else False
                    if basic_proj and current_project != basic_proj:
                        vals_to_write['project_id'] = basic_proj.id

        if vals_to_write:
            self.sale_auction_id.write(vals_to_write)

    def action_create_sale_auction(self):
        res = super().action_create_sale_auction()
        for rec in self:
            if rec.sale_auction_id:
                rec._sync_sale_auction_portfolio_project()
        return res

    @api.model
    def _is_study_manager(self, user=None):
        """Check if user has manager access to study entries."""
        user = user or self.env.user
        return bool(
            user.has_group('base.group_system') or
            user.has_group('bussma_system.group_commercial_sector_manager') or
            user.has_group('bussma_system.group_auctions_manager') or
            user.has_group('bussma_system.group_sales_manager') or
            user.has_group('bussma_system.group_studies_manager') or
            user.has_group('bussma_system.group_deputy_studies_manager') or
            user.has_group('bussma_system.group_committee_member') or
            user.has_group('bussma_system.group_rnd_manager')
        )

    @api.model
    def _get_study_accessible_entries_domain(self, user=None):
        """Returns the domain of entries accessible to the user based on web_search_read logic."""
        user = user or self.env.user
        if self._is_study_manager(user):
            return [(1, '=', 1)]

        if user.has_group('bussma_system.group_city_studies_manager') and not (
            user.has_group('bussma_system.group_studies_manager') or
            user.has_group('bussma_system.group_deputy_studies_manager') or
            user.has_group('base.group_system')
        ):
            return [('project_path', '=', 'cities')]

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

        t_pm = [('assigned_project_manager', '=', user.id)]
        t_creator = [('create_uid', '=', user.id)]
        t_neg = [
            ('assigned_negotiator', '=', user.id),
            ('project_stage_selection', '=', 'negotiator'),
            ('is_sent_to_deputy_studies_manager', '=', False)
        ]
        t_ds_cm = [('direct_sale_assigned_contract_manager', '=', user.id)]
        t_auc_cm = [('auction_assigned_contract_manager', '=', user.id)]
        t_study = [
            ('project_stage_selection', 'in', study_stages),
            '|', '|',
            ('analyst_id', '=', user.id),
            ('detailed_analyst_id', '=', user.id),
            ('city_analyst_id', '=', user.id)
        ]
        t_eanfaz = [
            ('project_stage_selection', 'in', eanfaz_stages),
            ('detailed_analyst_id', '=', user.id)
        ]

        domain_parts = [t_pm, t_creator, t_neg, t_ds_cm, t_auc_cm, t_study, t_eanfaz]

        if 'bussma.opportunity' in self.env:
            is_opp_manager = user.has_group('marketing_opportunity_management.group_opportunity_manager')
            is_mkt_supervisor = user.has_group('marketing_opportunity_management.group_marketing_supervisor')
            if is_opp_manager or is_mkt_supervisor:
                domain_parts.append([
                    '|',
                    ('requires_technical_offer', '=', 'yes'),
                    ('opportunity_id', '!=', False)
                ])

        return expression.OR(domain_parts)

    def _check_study_entry_access(self, user=None):
        """Check if user has access to this entry based on web_search_read rules."""
        self.ensure_one()
        user = user or self.env.user
        if self._is_study_manager(user):
            return True
        if user.has_group('bussma_system.group_city_studies_manager') and self.project_path == 'cities':
            return True
        domain = self._get_study_accessible_entries_domain(user)
        return bool(self.sudo().search_count([('id', '=', self.id)] + domain))

    def web_read(self, specification):
        """Protect against unauthorized reads on form view."""
        user = self.env.user
        if not self.env.su and not self._is_study_manager(user) and not self.env.context.get('bypass_entry_visibility_check'):
            is_form_view = self.env.context.get('view_type') == 'form' or \
                           self.env.context.get('params', {}).get('view_type') == 'form'
            if is_form_view:
                for rec in self:
                    if not rec._check_study_entry_access(user):
                        raise UserError(_("You do not have permission to view this property."))
        return super().web_read(specification)

    def action_remove_from_portfolio(self):
        if not self._is_portfolio_assignment_manager():
            raise UserError(_("You do not have permission to remove properties from a study portfolio."))
        for rec in self:
            if not rec._check_study_entry_access():
                raise UserError(_("You do not have permission to modify this property."))
            rec.with_context(bypass_portfolio_assignment_check=True).write({
                'has_portfolio': False,
                'portfolio_id': False,
            })
        return True

    def unlink(self):
        ports = self.mapped('portfolio_id')
        res = super().unlink()
        if ports:
            ports.exists()._compute_stage_ids()
        return res

    def _is_eanfaz_study(self):
        """Check if this entry is an Eanfaz detailed study."""
        self.ensure_one()
        # 1. Check request_type_id XML ref
        eanfaz_type = self.env.ref('sales_and_auction_management.detailed_study_eanfaz', raise_if_not_found=False)
        if eanfaz_type and self.request_type_id and self.request_type_id.id == eanfaz_type.id:
            return True

        # 2. Check request_type_id name (normalize Arabic hamzas and English case)
        if self.request_type_id:
            req_name = (self.request_type_id.name or '').strip().lower()
            norm_name = req_name.replace('\u0625', '\u0627').replace('\u0623', '\u0627').replace('\u0622', '\u0627')
            if 'eanfaz' in norm_name or '\u0627\u0646\u0641\u0627\u0630' in norm_name:
                return True

        # 3. Check stage selection on stage_id or project_stage_selection field
        stage_sel = self.stage_id.project_stage_selection if self.stage_id else (getattr(self, 'project_stage_selection', '') or '')
        if stage_sel and 'eanfaz' in str(stage_sel).lower():
            return True

        # 4. Check if linked to an auction/sales entry with enf path
        if getattr(self, 'sale_auction_id', False):
            path = getattr(self.sale_auction_id, 'auction_project_path', False)
            if path in ('enf', 'auction_enf', 'enforcement'):
                return True

        return False

    def get_formview_id(self, access_uid=None):
        """Return the appropriate form view depending on request_type_id."""
        if len(self) == 1 and self._is_eanfaz_study():
            eanfaz_form = self.env.ref('sales_and_auction_management.detailed_study_eanfaz_form_view', raise_if_not_found=False)
            if not eanfaz_form:
                eanfaz_form = self.env['ir.ui.view'].search([
                    ('model', '=', 'entries'),
                    ('name', '=', 'entries.detailed.study.eanfaz.form.view'),
                ], limit=1)
            if eanfaz_form:
                return eanfaz_form.id

        standard_form = self.env.ref('bussma_system.entries_form_view', raise_if_not_found=False)
        if standard_form:
            return standard_form.id
        return super().get_formview_id(access_uid=access_uid)

    def get_formview_action(self, access_uid=None):
        """Ensure get_formview_action uses the correct action and form view."""
        res = super().get_formview_action(access_uid=access_uid)
        view_id = self.get_formview_id(access_uid=access_uid)
        if view_id:
            res['views'] = [(view_id, 'form')]
        return res

    def action_open_entry_form(self):
        """Action called to open the record's specific form view dynamically."""
        self.ensure_one()
        if not self._check_study_entry_access():
            raise UserError(_("You do not have permission to view this property."))
        view_id = self.get_formview_id()
        return {
            'name': self.entrie_name or _('Property Details'),
            'type': 'ir.actions.act_window',
            'res_model': 'entries',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'new',
        }
