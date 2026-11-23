from odoo import models, fields, api, _

class OpportunityAssignEntriesWizard(models.TransientModel):
    _name = 'bussma.opportunity.assign.entries.wizard'
    _description = 'Assign Properties to Opportunity Wizard'

    opportunity_id = fields.Many2one('bussma.opportunity', string='Opportunity', required=True)
    partner_id = fields.Many2one('res.partner', string='Client', related='opportunity_id.partner_id', store=True)

    available_entry_ids = fields.Many2many(
        'entries',
        'wizard_entry_rel',
        'wizard_id',
        'entry_id',
        string='Available Properties for Assignment',
        compute='_compute_available_entries',
        store=False
    )
    selected_entry_ids = fields.Many2many(
        'entries',
        'wizard_selected_entry_rel',
        'wizard_id',
        'entry_id',
        string='Selected Properties for Assignment'
    )

    @api.depends('opportunity_id', 'partner_id')
    def _compute_available_entries(self):
        for rec in self:
            if rec.partner_id:
                # Find entries for this partner whose study is not completed ('completed') and not already assigned to this opportunity
                entries = self.env['entries'].search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('stage_id.project_stage_selection', '!=', 'completed'),
                    ('opportunity_id', '!=', rec.opportunity_id.id)
                ])
                rec.available_entry_ids = entries
            else:
                rec.available_entry_ids = False

    def action_confirm_assign(self):
        self.ensure_one()
        if self.selected_entry_ids:
            self.selected_entry_ids.write({'opportunity_id': self.opportunity_id.id})
            self.opportunity_id.sudo()._update_study_data_from_entries()
        return {'type': 'ir.actions.act_window_close'}
