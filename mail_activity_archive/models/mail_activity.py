from odoo import fields, models


class MailActivity(models.Model):
    _inherit = "mail.activity"

    active = fields.Boolean(default=True)
