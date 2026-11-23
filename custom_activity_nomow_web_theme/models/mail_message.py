# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import AccessError



class MailMessage(models.Model):
    _inherit = 'mail.message'

    def unlink(self):
        if not self.env.su:
            if not self.env.user.has_group('custom_activity_nomow_web_theme.group_record_deleter'):
                raise AccessError(_("You are not allowed to delete messages from the chatter."))
        return super().unlink()

    def write(self, vals):
        if 'body' in vals and not self.env.su:
            for msg in self:
                if msg.model and msg.model not in ('discuss.channel', 'mail.box'):
                    if not self.env.user.has_group('custom_activity_nomow_web_theme.group_record_editor'):
                        raise AccessError(_("You are not allowed to edit messages on this record."))
        return super().write(vals)
