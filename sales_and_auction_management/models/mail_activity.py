# -*- coding: utf-8 -*-
from odoo import models, api, _

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def unlink(self):
        # Silently delete activities without posting any log note to Chatter
        return super(MailActivity, self).unlink()

