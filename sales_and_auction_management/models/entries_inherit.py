# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Entries(models.Model):
    _inherit = 'entries'

    sale_auction_id = fields.Many2one('sales.auction.management', string="Sales Auctions Management Entry", readonly=True, copy=False)
    has_sale_auction = fields.Boolean(compute='_compute_has_sale_auction', store=False)
    # Related fields from sales.auction.management for Eanfaz Detailed Study
    p2_auction_project_path = fields.Selection(related='sale_auction_id.auction_project_path', string="Project Path", readonly=True)
    p2_auction_category = fields.Selection(related='sale_auction_id.auction_category', string="Auction Category", readonly=True)
    p2_need_identity = fields.Selection(related='sale_auction_id.need_identity', string="Need Identity", readonly=True)
    p2_asset_number = fields.Char(related='sale_auction_id.asset_number', string="Asset Number", readonly=True)
    p2_court_decision_number = fields.Char(related='sale_auction_id.court_decision_number', string="Court Decision Number", readonly=True)
    p2_execution_applicant_name = fields.Char(related='sale_auction_id.execution_applicant_name', string="Execution Applicant Name", readonly=True)
    p2_execution_applicant_phone = fields.Char(related='sale_auction_id.execution_applicant_phone', string="Execution Applicant Phone", readonly=True)
    p2_deed_number = fields.Char(related='sale_auction_id.deed_number', string="Deed Number", readonly=True)
    p2_deed_date_hijri = fields.Char(related='sale_auction_id.deed_date_hijri', string="Deed Date (Hijri)", readonly=True)
    p2_deed_issuer = fields.Char(related='sale_auction_id.deed_issuer', string="Deed Issuer", readonly=True)
    p2_plan_number = fields.Char(related='sale_auction_id.plan_number', string="Plan Number", readonly=True)
    p2_plot_number = fields.Char(related='sale_auction_id.plot_number', string="Plot Number", readonly=True)
    p2_city = fields.Many2one('res.country.state', related='sale_auction_id.city', string="City", readonly=True)
    p2_district_id = fields.Many2one('res.city', related='sale_auction_id.district_id', string="District", readonly=True)
    p2_property_type = fields.Many2one('property.type', related='sale_auction_id.property_type', string="Property Type", readonly=True)
    p2_area_sqm = fields.Float(related='sale_auction_id.area_sqm', string="Area (SQM)", readonly=True)
    p2_location_url = fields.Char(related='sale_auction_id.location_url', string="Location URL", readonly=True)
    p2_limit_north = fields.Char(related='sale_auction_id.limit_north', string="Limit (North)", readonly=True)
    p2_length_north = fields.Float(related='sale_auction_id.length_north', string="Length (North)", readonly=True)
    p2_limit_south = fields.Char(related='sale_auction_id.limit_south', string="Limit (South)", readonly=True)
    p2_length_south = fields.Float(related='sale_auction_id.length_south', string="Length (South)", readonly=True)
    p2_limit_east = fields.Char(related='sale_auction_id.limit_east', string="Limit (East)", readonly=True)
    p2_length_east = fields.Float(related='sale_auction_id.length_east', string="Length (East)", readonly=True)
    p2_limit_west = fields.Char(related='sale_auction_id.limit_west', string="Limit (West)", readonly=True)
    p2_length_west = fields.Float(related='sale_auction_id.length_west', string="Length (West)", readonly=True)
    p2_property_description = fields.Text(related='sale_auction_id.property_description', string="Property Description", readonly=True)
    p2_property_images_url = fields.Char(related='sale_auction_id.property_images_url', string="Property Images URL", readonly=True)
    p2_project_notes = fields.Text(related='sale_auction_id.project_notes', string="Project Notes", readonly=True)
    p2_lease_contract_type = fields.Selection(related='sale_auction_id.lease_contract_type', string="Lease Contract Type", readonly=True)
    p2_has_operation_contract = fields.Boolean(related='sale_auction_id.has_operation_contract', string="Has Operation Contract", readonly=True)
    p2_lease_contract_expiry_date = fields.Date(related='sale_auction_id.lease_contract_expiry_date', string="Lease Contract Expiry Date", readonly=True)
    p2_project_manager_notes = fields.Text(related='sale_auction_id.project_manager_notes', string="Project Manager Notes", readonly=True)
    # Are there any Movable Assets?
    has_movables = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Is there any movables?", default='no')
    # Is the estimate more than 50,000 SAR?
    is_estimated_more_than_50k = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Is the estimate more than 50k SAR?")
    # Are Keys Available?
    are_keys_available = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Are keys available?")
    # Key Location?
    key_location = fields.Char(string="Key Location")
    # Property Condition
    property_condition = fields.Selection([('rented', 'Rented'), ('vacant', 'Vacant')], string="Property Condition")

    notes_supervisor_study = fields.Text(string="Notes of Supervisor Study")
    studies_supervisor_data_complete = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string="Studies Supervisor Data Complete")
    is_return_to_supervisor_study = fields.Boolean(string="Is Return to Supervisor Study")
    study_rejection_notes = fields.Text(string="Study Rejection Notes")

    def _compute_has_sale_auction(self):
        for rec in self:
            rec.has_sale_auction = bool(rec.sale_auction_id)

    def write(self, vals):
        res = super(Entries, self).write(vals)
        completed_stage = self.env.ref('bussma_system.completed', raise_if_not_found=False)
        city_study_completed_stage = self.env.ref('bussma_system.city_study_completed', raise_if_not_found=False)
        if vals.get('stage_id') and completed_stage and vals.get('stage_id') == completed_stage.id:
            for rec in self:
                if not rec.sale_auction_id:
                    rec.action_create_sale_auction()
        elif vals.get('stage_id') and city_study_completed_stage and vals.get('stage_id') == city_study_completed_stage.id:
            for rec in self:
                if not rec.sale_auction_id:
                    rec.action_create_sale_auction()
        return res

    def action_create_sale_auction(self):
        self.ensure_one()
        # Create Sales Auctions Management record if it doesn't exist
        if not self.sale_auction_id:
            initial_stage = False
            request_type = False
            auction_project_path_val = False
            project_id_val = False
            # ── Cities path: goes directly to completed without committee_decision ──
            if self.project_path == 'cities':
                initial_stage = self.env.ref('sales_and_auction_management.p2_stage_auction_city_portfolio', raise_if_not_found=False)
                request_type = self.env.ref('sales_and_auction_management.p2_type_auction_city', raise_if_not_found=False)
                project_rec = self.env.ref('sales_and_auction_management.project_cities_basic', raise_if_not_found=False)
                auction_project_path_val = 'city'
                project_id_val = project_rec.id if project_rec else False
            elif self.committee_decision == 'auction':
                initial_stage = self.env.ref('sales_and_auction_management.p2_stage_auction_pvt_portfolio', raise_if_not_found=False)
                request_type = self.env.ref('sales_and_auction_management.p2_type_auction_pvt', raise_if_not_found=False)
                project_rec = self.env.ref('sales_and_auction_management.project_auctions_pvt_basic', raise_if_not_found=False)
                auction_project_path_val = 'private'
                project_id_val = project_rec.id if project_rec else False
            elif self.committee_decision == 'direct_sale':
                initial_stage = self.env.ref('sales_and_auction_management.p2_stage_sales_direct_mgmt', raise_if_not_found=False)
                request_type = self.env.ref('sales_and_auction_management.p2_type_sales', raise_if_not_found=False)
                project_rec = self.env.ref('sales_and_auction_management.project_sales_basic', raise_if_not_found=False)
                project_id_val = project_rec.id if project_rec else False

            vals = {
                'entry_id': self.id,
                'project_id': project_id_val,
                'request_type_id': request_type.id if request_type else False,
                'entrie_name': self.entrie_name,
                'stage_id': initial_stage.id if initial_stage else False,
                'auction_project_path': auction_project_path_val if auction_project_path_val else False,
                'customer_intent': self.customer_intent,
                'partner_id': self.partner_id.id,
                'customer_role_rel': self.customer_role_rel.id,
                'owner_type': self.owner_type,
                'partner_mobile': self.partner_mobile,
                'entered_by_id': self.entered_by_id.id,
                'entered_by_email': self.entered_by_email,
                # ── Cities Study Mappings ──
                'gps_coordinates': self.gps_coordinates,
                'area': self.area,
                'industrial_city': self.industrial_city,
                'allocation_fees': self.allocation_fees,
                'annual_financial_fee': self.annual_financial_fee,
                'previous_activity': self.previous_activity,
                'facility_investor': self.facility_investor,
                'investor_contact_number': self.investor_contact_number,
                'has_movables': self.has_movables,
                'equipment': self.equipment,
                'vehicles': self.vehicles,
                'machinery': self.machinery,
                'systems': self.systems,
                'analyst_notes': self.analyst_notes,
                'facility_photo_ids': [(6, 0, self.facility_photo_ids.ids)],
                'coordinates_kmz': self.coordinates_kmz,
                'coordinates_kmz_name': self.coordinates_kmz_name,
                'current_income_file': self.current_income_file,
                'current_income_file_name': self.current_income_file_name,
                'rent_contract_ids': [(6, 0, self.rent_contract_ids.ids)],
                'company_id': self.company_id.id,
                'country_id': self.country_id.id,
                'city': self.city.id,
                'district_id': self.district_id.id,
                'property_type': self.property_type.id,
                'area_sqm': self.area_sqm,
                'property_usage_rel': self.property_usage_rel.id,
                'current_income': self.current_income,
                'currency_id': self.currency_id.id,
                'plan_number': self.plan_number,
                'deed_number': self.deed_number,
                'deed_date': self.deed_date,
                'plot_number': self.plot_number,
                'customer_price_per_sqm': self.customer_price_per_sqm,
                'location_url': self.location_url,
                'requires_technical_offer': self.requires_technical_offer,
                'entered_notes': self.entered_notes,
                'is_authorized_property': self.is_authorized_property,
                'rejection_reason': self.rejection_reason,
                'return_to_lister_note': self.return_to_lister_note,
                'project_path': self.project_path,
                'analyst_id': self.city_analyst_id.id if self.project_path == 'cities' and self.city_analyst_id else self.analyst_id.id,
                'detailed_analyst_id': self.detailed_analyst_id.id,
                'verified_income': self.verified_income,
                'expected_full_lease_income': self.expected_full_lease_income,
                'building_requirements': self.building_requirements,
                'justice_index_average': self.justice_index_average,
                'comparison_average': self.comparison_average,
                'final_property_price': self.final_property_price,
                'analyst_recommendation_preliminary': self.analyst_recommendation_preliminary,
                'properties_count': self.properties_count,
                'preliminary_study_status': self.preliminary_study_status,
                'analyst_rejection_notes': self.analyst_rejection_notes,
                'analyst_recommendation_details': self.analyst_recommendation_details,
                'detailed_building_requirements': self.detailed_building_requirements,
                'detailed_final_property_price': self.detailed_final_property_price,
                'detailed_comparison_average': self.detailed_comparison_average,
                'limit_east': self.limit_east,
                'finishing_ratio': self.finishing_ratio,
                'electricity_meters_count': self.electricity_meters_count,
                'sewage_service': self.sewage_service,
                'internal_strength_points': self.internal_strength_points,
                'current_total_income': self.current_total_income,
                'precise_plot_location_link': self.precise_plot_location_link,
                'length_east': self.length_east,
                'limit_north': self.limit_north,
                'floors_count': self.floors_count,
                'electricity_meters_numbers': self.electricity_meters_numbers,
                'water_service': self.water_service,
                'street': self.street,
                'best_property_use': self.best_property_use,
                'justice_ministry_index_average': self.justice_ministry_index_average,
                'limit_west': self.limit_west,
                'length_north': self.length_north,
                'units_count': self.units_count,
                'building_license_date': self.building_license_date,
                'electricity_service': self.electricity_service,
                'nearest_main_road': self.nearest_main_road,
                'external_weakness_points': self.external_weakness_points,
                'expected_total_income_full_rent': self.expected_total_income_full_rent,
                'property_description': self.property_description,
                'length_west': self.length_west,
                'limit_south': self.limit_south,
                'property_age_estimated': self.property_age_estimated,
                'building_license_number': self.building_license_number,
                'water_meters_count': self.water_meters_count,
                'pavement_service': self.pavement_service,
                'external_strength_points': self.external_strength_points,
                'lowest_price_per_meter_total_property': self.lowest_price_per_meter_total_property,
                'approximate_building_value_per_meter': self.approximate_building_value_per_meter,
                'building_area': self.building_area,
                'length_south': self.length_south,
                'land_nature': self.land_nature,
                'completion_certificate_issued': self.completion_certificate_issued,
                'water_meters_numbers': self.water_meters_numbers,
                'lighting_service': self.lighting_service,
                'gas_service': self.gas_service,
                'ac_service': self.ac_service,
                'internet_service': self.internet_service,
                'telecom_service': self.telecom_service,
                'security_service': self.security_service,
                'elevator_service': self.elevator_service,
                'pool_service': self.pool_service,
                'garden_service': self.garden_service,
                'parking_service': self.parking_service,
                'construction_warranty': self.construction_warranty,
                'electrical_warranty': self.electrical_warranty,
                'plumbing_warranty': self.plumbing_warranty,
                'services_description': self.services_description,
                'internal_weakness_points': self.internal_weakness_points,
                'highest_price_per_meter_total_property': self.highest_price_per_meter_total_property,
                'approximate_land_value_per_meter': self.approximate_land_value_per_meter,
                'standard_study_manager_approval': self.standard_study_manager_approval,
                'specialized_study_manager_approval': self.specialized_study_manager_approval,
                'committee_decision': self.committee_decision,
                'committee_decision_date': self.committee_decision_date,
                'marketing_duration_months': self.marketing_duration_months,
                'committe_notes': self.committe_notes,
                'sales_manager_approval': self.sales_manager_approval,
                'auctions_manager_approval': self.auctions_manager_approval,
                'final_owner_decision': self.final_owner_decision,
                'final_owner_price': self.final_owner_price,
                'manager_negotiator_final_owner_decision': self.manager_negotiator_final_owner_decision,
                'manager_negotiator_final_owner_price': self.manager_negotiator_final_owner_price,
                'is_assign_detailed_study': self.is_assign_detailed_study,
                'contract_client_name': self.contract_client_name,
                'contract_client_identity': self.contract_client_identity,
                'contract_client_birthdate': self.contract_client_birthdate,
                'contract_client_mobile': self.contract_client_mobile,
                'contract_client_role': self.contract_client_role,
                'contract_owner_name': self.contract_owner_name,
                'contract_owner_identity': self.contract_owner_identity,
                'contract_owner_birthdate': self.contract_owner_birthdate,
                'contract_owner_mobile': self.contract_owner_mobile,
                'contract_agency_deed_attachment': self.contract_agency_deed_attachment,
                'contract_agency_deed_attachment_name': self.contract_agency_deed_attachment_name,
                'contract_agreed_price': self.contract_agreed_price,
                'contract_duration': self.contract_duration,
                'rooms_count': self.rooms_count,
                'property_facade': self.property_facade,
            }

            new_sale_auction = self.env['sales.auction.management'].create(vals)
            new_sale_auction.write({'amount_matches_selling_price': True})
            self.sale_auction_id = new_sale_auction.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales and Auction Data'),
            'res_model': 'sales.auction.management',
            'res_id': self.sale_auction_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_accept(self):
        for rec in self:
            # Stage 1: Studies Supervisor
            if rec.project_stage_selection == 'studies_supervisor_eanfaz':
                if not rec.detailed_analyst_id:
                    raise UserError(_("Please assign a Detailed Analyst before proceeding."))
                stage = self.env.ref('sales_and_auction_management.stage_detailed_study_eanfaz', raise_if_not_found=False)
                rec.write({'stage_id':stage.id})
                return 
            # Stage 2: Detailed Study
            elif rec.project_stage_selection == 'detailed_study_eanfaz':
                # 2. Check detailed study fields are filled
                detailed_fields_to_check = [
                    'limit_east', 'limit_west', 'limit_north', 'limit_south',
                    'street', 'street_length', 'nearest_main_road', 'precise_plot_location_link',
                    'has_movables', 'are_keys_available', 'property_condition', 'property_usage_rel',
                    'land_nature', 'building_license_number', 'building_license_date',
                    'detailed_building_requirements',
                    'electricity_meters_numbers', 'water_meters_numbers',
                    'internal_strength_points', 'internal_weakness_points',
                    'external_strength_points', 'external_weakness_points',
                    'best_property_use', 'analyst_recommendation_details',
                    'property_description',
                    'sewage_service', 'water_service', 'electricity_service',
                    'pavement_service', 'lighting_service', 'completion_certificate_issued',
                ]
                if rec.has_movables == 'yes':
                    detailed_fields_to_check.append('is_estimated_more_than_50k')
                if rec.are_keys_available == 'yes':
                    detailed_fields_to_check.append('key_location')
                missing_detailed = [
                    f for f in detailed_fields_to_check
                    if getattr(rec, f) in (0, 0.0, False, '')
                ]
                numeric_fields_to_check = [
                    'length_east', 'length_west', 'length_north', 'length_south',
                    'building_area',
                    'electricity_meters_count', 'water_meters_count',
                    'expected_total_income_full_rent',
                    'detailed_comparison_average', 'justice_ministry_index_average',
                    'lowest_price_per_meter_total_property', 'highest_price_per_meter_total_property',
                    'approximate_building_value_per_meter', 'approximate_land_value_per_meter',
                    'detailed_final_property_price', 'finishing_ratio'
                ]
                if not rec.is_land_property_type:
                    numeric_fields_to_check.extend(['floors_count', 'units_count'])
                missing_numeric = [
                    f for f in numeric_fields_to_check
                    if getattr(rec, f) in (0, 0.0, False, '')
                ]

                all_missing = missing_detailed + missing_numeric
                if all_missing:
                    field_labels = [rec.fields_get([f])[f]['string'] for f in all_missing]
                    stage_name = rec.stage_id.name or ''
                    raise UserError(
                        _("Stage: %s\n\nThe following fields are required and must not be empty or zero:\n- %s")
                        % (stage_name, "\n- ".join(field_labels))
                    )
                # All validations passed → clear notes atomically with stage change
                stage = self.env.ref('sales_and_auction_management.stage_detailed_study_approval_eanfaz', raise_if_not_found=False)
                rec.write({
                    'stage_id': stage.id,
                    'specialized_study_manager_note': False,
                    'study_rejection_notes': False,
                })
                return

            elif rec.project_stage_selection == 'detailed_study_approval_eanfaz':
                if not rec.specialized_study_manager_approval:
                    raise UserError(_("Please fill in the Study Manager Approval decision before proceeding."))
                if rec.specialized_study_manager_approval == 'incomplete':
                    raise UserError(_("You cannot complete the study when the approval decision is 'Incomplete'."))
                stage = self.env.ref('sales_and_auction_management.stage_detailed_study_completed_eanfaz', raise_if_not_found=False)
                rec.write({'stage_id': stage.id})
                stage_auction = self.env.ref('sales_and_auction_management.p2_auction_enf_pm_appr', raise_if_not_found=False)
                
                # Copy all detailed study fields to the Sales Auctions Management record
                fields_to_copy = [
                    'studies_supervisor_data_complete',
                    'notes_supervisor_study',
                    'detailed_analyst_id',
                    'specialized_study_manager_approval',
                    'specialized_study_manager_note',
                    'limit_east', 'limit_west', 'limit_north', 'limit_south',
                    'street', 'nearest_main_road', 'precise_plot_location_link',
                    'land_nature', 'building_license_number', 'building_license_date',
                    'detailed_building_requirements',
                    'electricity_meters_numbers', 'water_meters_numbers',
                    'internal_strength_points', 'internal_weakness_points',
                    'external_strength_points', 'external_weakness_points',
                    'best_property_use', 'analyst_recommendation_details',
                    'property_description', 'property_usage_rel',
                    'sewage_service', 'water_service', 'electricity_service',
                    'pavement_service', 'lighting_service', 'completion_certificate_issued',
                    'gas_service', 'ac_service', 'internet_service', 'telecom_service',
                    'security_service', 'elevator_service', 'pool_service',
                    'garden_service', 'parking_service',
                    'construction_warranty', 'electrical_warranty',
                    'plumbing_warranty', 'services_description',
                    'length_east', 'length_west', 'length_north', 'length_south',
                    'building_area', 'floors_count', 'units_count', 'property_age_estimated',
                    'electricity_meters_count', 'water_meters_count',
                    'expected_total_income_full_rent',
                    'detailed_comparison_average', 'justice_ministry_index_average',
                    'lowest_price_per_meter_total_property', 'highest_price_per_meter_total_property',
                    'approximate_building_value_per_meter', 'approximate_land_value_per_meter',
                    'detailed_final_property_price', 'finishing_ratio', 'current_total_income',
                    'contract_client_name', 'contract_client_identity', 'contract_client_birthdate',
                    'contract_client_mobile', 'contract_client_role', 'contract_owner_name',
                    'contract_owner_identity', 'contract_owner_birthdate', 'contract_owner_mobile',
                    'contract_agency_deed_attachment', 'contract_agency_deed_attachment_name',
                    'contract_agreed_price', 'contract_duration', 'rooms_count', 'property_facade',
                    'are_keys_available', 'property_condition', 'is_estimated_more_than_50k', 'key_location',
                    'has_movables', 'street_length'
                ]
                vals = {
                    'stage_id': stage_auction.id if stage_auction else rec.sale_auction_id.stage_id.id,
                }
                for field in fields_to_copy:
                    if hasattr(rec, field) and field in rec.sale_auction_id._fields:
                        val = getattr(rec, field)
                        if hasattr(val, '_name') and hasattr(val, 'id'):
                            vals[field] = val.id
                        elif hasattr(val, '_name') and hasattr(val, 'ids'):
                            vals[field] = [(6, 0, val.ids)]
                        else:
                            vals[field] = val

                if rec.notes_supervisor_study:
                    if 'studies_supervisor_data_complete_notes' in rec.sale_auction_id._fields:
                        vals['studies_supervisor_data_complete_notes'] = rec.notes_supervisor_study
                    if 'notes_supervisor_study' in rec.sale_auction_id._fields:
                        vals['notes_supervisor_study'] = rec.notes_supervisor_study

                if rec.sale_auction_id:
                    rec.sale_auction_id.write(vals)

                    # Copy all attachments linked to this entry to the sale_auction_id record
                    attachments = self.env['ir.attachment'].search([
                        ('res_model', '=', 'entries'),
                        ('res_id', '=', rec.id)
                    ])
                    for att in attachments:
                        existing = self.env['ir.attachment'].search([
                            ('res_model', '=', 'sales.auction.management'),
                            ('res_id', '=', rec.sale_auction_id.id),
                            ('name', '=', att.name),
                            ('checksum', '=', att.checksum),
                        ], limit=1)
                        if not existing:
                            att.copy({
                                'res_model': 'sales.auction.management',
                                'res_id': rec.sale_auction_id.id,
                            })
                return 

        result = super(Entries, self).action_accept()

    def action_return_to_analyst_eanfaz(self):
        for rec in self:
            if rec.project_stage_selection == 'detailed_study_approval_eanfaz':
                if not rec.specialized_study_manager_approval:
                    raise UserError(_("Please fill in the Study Manager Approval decision before returning."))
                if rec.specialized_study_manager_approval != 'incomplete':
                    raise UserError(_("You cannot return the study when the approval decision is 'Completed'. The approval decision must be 'Incomplete'."))
                if not rec.specialized_study_manager_note or not str(rec.specialized_study_manager_note).strip():
                    raise UserError(_("Please enter the Study Manager Notes explaining the return reason before returning."))

                self.env['entries.return.log'].create({
                    'entry_id': rec.id,
                    'return_type': 'study_to_analyst',
                    'study_type_detail': 'specialized',
                    'note': rec.specialized_study_manager_note,
                })
                # Stage 2: Detailed Study (Eanfaz)
                stage = self.env.ref('sales_and_auction_management.stage_detailed_study_eanfaz', raise_if_not_found=False)
                if stage:
                    rec.write({'stage_id': stage.id})

    def action_return_to_project_manager_eanfaz(self):
        self.ensure_one()
        parent = self.sale_auction_id
        if not parent:
            raise UserError(_("No linked management record found."))
        
        target_stage = self.env.ref('sales_and_auction_management.p2_auction_enf_project_manager', raise_if_not_found=False)
        if not target_stage:
            raise UserError(_("Target stage 'Project Manager' not found."))
        if not self.notes_supervisor_study:
            raise UserError(_("Please enter supervisor notes."))
        # Change parent's stage to Project Manager
        parent.write({'stage_id': target_stage.id, 'studies_supervisor_data_complete_notes': self.notes_supervisor_study,
                                                    'studies_supervisor_data_complete': self.studies_supervisor_data_complete})
        self.is_return_to_supervisor_study = True
