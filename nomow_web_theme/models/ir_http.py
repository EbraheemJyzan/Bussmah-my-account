# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.http import request

class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        session_info = super().session_info()
        user = self.env.user
        company = self.env.company
        if request.env and request.env.user._is_internal():
            for company in request.env.user.company_ids.with_context(bin_size=True):
                session_info['user_companies']['allowed_companies'][company.id].update({
                    'has_background_image': bool(company.background_image),
                })
        return {
            **session_info,
            'apps_menu': {
                'search_type': user.apps_menu_search_type,
                'theme': user.apps_menu_theme,
            },
        }
       