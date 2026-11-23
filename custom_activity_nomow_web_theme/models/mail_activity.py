# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import AccessError


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def _action_done(self, feedback=False, attachment_ids=None):
        return super(MailActivity, self.with_context(mail_activity_marking_done=True))._action_done(
            feedback=feedback, attachment_ids=attachment_ids
        )

    def action_cancel(self):
        if not self.env.su:
            if not self.env.user.has_group('custom_activity_nomow_web_theme.group_record_deleter'):
                raise AccessError(_("You are not allowed to cancel activities from the chatter."))
        return super().action_cancel()

    def unlink(self):
        if (
            not self.env.su
            and not self.env.context.get('mail_activity_marking_done')
        ):
            if not self.env.user.has_group('custom_activity_nomow_web_theme.group_record_deleter'):
                raise AccessError(_("You are not allowed to delete activities from the chatter."))
        return super().unlink()
