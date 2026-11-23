from datetime import timedelta
from lxml import etree

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Helpdesk Ticket'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    active = fields.Boolean(default=True)
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    subject = fields.Char(string='Subject', required=True, tracking=True)
    description = fields.Text(string='Description')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, tracking=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1', tracking=True)

    color = fields.Integer(string='Color Index')

    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('solved', 'Solved'),
        ('closed', 'Closed')
    ], string='Status', default='new', tracking=True)

    date_open = fields.Datetime(string='Open Date', default=fields.Datetime.now, readonly=True)
    date_close = fields.Datetime(string='Close Date', readonly=True)

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields=allfields, attributes=attributes)
        if res and 'active' in res:
            res['active']['readonly'] = True
            res['active']['invisible'] = True
        return res

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('helpdesk.ticket') or 'New'
        ticket = super().create(vals)
        return ticket

    # --- Méthodes de transition d'états ---
    def action_set_in_progress(self):
        for record in self:
            if record.state not in ['new']:
                raise ValidationError("The ticket must be in the 'New' state to be set to in progress.")
            record.state = 'in_progress'

    def action_set_solved(self):
        for record in self:
            if record.state not in ['in_progress']:
                raise ValidationError("The ticket must be in the 'In Progress' state to be marked as solved.")
            record.state = 'solved'

    def action_set_closed(self):
        for record in self:
            record.state = 'closed'
            record.date_close = fields.Datetime.now()

    def action_reset_to_new(self):
        for record in self:
            if record.state != 'closed':
                raise ValidationError("The ticket must be in the 'Closed' state to revert to 'New'.")
            record.state = 'new'

    def print_ticket_pdf(self):
        return self.env.ref('helpdesk_ticket.action_report_ticket').report_action(self)
