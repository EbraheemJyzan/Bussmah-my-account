# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BussmahTemplate(models.Model):
    _name = 'bussma.template'
    _description = 'Bussmah Templates'
    _order = 'sequence, id'

    name = fields.Char(string='Template Name', required=True)
    form_view = fields.Many2one('ir.ui.view', string='Form View', domain="[('type', '=', 'form')]", required=True)
    model_name = fields.Char(string='Model Name', related='form_view.model', store=True, readonly=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    color = fields.Integer(string='Color Index', default=0)
    image_1920 = fields.Image(string="Image", max_width=1920, max_height=1920)
    image_128 = fields.Image(string="Image 128", related="image_1920", max_width=128, max_height=128, store=True)

    def action_open_form_view(self):
        self.ensure_one()
        if not self.form_view:
            return False
        
        target_model = self.form_view.model or self.model_name
        
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': target_model,
            'view_mode': 'form',
            'views': [(self.form_view.id, 'form')],
            'target': 'new',
            'context': dict(self.env.context),
        }
