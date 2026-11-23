# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class EntriesImportWizard(models.TransientModel):
    _inherit = 'entries.import.wizard'

    has_portfolio = fields.Boolean(
        string='Belongs to a Portfolio?',
        default=False,
    )
    portfolio_id = fields.Many2one(
        'study.portfolio',
        string='Study Portfolio',
    )

    @api.onchange('has_portfolio')
    def _onchange_has_portfolio(self):
        if not self.has_portfolio:
            self.portfolio_id = False

    @api.onchange('portfolio_id')
    def _onchange_portfolio_id(self):
        if self.portfolio_id:
            self.has_portfolio = True

    def _build_entry_vals(self, row_vals):
        vals = super()._build_entry_vals(row_vals)
        if self.has_portfolio and self.portfolio_id:
            vals['has_portfolio'] = True
            vals['portfolio_id'] = self.portfolio_id.id
        return vals


class EanfazEntriesImportWizard(models.TransientModel):
    _inherit = 'eanfaz.entries.import.wizard'

    has_portfolio = fields.Boolean(
        string='Belongs to a Portfolio?',
        default=False,
    )
    portfolio_id = fields.Many2one(
        'study.portfolio',
        string='Study Portfolio',
    )

    @api.onchange('has_portfolio')
    def _onchange_has_portfolio(self):
        if not self.has_portfolio:
            self.portfolio_id = False

    @api.onchange('portfolio_id')
    def _onchange_portfolio_id(self):
        if self.portfolio_id:
            self.has_portfolio = True

    def _build_eanfaz_vals(self, row_vals):
        vals = super()._build_eanfaz_vals(row_vals)
        if self.has_portfolio and self.portfolio_id:
            vals['has_portfolio'] = True
            vals['portfolio_id'] = self.portfolio_id.id
        return vals

