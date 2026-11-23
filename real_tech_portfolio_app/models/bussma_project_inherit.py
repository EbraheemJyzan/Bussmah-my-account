from odoo import models, fields, api, _

class BussmaProjectInherit(models.Model):
    _inherit = 'bussma.project'

    is_real_tech_portfolio_app = fields.Boolean(
        string='Real Tech Portfolio App',
        default=False,
        tracking=True
    )

    def action_toggle_real_tech_portfolio_app(self):
        for rec in self:
            rec.is_real_tech_portfolio_app = True
