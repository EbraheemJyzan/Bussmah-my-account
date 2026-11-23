# -*- coding: utf-8 -*-

from odoo import api, models, fields


class HrRequestCategory(models.Model):
    _name = 'hr.request.category'
    _description = 'HR Request Category'
    _order = 'sequence, id'

    name = fields.Char(string='Request Category', required=True, translate=True)
    employee_classification = fields.Selection([
        ('employee', 'Employee Request'),
        ('manager', 'Manager Request'),
    ], string='Employee Classification', required=True, default='employee')
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
