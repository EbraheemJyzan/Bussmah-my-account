# -*- coding: utf-8 -*-

from odoo import api, models, fields


class HrRequestType(models.Model):
    _name = 'hr.request.type'
    _description = 'HR Request Type'
    _order = 'sequence, id'

    name = fields.Char(string='Request Type', required=True, translate=True)
    code = fields.Char(string='Request Type Code')
    category_id = fields.Many2one(
        'hr.request.category',
        string='Request Category (Package)',
        required=True,
        ondelete='cascade'
    )
    employee_classification = fields.Selection(
        related='category_id.employee_classification',
        string='Employee Classification',
        store=True,
        readonly=True
    )
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields=allfields, attributes=attributes)
        if res and 'active' in res:
            res['active']['readonly'] = True
            res['active']['invisible'] = True
        return res
