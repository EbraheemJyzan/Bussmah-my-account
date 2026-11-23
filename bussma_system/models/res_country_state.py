# -*- coding: utf-8 -*-
from odoo import models, fields, api
import re

class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    @api.depends('name', 'code', 'country_id.code')
    def _compute_display_name(self):
        super()._compute_display_name()
        for state in self:
            if state.country_id.code == 'SA' and state.code and state.code.startswith('CT_'):
                state.display_name = state.name

    @api.model
    def default_get(self, fields_list):
        res = super(ResCountryState, self).default_get(fields_list)
        
        # Default Country to Saudi Arabia
        saudi_arabia = self.env.ref('base.sa', raise_if_not_found=False)
        if saudi_arabia and 'country_id' in fields_list:
            res.update({'country_id': saudi_arabia.id})
            
        # Sequential Code CT_XXX
        if 'code' in fields_list:
            # Search for existing codes matching CT_ pattern for Saudi Arabia
            domain = [('code', 'like', 'CT_')]
            if saudi_arabia:
                domain.append(('country_id', '=', saudi_arabia.id))
            
            states = self.search(domain)
            codes = states.mapped('code')
            
            max_num = 0
            for code in codes:
                match = re.search(r'CT_(\d+)', code)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
            
            res.update({'code': f'CT_{max_num + 1}'})
            
        return res
