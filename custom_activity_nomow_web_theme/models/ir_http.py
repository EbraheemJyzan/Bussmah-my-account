# -*- coding: utf-8 -*-
from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        res = super().session_info()
        res['is_record_editor'] = self.env.user.has_group('custom_activity_nomow_web_theme.group_record_editor')
        res['is_record_deleter'] = self.env.user.has_group('custom_activity_nomow_web_theme.group_record_deleter')
        return res

