# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression


STAGE_XML_ID_TO_FIELD = {
    # Stages without request type (3)
    'bussma_system.entry_screen': 'stage_count_entry_screen',
    'bussma_system.data_completion': 'stage_count_data_completion',
    'bussma_system.define_project_path_assign_analyst': 'stage_count_define_project_path',
    # Preliminary & Detailed study (14)
    'bussma_system.analyst': 'stage_count_analyst',
    'bussma_system.study_approval': 'stage_count_study_approval',
    'bussma_system.detailed_study_analyst': 'stage_count_detailed_study_analyst',
    'bussma_system.detailed_study_approval': 'stage_count_detailed_study_approval',
    'bussma_system.committee_decision': 'stage_count_committee_decision',
    'bussma_system.sale_manager_decision': 'stage_count_sales_manager_decision',
    'bussma_system.auctions_manager_decision': 'stage_count_auctions_manager_decision',
    'bussma_system.commercial_manager_approval': 'stage_count_commercial_manager_approval',
    'bussma_system.assign_negotiator': 'stage_count_assign_negotiator',
    'bussma_system.negotiator': 'stage_count_negotiator',
    'bussma_system.manager_contract_approval': 'stage_count_manager_contract_approval',
    'bussma_system.contract_followup': 'stage_count_contract_followup',
    'bussma_system.negotiation_approval': 'stage_count_negotiation_approval',
    'bussma_system.contract_completion': 'stage_count_contract_completion',
    'bussma_system.completed': 'stage_count_completed',
    # City study (3)
    'bussma_system.city_study_analyst': 'stage_count_city_study_analyst',
    'bussma_system.city_study_approval': 'stage_count_city_study_approval',
    'bussma_system.city_study_completed': 'stage_count_city_study_completed',
    # Detailed study - Eanfaz (4)
    'sales_and_auction_management.stage_studies_supervisor_eanfaz': 'stage_count_studies_supervisor_eanfaz',
    'sales_and_auction_management.stage_detailed_study_eanfaz': 'stage_count_detailed_study_eanfaz',
    'sales_and_auction_management.stage_detailed_study_approval_eanfaz': 'stage_count_detailed_study_approval_eanfaz',
    'sales_and_auction_management.stage_detailed_study_completed_eanfaz': 'stage_count_detailed_study_completed_eanfaz',
}


