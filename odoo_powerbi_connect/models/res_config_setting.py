# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_powerbi_fabric = fields.Boolean(
        "Powerbi Fabric", implied_group='odoo_powerbi_connect.group_powerbi_fabric')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        config = self.env['ir.config_parameter'].sudo()
        fabric = config.get_param('res.config.settings.group_powerbi_fabric')
        res.update(
            group_powerbi_fabric=fabric
        )
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'res.config.settings.group_powerbi_fabric', self.group_powerbi_fabric)

        action_tab = self.env.ref(
            'odoo_powerbi_connect.powerbi_table_action_tree')
        if action_tab:
            action_tab.context = {'fabric_group': self.group_powerbi_fabric}
            action_tab.domain = [('dataset_id', '=', False)] if self.group_powerbi_fabric else [
                ('database_id', '=', False)]

        action_dash = self.env.ref(
            'odoo_powerbi_connect.powerbi_connector_dashboard_action')
        if action_dash:
            states = ['dataset'] if self.group_powerbi_fabric else [
                'eventhouse', 'database']
            action_dash.domain = [('state', 'not in', states)]

        action_rep = self.env.ref(
            'odoo_powerbi_connect.powerbi_report_action_tree')
        if action_rep:
            action_rep.context = {'fabric_group': self.group_powerbi_fabric}

        return res
