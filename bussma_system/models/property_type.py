# -*- coding: utf-8 -*-
from odoo import models, fields

class PropertyType(models.Model):
    _name = 'property.type'
    _description = 'Property Type'

    name = fields.Char(string='Name', required=True, translate=True)
    active = fields.Boolean(string='Active', default=True)
    is_land = fields.Boolean(string='Is Land', default=False)
