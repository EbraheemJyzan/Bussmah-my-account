# -*- coding: utf-8 -*-
from odoo import fields, models


class HrClearanceProcedureStatus(models.Model):
    _name = 'hr.clearance.procedure.status'
    _description = 'Clearance Procedure Status'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)

