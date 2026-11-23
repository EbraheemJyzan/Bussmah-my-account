# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CommitteeEntriesWizard(models.TransientModel):
    _name = 'committee.entries.wizard'
    _description = 'Committee Actions Wizard'

    @api.model
    def default_get(self, fields_list):
        res = super(CommitteeEntriesWizard, self).default_get(fields_list)
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        if active_model == 'entries' and active_ids:
            entries_recs = self.env['entries'].browse(active_ids)
            res['entry_ids'] = [(6, 0, entries_recs.ids)]
            if entries_recs and entries_recs[0].currency_id:
                res['currency_id'] = entries_recs[0].currency_id.id
        return res

    entry_ids = fields.Many2many(
        'entries',
        'committee_entries_wizard_entries_rel',
        'wizard_id',
        'entry_id',
        string='Selected Entries'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    committee_approved_users = fields.Many2many(
        'res.users',
        'committee_entries_wizard_approved_users_rel',
        'wizard_id',
        'user_id',
        string='Approved'
    )
    committee_rejected_users = fields.Many2many(
        'res.users',
        'committee_entries_wizard_rejected_users_rel',
        'wizard_id',
        'user_id',
        string='Rejected'
    )
    committee_postponed_users = fields.Many2many(
        'res.users',
        'committee_entries_wizard_postponed_users_rel',
        'wizard_id',
        'user_id',
        string='Postponed'
    )
    marketing_duration_months = fields.Integer(string='Marketing Duration (Months)')
    committee_decision_date = fields.Date(string='Committee Decision Date')
    committee_decision = fields.Selection([
        ('direct_sale', 'Direct Sale'),
        ('auction', 'Auction'),
        ('exclusion', 'Exclusion'),
    ], string='Committee Decision')
    committee_decision_rel = fields.Many2one(
        'committee.decision.type',
        string='Committee Decision',
        domain="[('code', 'in', ['direct_sale', 'auction', 'exclusion'])]"
    )
    direct_sale_price_per_meter = fields.Float(string='Direct Sale Price per Square Meter')
    auction_price_per_meter = fields.Float(string='Auction Price per Square Meter')
    committe_notes = fields.Text(string='Notes')


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

    @api.onchange('committee_decision_rel')
    def _onchange_committee_decision_rel(self):
        code = self.committee_decision_rel.code if self.committee_decision_rel else False
        self.committee_decision = code if code in ['direct_sale', 'auction', 'exclusion'] else False
        if self.committee_decision_rel:
            self.committee_decision_date = fields.Date.today()

    @api.onchange('committee_decision')
    def _onchange_committee_decision(self):
        if self.committee_decision:
            self.committee_decision_rel = self.env['committee.decision.type'].search([('code', '=', self.committee_decision)], limit=1)
        else:
            self.committee_decision_rel = False

    def _validate_entries(self, entries):
        if not entries:
            raise UserError(_("No entries selected to apply the action."))

        invalid_entries = entries.filtered(lambda e: e.project_stage_selection != 'committee_decision')
        if invalid_entries:
            entry_lines = "\n".join(f"- {e.entrie_name or e.display_name} (Current Stage: {e.stage_id.name or 'Unknown'})" for e in invalid_entries)
            raise UserError(_(
                "The following properties/entries are not in the 'Committee Decision' stage:\n\n"
                "%s\n\n"
                "Please make sure all selected entries are in the 'Committee Decision' stage before applying this action."
            ) % entry_lines)

        archived_entries = entries.filtered(lambda e: e.is_entry_archive)
        if archived_entries:
            entry_lines = "\n".join(f"- {e.entrie_name or e.display_name}" for e in archived_entries)
            raise UserError(_(
                "The following properties/entries are archived and cannot be processed:\n\n"
                "%s"
            ) % entry_lines)

        if not self.committee_decision:
            raise UserError(_("Please select the Committee Decision before proceeding."))

        if self.committee_decision in ('direct_sale', 'auction'):
            if not self.committee_approved_users:
                raise UserError(_("Please select the approved committee members."))
            if not self.marketing_duration_months or self.marketing_duration_months <= 0:
                raise UserError(_("Please specify a valid marketing duration (months)."))
            if not self.committee_decision_date:
                raise UserError(_("Please select the committee decision date."))

            if self.committee_decision == 'direct_sale' and (not self.direct_sale_price_per_meter or self.direct_sale_price_per_meter <= 0):
                raise UserError(_("Please enter a valid Direct Sale price per square meter."))
            elif self.committee_decision == 'auction' and (not self.auction_price_per_meter or self.auction_price_per_meter <= 0):
                raise UserError(_("Please enter a valid Auction price per square meter."))

        elif self.committee_decision == 'exclusion':
            if not self.committee_rejected_users:
                raise UserError(_("Please select the rejecting committee members."))
            if not self.committe_notes:
                raise UserError(_("Please enter the committee notes explaining the reason for exclusion."))

    def action_apply(self):
        self.ensure_one()
        entries = self.entry_ids
        self._validate_entries(entries)

        decision_rel = self.committee_decision_rel or self.env['committee.decision.type'].search([('code', '=', self.committee_decision)], limit=1)

        base_vals = {
            'committee_decision': self.committee_decision,
            'committee_decision_rel': decision_rel.id if decision_rel else False,
            'committee_decision_date': self.committee_decision_date,
            'committee_approved_users': [(6, 0, self.committee_approved_users.ids)],
            'committee_rejected_users': [(6, 0, self.committee_rejected_users.ids)],
            'committee_postponed_users': [(6, 0, self.committee_postponed_users.ids)],
        }
        if self.committee_decision in ('direct_sale', 'auction'):
            base_vals['marketing_duration_months'] = self.marketing_duration_months
            if self.committee_decision == 'direct_sale':
                base_vals['direct_sale_price_per_meter'] = self.direct_sale_price_per_meter
            else:
                base_vals['auction_price_per_meter'] = self.auction_price_per_meter
        if self.committe_notes:
            base_vals['committe_notes'] = self.committe_notes

        for entry in entries:
            vals = dict(base_vals)
            if self.committee_decision == 'direct_sale':
                vals['direct_sale_total_price'] = (entry.area_sqm or 0.0) * self.direct_sale_price_per_meter
            elif self.committee_decision == 'auction':
                vals['auction_total_price'] = (entry.area_sqm or 0.0) * self.auction_price_per_meter

            entry.write(vals)
            entry.action_accept()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Committee decision successfully applied to %s entries.') % len(entries),
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
