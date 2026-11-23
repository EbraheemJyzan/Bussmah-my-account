# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SalesAuctionManagement(models.Model):
    _inherit = 'sales.auction.management'

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
        for rec in records:
            if rec.portfolio_id:
                rec._sync_matching_bussma_project()
        return records

    def _create_detailed_study_eanfaz(self):
        for rec in self:
            if rec.entry_id:
                return
        res = super()._create_detailed_study_eanfaz()
        for rec in self:
            if rec.portfolio_id:
                study = self.env['entries'].search([('sale_auction_id', '=', rec.id)], limit=1)
                if study:
                    vals = {
                        'has_portfolio': True,
                        'portfolio_id': rec.portfolio_id.id,
                    }
                    if not study.area_sqm and rec.area_sqm:
                        vals['area_sqm'] = rec.area_sqm
                    if not study.city and rec.city:
                        vals['city'] = rec.city.id
                    if not study.district_id and rec.district_id:
                        vals['district_id'] = rec.district_id.id
                    if not study.property_type and rec.property_type:
                        vals['property_type'] = rec.property_type.id
                    study.with_context(bypass_portfolio_assignment_check=True).write(vals)
        return res

    def _get_target_project_type(self):
        """Determine target project_type for this sale_auction record."""
        self.ensure_one()
        sales_type = self.env.ref('sales_and_auction_management.p2_type_sales', raise_if_not_found=False)
        enf_type = self.env.ref('sales_and_auction_management.p2_type_auction_enf', raise_if_not_found=False)
        pvt_type = self.env.ref('sales_and_auction_management.p2_type_auction_pvt', raise_if_not_found=False)
        city_type = self.env.ref('sales_and_auction_management.p2_type_auction_city', raise_if_not_found=False)

        if self.project_type_selection:
            return self.project_type_selection
        if sales_type and self.request_type_id == sales_type:
            return 'sales'
        if enf_type and self.request_type_id == enf_type:
            return 'auction_enf'
        if city_type and self.request_type_id == city_type:
            return 'city'
        if pvt_type and self.request_type_id == pvt_type:
            return 'auction_pvt'
        if self.entry_id:
            entry = self.entry_id
            city_req_types = [
                self.env.ref('bussma_system.city_study', raise_if_not_found=False),
                self.env.ref('bussma_system.direct_sale_city_study', raise_if_not_found=False),
            ]
            city_req_type_ids = [t.id for t in city_req_types if t]
            p_code = (entry.project_path_rel.code if hasattr(entry, 'project_path_rel') and entry.project_path_rel else False) or entry.project_path
            comm_dec = (entry.committee_decision_rel.code if hasattr(entry, 'committee_decision_rel') and entry.committee_decision_rel else False) or entry.committee_decision
            req_name = (entry.request_type_id.with_context(lang='en_US').name or entry.request_type_id.name or '').strip().lower() if entry.request_type_id else ''
            is_city = (
                p_code == 'cities' or
                (entry.request_type_id and (
                    entry.request_type_id.id in city_req_type_ids or
                    req_name in ['city study', 'cities', 'city studies']
                )) or
                (entry.stage_id and entry.stage_id.project_stage_selection in ['city_study_analyst', 'city_study_approval', 'city_study_completed'])
            )
            if is_city:
                return 'city'
            if comm_dec == 'auction':
                return 'auction_pvt'
            if comm_dec == 'direct_sale':
                return 'sales'
        return False

    def _sync_matching_bussma_project(self):
        """Sync project_id based on portfolio_id name AND matching project_type."""
        type_basic_map = {
            'sales': 'sales_and_auction_management.project_sales_basic',
            'auction_pvt': 'sales_and_auction_management.project_auctions_pvt_basic',
            'city': 'sales_and_auction_management.project_cities_basic',
            'auction_enf': 'sales_and_auction_management.project_auctions_enf_basic',
        }
        for rec in self:
            target_type = rec._get_target_project_type()
            basic_xml_id = type_basic_map.get(target_type)

            if rec.portfolio_id and rec.portfolio_id.name and target_type:
                port_name = rec.portfolio_id.name.strip()
                matched = self.env['bussma.project'].search([
                    ('name', '=', port_name),
                    ('project_type', '=', target_type),
                ], limit=1)
                if not matched:
                    matched = self.env['bussma.project'].search([
                        ('name', '=ilike', port_name),
                        ('project_type', '=', target_type),
                    ], limit=1)

                if matched:
                    if rec.project_id != matched:
                        rec.project_id = matched.id
                else:
                    if not rec.project_id or rec.project_id.is_basic or rec.project_id.project_type != target_type:
                        basic_proj = self.env.ref(basic_xml_id, raise_if_not_found=False) if basic_xml_id else False
                        if basic_proj and rec.project_id != basic_proj:
                            rec.project_id = basic_proj.id
            elif target_type and basic_xml_id:
                if not rec.project_id or rec.project_id.is_basic or rec.project_id.project_type != target_type:
                    basic_proj = self.env.ref(basic_xml_id, raise_if_not_found=False) if basic_xml_id else False
                    if basic_proj and rec.project_id != basic_proj:
                        rec.project_id = basic_proj.id

    def write(self, vals):
        if vals.get('has_portfolio') is False:
            vals['portfolio_id'] = False
        elif vals.get('portfolio_id') and 'has_portfolio' not in vals:
            vals['has_portfolio'] = True
        res = super().write(vals)
        if 'portfolio_id' in vals:
            for rec in self:
                studies = self.env['entries'].search([('sale_auction_id', '=', rec.id)])
                if studies:
                    studies.with_context(bypass_portfolio_assignment_check=True).write({
                        'has_portfolio': bool(rec.portfolio_id),
                        'portfolio_id': rec.portfolio_id.id if rec.portfolio_id else False,
                    })
                rec._sync_matching_bussma_project()
        return res

