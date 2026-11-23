# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Entries(models.Model):
    _inherit = 'entries'

    is_my_activity = fields.Boolean(
        string="Is My Activity",
        compute="_compute_is_my_activity"
    )

    @api.depends_context('uid')
    @api.depends('activity_ids', 'activity_ids.user_id')
    def _compute_is_my_activity(self):
        current_user = self.env.user
        for record in self:
            record.is_my_activity = any(act.user_id == current_user for act in record.activity_ids)