class StudyPortfolio(models.Model):
    _name = 'study.portfolio'
    _description = 'Study Portfolio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Portfolio Name',
        required=True,
        tracking=True
    )
    reference = fields.Char(
        string='Reference',
        readonly=True,
        copy=False,
        default=lambda self: _('New')
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    notes = fields.Html(
        string='Notes / Description'
    )

    entry_ids = fields.One2many(
        'entries',
        'portfolio_id',
        string='Properties'
    )
    entry_count = fields.Integer(
        string='Properties Count',
        compute='_compute_entry_count',
        store=True
    )
    total_area = fields.Float(
        string='Total Area (m²)',
        compute='_compute_totals',
        store=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    total_portfolio_value = fields.Monetary(
        string='Total Portfolio Value',
        currency_field='currency_id',
        compute='_compute_totals',
        store=True,
    )
    stage_ids = fields.Many2many(
        'request.stage',
        'study_portfolio_request_stage_rel',
        'portfolio_id',
        'stage_id',
        string='Portfolio Stages',
        compute='_compute_stage_ids',
        store=True,
        readonly=True,
        help='Stages of properties currently associated with this portfolio.',
    )
    can_manage_portfolio_assignment = fields.Boolean(
        string='Can Manage Portfolio Assignment',
        compute='_compute_can_manage_portfolio_assignment',
    )

    def _compute_can_manage_portfolio_assignment(self):
        can_manage = self.env['entries']._is_portfolio_assignment_manager()
        for rec in self:
            rec.can_manage_portfolio_assignment = can_manage

    # Stage-specific entry count fields
    stage_count_entry_screen = fields.Integer(
        string='Entry Screen Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_data_completion = fields.Integer(
        string='Data Completion Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_define_project_path = fields.Integer(
        string='Define Project Path Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_analyst = fields.Integer(
        string='Preliminary Study Analyst Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_study_approval = fields.Integer(
        string='Preliminary Study Approval Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_detailed_study_analyst = fields.Integer(
        string='Detailed Study Analyst Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_detailed_study_approval = fields.Integer(
        string='Detailed Study Approval Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_committee_decision = fields.Integer(
        string='Committee Decision Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_sales_manager_decision = fields.Integer(
        string='Sales Manager Decision Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_auctions_manager_decision = fields.Integer(
        string='Auctions Manager Decision Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_commercial_manager_approval = fields.Integer(
        string='Commercial Manager Approval Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_assign_negotiator = fields.Integer(
        string='Assign Negotiator Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_negotiator = fields.Integer(
        string='Negotiator Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_manager_contract_approval = fields.Integer(
        string='Contract Approval Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_contract_followup = fields.Integer(
        string='Contract Followup Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_negotiation_approval = fields.Integer(
        string='Negotiation Approval Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_contract_completion = fields.Integer(
        string='Contract Completion Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_completed = fields.Integer(
        string='Completed Detailed Study Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_city_study_analyst = fields.Integer(
        string='City Study - Analyst Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_city_study_approval = fields.Integer(
        string='City Study - Approval Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_city_study_completed = fields.Integer(
        string='City Study - Completed Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_studies_supervisor_eanfaz = fields.Integer(
        string='Studies Supervisor Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_detailed_study_eanfaz = fields.Integer(
        string='Detailed Study Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_detailed_study_approval_eanfaz = fields.Integer(
        string='Detailed Study Approval Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_count_detailed_study_completed_eanfaz = fields.Integer(
        string='Detailed Study Completed Properties Count',
        compute='_compute_stage_counts',
        store=True,
    )
    stage_counts_json = fields.Json(
        string='Stage Counts JSON',
        compute='_compute_stage_counts',
        store=True,
    )

    @api.model
    def _get_study_request_types(self):
        types = self.env['request.type']
        for xml_id in [
            'bussma_system.preliminary_study',
            'bussma_system.city_study',
            'sales_and_auction_management.detailed_study_eanfaz',
        ]:
            req_type = self.env.ref(xml_id, raise_if_not_found=False)
            if req_type:
                types |= req_type
        return types

    @api.depends('entry_ids.stage_id', 'entry_ids.stage_id.request_type_ids', 'entry_ids.request_type_id')
    def _compute_stage_ids(self):
        allowed_types = self._get_study_request_types()
        for rec in self:
            entries = rec.sudo().entry_ids
            if not entries:
                rec.stage_ids = False
                continue
            stages = entries.mapped('stage_id')
            if allowed_types:
                valid_stages = stages.filtered(
                    lambda s: bool(s.request_type_ids & allowed_types) or (
                        s in entries.filtered(lambda e: e.request_type_id in allowed_types).mapped('stage_id')
                    ) or not bool(s.request_type_ids)
                )
            else:
                valid_stages = stages
            rec.stage_ids = valid_stages

    @api.depends('entry_ids.stage_id')
    def _compute_stage_counts(self):
        stage_map = {}
        for xml_id, field_name in STAGE_XML_ID_TO_FIELD.items():
            st = self.env.ref(xml_id, raise_if_not_found=False)
            if st:
                stage_map[st.id] = field_name

        for rec in self:
            counts_by_field = {field_name: 0 for field_name in STAGE_XML_ID_TO_FIELD.values()}
            counts_by_id = {}
            entries = rec.sudo().entry_ids
            for entry in entries:
                sid = entry.stage_id.id if entry.stage_id else False
                if sid:
                    counts_by_id[str(sid)] = counts_by_id.get(str(sid), 0) + 1
                    fname = stage_map.get(sid)
                    if fname:
                        counts_by_field[fname] += 1
            for fname, val in counts_by_field.items():
                rec[fname] = val
            rec.stage_counts_json = counts_by_id

    @api.depends('entry_ids')
    def _compute_entry_count(self):
        for rec in self:
            rec.entry_count = len(rec.sudo().entry_ids)

    @api.depends(
        'entry_ids.area_sqm',
        'entry_ids.committee_decision',
        'entry_ids.committee_decision_rel',
        'entry_ids.customer_intent',
        'entry_ids.customer_intent_rel',
        'entry_ids.direct_sale_total_price',
        'entry_ids.auction_total_price'
    )
    def _compute_totals(self):
        for rec in self:
            entries = rec.sudo().entry_ids
            rec.total_area = sum(entries.mapped('area_sqm'))
            rec.total_portfolio_value = sum(entry._get_committee_price() for entry in entries)

    def read(self, fields=None, load='_classic_read'):
        """Ensure entry_ids only returns accessible properties for non-managers."""
        res = super().read(fields=fields, load=load)
        if not self.env.su and not self.env.context.get('bypass_portfolio_security'):
            user = self.env.user
            if (fields is None or 'entry_ids' in fields) and not self.env['entries']._is_study_manager(user):
                allowed_entries_domain = self.env['entries']._get_study_accessible_entries_domain(user)
                if allowed_entries_domain != [(1, '=', 1)]:
                    all_entry_ids = []
                    for val in res:
                        eids = val.get('entry_ids')
                        if eids:
                            all_entry_ids.extend(eids)
                    if all_entry_ids:
                        allowed_ids = set(self.env['entries'].with_context(
                            bypass_entries_personal_domain=True,
                            bypass_entry_visibility_check=True
                        ).search([('id', 'in', all_entry_ids)] + allowed_entries_domain).ids)
                    else:
                        allowed_ids = set()
                    for val in res:
                        if 'entry_ids' in val and val['entry_ids']:
                            val['entry_ids'] = [eid for eid in val['entry_ids'] if eid in allowed_ids]
        return res

    def web_read(self, specification: dict[str, dict]) -> list[dict]:
        """Ensure web_read only returns accessible properties in entry_ids for non-managers."""
        res = super().web_read(specification)
        if not self.env.su and not self.env.context.get('bypass_portfolio_security'):
            user = self.env.user
            if 'entry_ids' in specification and not self.env['entries']._is_study_manager(user):
                allowed_entries_domain = self.env['entries']._get_study_accessible_entries_domain(user)
                if allowed_entries_domain != [(1, '=', 1)]:
                    all_entry_ids = []
                    for val in res:
                        entry_vals = val.get('entry_ids')
                        if entry_vals:
                            if isinstance(entry_vals[0], dict):
                                all_entry_ids.extend([d['id'] for d in entry_vals if d.get('id')])
                            elif isinstance(entry_vals[0], int):
                                all_entry_ids.extend(entry_vals)
                    if all_entry_ids:
                        allowed_ids = set(self.env['entries'].with_context(
                            bypass_entries_personal_domain=True,
                            bypass_entry_visibility_check=True
                        ).search([('id', 'in', all_entry_ids)] + allowed_entries_domain).ids)
                    else:
                        allowed_ids = set()
                    for val in res:
                        entry_vals = val.get('entry_ids')
                        if entry_vals:
                            if isinstance(entry_vals[0], dict):
                                val['entry_ids'] = [d for d in entry_vals if d.get('id') in allowed_ids]
                            elif isinstance(entry_vals[0], int):
                                val['entry_ids'] = [eid for eid in entry_vals if eid in allowed_ids]
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('reference') or vals.get('reference') == _('New'):
                vals['reference'] = self.env['ir.sequence'].next_by_code('study.portfolio') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        if 'entry_ids' in vals and not self.env.su and not self.env.context.get('bypass_portfolio_assignment_check'):
            if not self.env['entries']._is_portfolio_assignment_manager():
                raise UserError(_("You do not have permission to assign or unassign properties to/from a study portfolio."))
        old_entries = {rec.id: set(rec.entry_ids.ids) for rec in self} if 'entry_ids' in vals else {}
        ctx = self.env.context
        if 'entry_ids' in vals and not ctx.get('bypass_portfolio_notify'):
            ctx = dict(ctx, bypass_portfolio_notify=True)

        res = super(StudyPortfolio, self.with_context(ctx)).write(vals)

        if 'entry_ids' in vals:
            self._compute_stage_ids()
            for rec in self:
                old_set = old_entries.get(rec.id, set())
                new_set = set(rec.entry_ids.ids)
                added_ids = new_set - old_set
                removed_ids = old_set - new_set

                if added_ids:
                    added_entries = self.env['entries'].browse(list(added_ids))
                    added_names = ", ".join(filter(None, added_entries.mapped(lambda e: e.entrie_name or f"Listing #{e.id}")))
                    rec.message_post(body=_("Property (%s) was added to portfolio properties.") % added_names)
                    for entry in added_entries:
                        entry.message_post(body=_("Property was added to study portfolio (%s).") % (rec.name or rec.reference))

                if removed_ids:
                    removed_entries = self.env['entries'].browse(list(removed_ids))
                    removed_names = ", ".join(filter(None, removed_entries.mapped(lambda e: e.entrie_name or f"Listing #{e.id}")))
                    rec.message_post(body=_("Property (%s) was removed from portfolio properties.") % removed_names)
                    for entry in removed_entries:
                        entry.message_post(body=_("Property was removed from study portfolio (%s).") % (rec.name or rec.reference))

        return res

    def action_open_assign_wizard(self):
        self.ensure_one()
        if not self.env['entries']._is_portfolio_assignment_manager():
            raise UserError(_("You do not have permission to assign properties to a study portfolio."))
        assign_list_view = self.env.ref(
            'study_portfolio_management.view_entries_assign_portfolio_list',
            raise_if_not_found=False,
        )
        search_view = self.env.ref(
            'bussma_system.view_entries_search',
            raise_if_not_found=False,
        )
        domain = [
            ('portfolio_id', '=', False),
            ('is_entry_archive', '=', False),
            ('is_deferred_opportunities_archive', '=', False),
            ('is_listing_archive_2023', '=', False),
            ('is_technical_offers_archive', '=', False),
            ('is_partners_screen', '=', False),
            ('is_from_smart_sheet', '=', False),
            ('project_stage_selection', 'not in', ['completed', 'city_study_completed', 'detailed_study_completed_eanfaz']),
        ]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Select Properties to Assign to Portfolio'),
            'res_model': 'entries',
            'view_mode': 'list',
            'views': [(assign_list_view.id if assign_list_view else False, 'list')],
            'search_view_id': [search_view.id if search_view else False, 'search'] if search_view else False,
            'domain': domain,
            'context': {
                'portfolio_to_assign': self.id,
            },
            'target': 'new',
        }

    def action_view_entries(self):
        self.ensure_one()
        user = self.env.user
        allowed_domain = self.env['entries']._get_study_accessible_entries_domain(user)
        if allowed_domain == [(1, '=', 1)]:
            entry_ids = self.sudo().entry_ids.ids
        else:
            entry_ids = self.env['entries'].with_context(
                bypass_entries_personal_domain=True,
                bypass_entry_visibility_check=True
            ).search([('portfolio_id', '=', self.id)] + allowed_domain).ids

        return {
            'name': _('Assigned Properties'),
            'type': 'ir.actions.act_window',
            'res_model': 'entries',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', entry_ids)],
            'context': {
                'default_portfolio_id': self.id,
                'hide_personal_create_uid': True,
            },
        }

    def action_view_stage_entries(self):
        """Open the properties associated with this portfolio, filtered by the stage

        corresponding to the kanban group column from which this action was triggered.
        """
        self.ensure_one()
        stage_id = False
        default_stage_ids = self.env.context.get('default_stage_ids')
        if default_stage_ids:
            if isinstance(default_stage_ids, (list, tuple)):
                stage_id = default_stage_ids[0] if default_stage_ids else False
            else:
                stage_id = default_stage_ids

        if not stage_id:
            stage_id = (
                self.env.context.get('group_stage_id') or
                self.env.context.get('stage_id') or
                self.env.context.get('active_stage_id')
            )
        if stage_id:
            try:
                stage_id = int(stage_id)
            except (ValueError, TypeError):
                stage_id = False

        user = self.env.user
        allowed_domain = self.env['entries']._get_study_accessible_entries_domain(user)
        base_domain = [('portfolio_id', '=', self.id)]
        if stage_id:
            base_domain.append(('stage_id', '=', stage_id))

        if allowed_domain == [(1, '=', 1)]:
            entries = self.sudo().entry_ids
            if stage_id:
                entries = entries.filtered(lambda e: e.stage_id.id == stage_id)
            entry_ids = entries.ids
        else:
            entry_ids = self.env['entries'].with_context(
                bypass_entries_personal_domain=True,
                bypass_entry_visibility_check=True
            ).search(base_domain + allowed_domain).ids

        action_name = _('Properties')
        if stage_id:
            stage = self.env['request.stage'].browse(stage_id)
            if stage.exists():
                action_name = _('%(portfolio)s - %(stage)s', portfolio=self.name, stage=stage.name)
        else:
            action_name = _('Properties - %(portfolio)s', portfolio=self.name)

        ctx = {
            'default_portfolio_id': self.id,
            'hide_personal_create_uid': True,
        }
        if stage_id:
            ctx['default_stage_id'] = stage_id
            ctx['search_default_stage_id'] = stage_id

        return {
            'name': action_name,
            'type': 'ir.actions.act_window',
            'res_model': 'entries',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', entry_ids)],
            'context': ctx,
        }
