# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class SalesAuctionRequestWizard(models.TransientModel):
    _name = 'sales.auction.request.wizard'
    _description = 'Request Wizard'

    entry_id = fields.Many2one('sales.auction.management', string='Property', required=False, ondelete='cascade')
    project_id = fields.Many2one('bussma.project', string='Project', ondelete='cascade')
    property_ids = fields.Many2many('sales.auction.management', string='Properties', domain="[('project_id', '=', project_id)]")
    request_type = fields.Selection([
        ('marketing', 'Marketing Department'),
        ('legal', 'Legal Department')
    ], string='Request Type', required=True, readonly=True)

    def action_confirm(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

