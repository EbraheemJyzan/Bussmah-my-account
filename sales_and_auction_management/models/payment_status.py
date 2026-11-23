# -*- coding: utf-8 -*-
from odoo import fields, models


class PaymentStatus(models.Model):
    _name = 'payment.status'
    _description = 'Payment Status'
    _order = 'id'

    name = fields.Char(string='Name', required=True, translate=True)
    active = fields.Boolean(default=True)
