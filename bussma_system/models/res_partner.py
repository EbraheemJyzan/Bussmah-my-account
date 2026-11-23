# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_customer = fields.Boolean(string='Is Customer')
    allowed_user_ids = fields.Many2many(
        'res.users', 
        string='Users Who Added This Customer',
        help='Users who have access to this partner due to being the original creator or part of a merge.'
    )
    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        for partner in partners:
            if not partner.allowed_user_ids and partner.create_uid:
                partner.allowed_user_ids = [(4, partner.create_uid.id)]
        return partners

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('skip_allowed_user_ids'):
            return res
            
        for partner in self:
            if partner.create_uid and partner.create_uid not in partner.allowed_user_ids:
                partner.with_context(skip_allowed_user_ids=True).write({
                    'allowed_user_ids': [(4, partner.create_uid.id)]
                })
        return res
