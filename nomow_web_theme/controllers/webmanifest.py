# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers import webmanifest
import base64

class WebManifest(webmanifest.WebManifest):
    def _get_webmanifest(self):

        company = request.env.company

        if company.logo:
            icon_src = f"data:image/png;base64,{company.logo.decode() if isinstance(company.logo, bytes) else company.logo}"
        else:
            icon_src = "/nomow_web_theme/static/src/img/nomowsoft.png"
        manifest = {
            'name': company.name,
            'scope': '/odoo',
            'start_url': '/odoo',
            'display': 'standalone',
            'background_color': "#234090",
            'theme_color': "#3bb8bc",
            'prefer_related_applications': False,
            'icons': [
                {
                    "src": icon_src,
                    "sizes": "512x512",
                    "type": "image/png"
                },
                {
                    "src": icon_src,
                    "sizes": "192x192",
                    "type": "image/png"
                }
            ],
            'shortcuts': self._get_shortcuts(),
        }

        return manifest
