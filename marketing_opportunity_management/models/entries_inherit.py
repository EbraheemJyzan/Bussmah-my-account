from collections import defaultdict
import logging
from odoo import models, fields, api, _
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class Entries(models.Model):
    _inherit = 'entries'

    opportunity_id = fields.Many2one(
        'bussma.opportunity',
        string='Opportunity',
        ondelete='set null',
        tracking=True
    )
    committee_total_price = fields.Float(
        string='Approved Total Price',
        compute='_compute_committee_total_price',
        store=True
    )
    effective_owner_price = fields.Float(
        string='Final Owner Price',
        compute='_compute_effective_owner_price',
        store=True
    )
    effective_price_per_meter = fields.Float(
        string='Price per Meter',
        compute='_compute_effective_price_per_meter',
        store=True
    )

    @api.depends('committee_decision', 'direct_sale_total_price', 'auction_total_price')
    def _compute_committee_total_price(self):
        for rec in self:
            if rec.committee_decision == 'auction':
                rec.committee_total_price = rec.auction_total_price or 0.0
            elif rec.committee_decision == 'direct_sale':
                rec.committee_total_price = rec.direct_sale_total_price or 0.0
            else:
                rec.committee_total_price = 0.0

    @api.depends('final_owner_price', 'manager_negotiator_final_owner_price')
    def _compute_effective_owner_price(self):
        for rec in self:
            if rec.manager_negotiator_final_owner_price:
                rec.effective_owner_price = rec.manager_negotiator_final_owner_price
            else:
                rec.effective_owner_price = rec.final_owner_price or 0.0

    @api.depends('committee_decision', 'direct_sale_price_per_meter', 'auction_price_per_meter')
    def _compute_effective_price_per_meter(self):
        for rec in self:
            if rec.committee_decision == 'direct_sale':
                rec.effective_price_per_meter = rec.direct_sale_price_per_meter or 0.0
            elif rec.committee_decision == 'auction':
                rec.effective_price_per_meter = rec.auction_price_per_meter or 0.0
            else:
                rec.effective_price_per_meter = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        records = super(Entries, self).create(vals_list)
        # Notify Opportunity Department members when technical offer is activated
        tech_offer_records = records.filtered(lambda r: r.requires_technical_offer == 'yes')
        if tech_offer_records:
            tech_offer_records._notify_opportunity_department_technical_offer()

        if not self.env.context.get('bypass_entry_notify'):
            opp_props = defaultdict(list)
            for rec in records:
                if rec.opportunity_id:
                    opp = rec.opportunity_id
                    if opp.marketing_id:
                        prop_name = rec.entrie_name or f"Listing #{rec.id}"
                        opp_props[opp].append(prop_name)

            for opp, prop_names in opp_props.items():
                opp.sudo()._update_study_data_from_entries()
                opp.marketing_id.sudo().with_context(bypass_marketing_check=True).write({
                    'entry_ids': [(6, 0, opp.entry_ids.ids)]
                })
                combined_names = ", ".join(filter(None, prop_names))
                opp.marketing_id.sudo()._send_property_changed_notification(action_type=_('Added'), property_name=combined_names, is_project=False)
        return records

    def write(self, vals):
        old_stages = {rec.id: rec.stage_id.project_stage_selection for rec in self}
        old_opps = {rec.id: rec.sudo().opportunity_id for rec in self}
        technical_offer_just_activated = self.env['entries']
        if vals.get('requires_technical_offer') == 'yes':
            technical_offer_just_activated = self.filtered(lambda r: r.requires_technical_offer != 'yes')

        res = super(Entries, self).write(vals)

        if technical_offer_just_activated:
            technical_offer_just_activated._notify_opportunity_department_technical_offer()

        # Handle opportunity_id changes and group notifications per opportunity
        if 'opportunity_id' in vals and not self.env.context.get('bypass_entry_notify'):
            new_opp_id = vals.get('opportunity_id')
            new_opp = self.env['bussma.opportunity'].browse(new_opp_id) if new_opp_id else False

            old_opp_props = defaultdict(list)
            new_opp_props = defaultdict(list)

            for rec in self:
                old_opp = old_opps.get(rec.id)
                prop_name = rec.entrie_name or f"Listing #{rec.id}"

                if old_opp and old_opp != new_opp:
                    old_opp_props[old_opp].append(prop_name)

                if new_opp and old_opp != new_opp:
                    new_opp_props[new_opp].append(prop_name)

            for old_opp, prop_names in old_opp_props.items():
                if old_opp:
                    old_opp.sudo()._update_study_data_from_entries()
                    combined_names = ", ".join(filter(None, prop_names))
                    old_opp.message_post(body=_("Property (%s) was removed from opportunity properties.") % combined_names)
                    if old_opp.marketing_id:
                        old_opp.marketing_id.sudo().with_context(bypass_marketing_check=True).write({
                            'entry_ids': [(6, 0, old_opp.entry_ids.ids)]
                        })
                        old_opp.marketing_id.sudo()._send_property_changed_notification(action_type=_('Removed'), property_name=combined_names, is_project=False)

            for new_opp, prop_names in new_opp_props.items():
                if new_opp:
                    new_opp.sudo()._update_study_data_from_entries()
                    combined_names = ", ".join(filter(None, prop_names))
                    new_opp.message_post(body=_("Property (%s) was added to opportunity properties.") % combined_names)
                    if new_opp.marketing_id:
                        new_opp.marketing_id.sudo().with_context(bypass_marketing_check=True).write({
                            'entry_ids': [(6, 0, new_opp.entry_ids.ids)]
                        })
                        new_opp.marketing_id.sudo()._send_property_changed_notification(action_type=_('Added'), property_name=combined_names, is_project=False)

        for rec in self:
            opp = rec.sudo().opportunity_id
            if opp:
                opp.sudo()._update_study_data_from_entries()
                entry_name = rec.entrie_name or f"Listing #{rec.id}"
                opp_just_assigned = 'opportunity_id' in vals and not old_opps.get(rec.id)
                current_stage = rec.stage_id.project_stage_selection
                if current_stage in ['city_study_completed', 'completed']:
                    stage_changed = old_stages.get(rec.id) != current_stage
                    if stage_changed or opp_just_assigned:
                        opp.sudo()._send_opportunity_mail_template(
                            'marketing_opportunity_management.email_template_opportunity_study_completed',
                            extra_context={
                                'entry_name': entry_name,
                                'action_user_name': self.env.user.name or ''
                            }
                        )
                
                # Auto-move opportunity to 'Contracted' if all entries are contracted
                if 'auction_contract_status' in vals or 'direct_sale_contract_status' in vals:
                    if opp.entry_ids:
                        all_contracted = all(
                            e.auction_contract_status == 'yes' or e.direct_sale_contract_status == 'yes' 
                            for e in opp.sudo().entry_ids
                        )
                        if all_contracted:
                            if opp.opportunity_stage_selection == 'opp_approve_close':
                                stage_contracted = self.env.ref('marketing_opportunity_management.stage_opportunity_contracted', raise_if_not_found=False)
                                if stage_contracted and opp.stage_id != stage_contracted:
                                    opp.sudo().stage_id = stage_contracted.id
                            elif opp.opportunity_stage_selection != 'opp_contracted':
                                opp.sudo()._send_opportunity_mail_template(
                                    'marketing_opportunity_management.email_template_opportunity_early_contracted'
                                )
        return res

    def unlink(self):
        opp_props = defaultdict(list)
        for rec in self:
            if rec.opportunity_id:
                opp = rec.opportunity_id
                if opp.marketing_id:
                    prop_name = rec.entrie_name or f"Listing #{rec.id}"
                    opp_props[opp].append(prop_name)

        res = super(Entries, self).unlink()

        for opp, prop_names in opp_props.items():
            if opp.exists():
                opp.sudo()._update_study_data_from_entries()
                if opp.marketing_id:
                    opp.marketing_id.sudo().with_context(bypass_marketing_check=True).write({
                        'entry_ids': [(6, 0, opp.entry_ids.ids)]
                    })
                    combined_names = ", ".join(filter(None, prop_names))
                    opp.marketing_id.sudo()._send_property_changed_notification(action_type=_('Removed'), property_name=combined_names, is_project=False)

        return res

    def _notify_opportunity_department_technical_offer(self):
        """Send email notification to Opportunity Department members when technical offer is required."""
        template = self.env.ref(
            'marketing_opportunity_management.email_template_entry_requires_technical_offer',
            raise_if_not_found=False
        )
        if not template:
            _logger.warning("Email template 'email_template_entry_requires_technical_offer' not found.")
            return

        member_emails = self.env['bussma.opportunity.department'].get_opportunity_member_emails()
        if not member_emails:
            _logger.warning("No Opportunity Department members found or they have no active email addresses.")
            return

        email_to = ",".join(member_emails)
        ctx = dict(self.env.context, action_user_name=self.env.user.name or '')

        for rec in self:
            try:
                template.sudo().with_context(ctx).send_mail(
                    rec.id,
                    force_send=True,
                    email_values={'email_to': email_to}
                )
            except Exception as e:
                _logger.error("Failed to send technical offer notification for entry %s: %s", rec.id, str(e))

    def action_unlink_from_opportunity(self):
        for rec in self:
            rec.opportunity_id = False
        return True

    def action_assign_to_opportunity(self):
        opportunity_id = self.env.context.get('opportunity_to_assign')
        if opportunity_id and self:
            self.write({'opportunity_id': opportunity_id})
            opp = self.env['bussma.opportunity'].browse(opportunity_id)
            if opp.exists():
                opp._update_study_data_from_entries()
        return {'type': 'ir.actions.act_window_close'}

    def action_view_opportunity(self):
        self.ensure_one()
        if not self.opportunity_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': _('Opportunity'),
            'res_model': 'bussma.opportunity',
            'res_id': self.opportunity_id.id,
            'view_mode': 'form',
            'target': 'current',
            }

    @api.model
    def web_search_read(self, domain=None, specification=None, offset=0, limit=None, order=None, count_limit=None):
        domain = domain or []
        user = self.env.user
        is_opp_manager = user.has_group('marketing_opportunity_management.group_opportunity_management')
        is_mkt_supervisor = user.has_group('marketing_opportunity_management.group_marketing_supervisor')
        is_general_manager = user.has_group('base.group_system') or \
                             user.has_group('bussma_system.group_commercial_sector_manager') or \
                             user.has_group('bussma_system.group_auctions_manager') or \
                             user.has_group('bussma_system.group_sales_manager') or \
                             user.has_group('bussma_system.group_studies_manager') or \
                             user.has_group('bussma_system.group_deputy_studies_manager') or \
                             user.has_group('bussma_system.group_committee_member') or \
                             user.has_group('bussma_system.group_city_studies_manager') or \
                             user.has_group('bussma_system.group_rnd_manager')

        if (is_opp_manager or is_mkt_supervisor) and not is_general_manager:
            is_study_menu = self.env.context.get('hide_personal_create_uid')
            if is_study_menu:
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
                base_domain = [
                    '|', '|', '|', '|', '|',
                    ('opportunity_id', '!=', False),
                    '&',
                    ('assigned_negotiator', '=', user.id),
                    ('project_stage_selection', '=', 'negotiator'),
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
            else:
                base_domain = [
                    '|', '|', '|', '|',
                    ('opportunity_id', '!=', False),
                    ('create_uid', '=', user.id),
                    '&',
                    ('assigned_negotiator', '=', user.id),
                    ('project_stage_selection', '=', 'negotiator'),
                    ('direct_sale_assigned_contract_manager', '=', user.id),
                    ('auction_assigned_contract_manager', '=', user.id)
                ]
            combined_domain = ['|', ('requires_technical_offer', '=', 'yes')] + base_domain
            domain = expression.AND([domain, combined_domain])
            return super(Entries, self.with_context(bypass_entries_personal_domain=True)).web_search_read(
                domain=domain,
                specification=specification,
                offset=offset,
                limit=limit,
                order=order,
                count_limit=count_limit
            )

        return super(Entries, self).web_search_read(
            domain=domain,
            specification=specification,
            offset=offset,
            limit=limit,
            order=order,
            count_limit=count_limit
        )

    def web_read(self, specification):
        user = self.env.user
        if user.has_group('marketing_opportunity_management.group_opportunity_management') or \
           user.has_group('marketing_opportunity_management.group_marketing_supervisor'):
            return super(Entries, self.sudo()).web_read(specification)
        return super(Entries, self).web_read(specification)
