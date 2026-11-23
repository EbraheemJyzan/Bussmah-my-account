# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SectorManagerEntriesWizard(models.TransientModel):
    _name = 'sector.manager.entries.wizard'
    _description = 'Commercial Sector Manager Actions Wizard'

    entry_ids = fields.Many2many(
        'entries',
        'sector_manager_entries_wizard_entries_rel',
        'wizard_id',
        'entry_id',
        string='Selected Entries (Fallback)'
    )
    line_ids = fields.One2many(
        'sector.manager.entries.wizard.line',
        'wizard_id',
        string='Selected Entries'
    )
    approval_process = fields.Selection([
        ('committee_decision', 'Commercial Sector Manager Approval for Committee Decision'),
        ('contract_approval', 'Commercial Sector Manager Approval for Client Contract'),
    ], string='Current Stage / Action Type', required=True, default='committee_decision')
    # Fields for Committee Decision Approval
    commercial_sector_manager_approval = fields.Selection([
        ('approval', 'Accept Listing and Move to Negotiation'),
        ('return_committee', 'Return Listing to Committee'),
        ('transfer', 'Transfer Listing to Partners Management'),
        ('declined', 'Decline Listing and Archive'),
        ('postponed', 'Move to Postponed Page'),
    ], string='Commercial Sector Manager Approval')
    commercial_sector_manager_notes = fields.Text(string='Commercial Sector Manager Notes')
    commercial_sector_manager_reason = fields.Text(string='Reason for Rejection or Transfer')
    # Fields for Contract Approval
    commercial_sector_manager_contract_approval = fields.Selection([
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('transfer', 'Transfer to Partners'),
    ], string='Commercial Sector Manager Contract Approval')
    commercial_sector_manager_contract_notes = fields.Text(string='Commercial Sector Manager Notes for Client Contract')
    # Computed helper fields for dynamic UI in wizard
    has_rejected_owner_entry = fields.Boolean(compute='_compute_owner_decision_summary')
    is_all_rejected_owner = fields.Boolean(compute='_compute_owner_decision_summary')

    @api.depends('line_ids.entry_id', 'entry_ids')
    def _compute_owner_decision_summary(self):
        for wiz in self:
            entries = wiz.line_ids.mapped('entry_id') or wiz.entry_ids
            if not entries:
                wiz.has_rejected_owner_entry = False
                wiz.is_all_rejected_owner = False
                continue
            owner_decisions = []
            for e in entries:
                dec = e.manager_negotiator_final_owner_decision if e.is_manager_negotiator else e.final_owner_decision
                owner_decisions.append(dec)
            wiz.has_rejected_owner_entry = any(d == 'rejected' for d in owner_decisions)
            wiz.is_all_rejected_owner = bool(owner_decisions) and all(d == 'rejected' for d in owner_decisions)

    @api.model
    def default_get(self, fields_list):
        res = super(SectorManagerEntriesWizard, self).default_get(fields_list)
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if active_model == 'entries' and active_ids:
            entries_recs = self.env['entries'].browse(active_ids)
            res['entry_ids'] = [(6, 0, entries_recs.ids)]
            lines = []
            for entry in entries_recs:
                lines.append((0, 0, {
                    'entry_id': entry.id,
                }))
            res['line_ids'] = lines

            if entries_recs:
                if all(e.project_stage_selection == 'manager_contract_approval' for e in entries_recs):
                    res['approval_process'] = 'contract_approval'
                elif all(e.project_stage_selection == 'commercial_manager_approval' for e in entries_recs):
                    res['approval_process'] = 'committee_decision'
        return res

    def action_apply(self):
        self.ensure_one()
        entries = self.line_ids.mapped('entry_id')
        if not entries and self.entry_ids:
            entries = self.entry_ids

        if not entries:
            raise UserError(_("No entries selected to apply the action."))

        # Stage validation against selected approval process (executed on button click)
        if self.approval_process == 'committee_decision':
            invalid_entries = entries.filtered(lambda e: e.project_stage_selection != 'commercial_manager_approval')
            if invalid_entries:
                entry_lines = "\n".join(f"- {e.entrie_name or e.display_name} (Current Stage: {e.stage_id.name or 'Unknown'})" for e in invalid_entries)
                raise UserError(_(
                    "The following properties/entries are not in the required stage (Commercial Sector Manager Approval):\n\n"
                    "%s\n\n"
                    "Please ensure that all selected entries are in the 'Commercial Sector Manager Approval' stage before applying this action."
                ) % entry_lines)

            if not self.commercial_sector_manager_approval:
                raise UserError(_("Please select a Commercial Sector Manager Approval option for Committee Decision."))

            if self.commercial_sector_manager_approval == 'return_committee' and not self.commercial_sector_manager_notes:
                raise UserError(_("Please enter Commercial Sector Manager notes for returning the listing to the committee."))

            if self.commercial_sector_manager_approval in ('declined', 'transfer') and not self.commercial_sector_manager_reason:
                raise UserError(_("Please enter the reason for rejection or transfer."))

            # Check for archived records
            archived_entries = entries.filtered(lambda e: e.is_entry_archive)
            if archived_entries:
                entry_lines = "\n".join(f"- {e.entrie_name or e.display_name}" for e in archived_entries)
                raise UserError(_(
                    "The following properties/entries are archived and cannot be processed:\n\n"
                    "%s"
                ) % entry_lines)

            for entry in entries:
                vals = {
                    'commercial_sector_manager_approval': self.commercial_sector_manager_approval,
                }
                if self.commercial_sector_manager_notes:
                    vals['commercial_sector_manager_notes'] = self.commercial_sector_manager_notes
                if self.commercial_sector_manager_reason:
                    vals['commercial_sector_manager_reason'] = self.commercial_sector_manager_reason

                entry.write(vals)
                entry.commercial_sector_manager_approval_path()

        elif self.approval_process == 'contract_approval':
            invalid_entries = entries.filtered(lambda e: e.project_stage_selection != 'manager_contract_approval')
            if invalid_entries:
                entry_lines = "\n".join(f"- {e.entrie_name or e.display_name} (Current Stage: {e.stage_id.name or 'Unknown'})" for e in invalid_entries)
                raise UserError(_(
                    "The following properties/entries are not in the required stage (Manager Contract Approval):\n\n"
                    "%s\n\n"
                    "Please ensure that all selected entries are in the 'Manager Contract Approval' stage before applying this action."
                ) % entry_lines)

            if not self.commercial_sector_manager_contract_approval:
                raise UserError(_("Please select a Commercial Sector Manager Contract Approval option."))

            if self.commercial_sector_manager_contract_approval == 'rejected' and not self.commercial_sector_manager_contract_notes:
                raise UserError(_("Please enter Commercial Sector Manager notes for rejecting the owner decision."))

            # Check for archived records
            archived_entries = entries.filtered(lambda e: e.is_entry_archive)
            if archived_entries:
                entry_lines = "\n".join(f"- {e.entrie_name or e.display_name}" for e in archived_entries)
                raise UserError(_(
                    "The following properties/entries are archived and cannot be processed:\n\n"
                    "%s"
                ) % entry_lines)

            for entry in entries:
                vals = {
                    'commercial_sector_manager_contract_approval': self.commercial_sector_manager_contract_approval,
                }
                if self.commercial_sector_manager_contract_notes:
                    vals['commercial_sector_manager_contract_notes'] = self.commercial_sector_manager_contract_notes

                entry.write(vals)

                if self.commercial_sector_manager_contract_approval == 'accepted':
                    owner_decision = (
                        entry.manager_negotiator_final_owner_decision
                        if entry.is_manager_negotiator
                        else entry.final_owner_decision
                    )
                    if owner_decision == 'rejected':
                        entry.move_to_entry_archive()
                    elif owner_decision in ['higher_price', 'committee_price']:
                        entry.action_accept()
                    else:
                        raise UserError(_(
                            "Entry '%s': You cannot proceed to the Contract Stage.\n"
                            "Approval from both the Sector Manager and the Owner is required first."
                        ) % (entry.entrie_name or entry.display_name))

                elif self.commercial_sector_manager_contract_approval == 'rejected':
                    entry.rejecte_owner_decision()

                elif self.commercial_sector_manager_contract_approval == 'transfer':
                    entry.commercial_sector_manager_approval_path()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Commercial Sector Manager actions successfully applied to %s entries.') % len(entries),
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }


