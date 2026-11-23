# -*- coding: utf-8 -*-

from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_hr_clearance_user = fields.Boolean(string='HR Clearance Officer', prefetch=False)
    is_finance_clearance_user = fields.Boolean(string='Financial Clearance Officer', prefetch=False)
    is_it_clearance_user = fields.Boolean(string='IT Clearance Officer', prefetch=False)
    is_legal_clearance_user = fields.Boolean(string='Legal Clearance Officer', prefetch=False)
    is_commercial_manager_user = fields.Boolean(string='Commercial Sector Manager', prefetch=False)
    is_projects_manager_user = fields.Boolean(string='Projects Manager', prefetch=False)
    is_marketing_manager_user = fields.Boolean(string='Marketing Manager', prefetch=False)
    is_assets_manager_user = fields.Boolean(string='Assets & Investment Manager', prefetch=False)
    is_executive_manager_user = fields.Boolean(string='Executive Manager', prefetch=False)

