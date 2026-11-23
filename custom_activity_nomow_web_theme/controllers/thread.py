# -*- coding: utf-8 -*-
from odoo.http import request
from odoo.addons.mail.controllers.thread import ThreadController


class CustomThreadController(ThreadController):

    def _is_message_editable(self, message, **kwargs):
        if message.model and message.model not in ('discuss.channel', 'mail.box'):
            if request.env.su:
                return True
            return request.env.user.has_group('custom_activity_nomow_web_theme.group_record_editor')
        return super()._is_message_editable(message, **kwargs)