class SectorManagerEntriesWizardLine(models.TransientModel):
    _name = 'sector.manager.entries.wizard.line'
    _description = 'Commercial Sector Manager Actions Wizard Line'

    wizard_id = fields.Many2one(
        'sector.manager.entries.wizard',
        string='Wizard',
        ondelete='cascade',
        required=True
    )
    entry_id = fields.Many2one(
        'entries',
        string='Entry',
        ondelete='cascade',
    )
    entrie_name = fields.Char(related='entry_id.entrie_name', string='Entry Reference', readonly=True)
    partner_id = fields.Many2one(related='entry_id.partner_id', string='Customer Name', readonly=True)
    customer_intent_rel = fields.Many2one(related='entry_id.customer_intent_rel', string='Customer Intent', readonly=True)
    property_type = fields.Many2one(related='entry_id.property_type', string='Property Type', readonly=True)
    entered_by_id = fields.Many2one(related='entry_id.entered_by_id', string='Entered By', readonly=True)
    stage_id = fields.Many2one(related='entry_id.stage_id', string='Current Stage', readonly=True)
    owner_decision_display = fields.Char(string='Owner Decision', compute='_compute_owner_decision_display')

    @api.depends('entry_id', 'entry_id.final_owner_decision', 'entry_id.manager_negotiator_final_owner_decision', 'entry_id.is_manager_negotiator')
    def _compute_owner_decision_display(self):
        decision_labels = {
            'committee_price': _('Approved at Committee Price'),
            'higher_price': _('Approved at Another Price'),
            'rejected': _('Rejected'),
        }
        for line in self:
            if not line.entry_id:
                line.owner_decision_display = ''
                continue
            e = line.entry_id
            code = e.manager_negotiator_final_owner_decision if e.is_manager_negotiator else e.final_owner_decision
            line.owner_decision_display = decision_labels.get(code, code or '')
