# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import fields, models


class UnpublishMessageWizard(models.TransientModel):
    _name = "unpublish.message.wizard"
    _description = "Unpublish Message Wizard"

    operation = fields.Selection(
        [('unlink', 'Unpublish only from Odoo end'),
         ('delete', 'Delete at the Power BI end')],
        string='Operation',
        default='unlink',
        required=True)
    reason = fields.Text(string="Reason to Unpublish", required=True)
    operation_object = fields.Selection(
        [('dataset', 'Dataset'), ('eventhouse', 'Eventhouse'),
         ('table', 'Table'), ('kql.database', 'KQL Database')],
        string='Object',
        required=True
    )

    def unpublish(self):
        return self.env[f'powerbi.{self.operation_object}'].browse(
            self._context.get('active_id')).unpublish_powerbi(self.operation, self.reason)
