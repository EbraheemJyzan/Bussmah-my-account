# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResCity(models.Model):
    _inherit = 'res.city'

    @api.model
    def default_get(self, fields_list):
        res = super(ResCity, self).default_get(fields_list)
        
        # Default Country to Saudi Arabia
        saudi_arabia = self.env.ref('base.sa', raise_if_not_found=False)
        if saudi_arabia and 'country_id' in fields_list:
            res.update({'country_id': saudi_arabia.id})
            
        return res
