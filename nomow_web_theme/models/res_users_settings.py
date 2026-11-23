# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.http import request, DEFAULT_LANG


class ResUsersSettings(models.Model):
    _inherit = 'res.users.settings'
    
    
   
    def _res_users_settings_format(self, fields_to_format=None):
        users_settings = super()._res_users_settings_format(fields_to_format)
        langs = [{
            'code': lang.code,
            'iso_code': lang.iso_code
        } for lang in self.env['res.lang'].with_context(active_test=True).search([])]
        users_settings['langs'] = langs
        return users_settings
