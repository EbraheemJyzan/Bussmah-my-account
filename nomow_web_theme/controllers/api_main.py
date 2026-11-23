# -*- coding: utf-8 -*-


from odoo import http, _, Command
from odoo.http import request
from odoo.addons.base.models.ir_qweb import keep_query


class ControllerBaseModel(http.Controller):

    @http.route('/api/flag_image_url', type='json', auth='public')
    def get_lang_active(self, **post):
        code = post.get('lang')
        lang = request.env['res.lang'].search([('code', '=', code)])
        if lang.flag_image:
            flag_image_url = f"/web/image/res.lang/{lang.id}/flag_image?height=25"
        else:
            flag_image_url = f"/base/static/img/country_flags/{code.lower().rsplit('_')[-1]}.png?height=25"
        return flag_image_url
           
       