import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class EntryOpportunityWizard(models.TransientModel):
    _name = 'bussma.entry.opportunity.wizard'
    _description = 'Link / Create Opportunity Wizard'

    entry_id = fields.Many2one('entries', string='Listing (Property)', required=True)
    partner_id = fields.Many2one('res.partner', string='Client', required=True)
    stage_id = fields.Many2one(
        'request.stage',
        string='Stage',
        domain="[('res_model', '=', 'bussma.opportunity')]"
    )

    existing_opportunity_ids = fields.Many2many(
        'bussma.opportunity',
        string='Active Opportunities for Client',
        compute='_compute_existing_opportunities'
    )
    has_existing_opportunities = fields.Boolean(
        string='Has Active Opportunities',
        compute='_compute_existing_opportunities'
    )

    action_type = fields.Selection([
        ('link', 'Link to Existing Opportunity'),
        ('create', 'Create New Opportunity')
    ], string='Action Type', required=True, default='link')

    opportunity_id = fields.Many2one(
        'bussma.opportunity',
        string='Select Existing Opportunity',
        domain="[('partner_id', '=', partner_id), ('stage_id.state', '!=', 'done')]"
    )
    new_opportunity_name = fields.Char(string='New Opportunity Name')

    @api.depends('partner_id')
    def _compute_existing_opportunities(self):
        for rec in self:
            if rec.partner_id:
                opps = self.env['bussma.opportunity'].search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('stage_id.state', '!=', 'done')
                ])
                rec.existing_opportunity_ids = opps
                rec.has_existing_opportunities = bool(opps)
            else:
                rec.existing_opportunity_ids = False
                rec.has_existing_opportunities = False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if not self.has_existing_opportunities:
            self.action_type = 'create'
        else:
            self.action_type = 'link'

    def _send_opportunity_creation_notification(self, opp):
        template = self.env.ref('marketing_opportunity_management.email_template_opportunity_created_from_studies', raise_if_not_found=False)
        if not template:
            return
        emails = self.env['bussma.opportunity.department'].get_opportunity_member_emails()
        if not emails:
            _logger.warning("[Opportunity Email] No Opportunity Department members with emails found.")
            return
        email_to = ",".join(emails)
        sender_email = self.env.user.email or self.env.company.email
        if not sender_email:
            _logger.warning("[Opportunity Email] Cannot send creation email: No sender email configured on user or company.")
            return
        try:
            email_values = {
                'email_to': email_to,
                'email_from': sender_email,
                'model': False,
                'res_id': False,
            }
            template.send_mail(opp.id, force_send=True, email_values=email_values)
            _logger.info("[Opportunity Email] Sent creation email from studies to department members: %s", email_to)
        except Exception as e:
            _logger.error("Failed to send opportunity creation email from studies for %s: %s", opp.id, str(e))

    def action_apply(self):
        self.ensure_one()
        if self.action_type == 'link':
            if not self.opportunity_id:
                raise UserError(_('Please select an existing opportunity to link.'))
            self.entry_id.opportunity_id = self.opportunity_id.id
        else:
            name = self.new_opportunity_name or f"Opportunity - {self.partner_id.name} - {self.entry_id.entrie_name or ''}"
            opp_vals = {
                'name': name,
                'partner_id': self.partner_id.id,
                'source': 'system',
                'entry_ids': [(4, self.entry_id.id)],
            }
            if self.stage_id:
                opp_vals['stage_id'] = self.stage_id.id
            opp = self.env['bussma.opportunity'].with_context(bypass_opportunity_check=True).sudo().create(opp_vals)
            self.entry_id.opportunity_id = opp.id
            self._send_opportunity_creation_notification(opp)
        return {'type': 'ir.actions.act_window_close'}
