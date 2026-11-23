# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PowerbiTableColumn(models.Model):
    _name = "powerbi.table.column"
    _order = 'sequence, id'
    _description = "Power BI Table Columns"

    name = fields.Char(string="Name", related="field_id.name")
    sequence = fields.Integer(required=True, default=1)
    table_id = fields.Many2one(
        "powerbi.table",
        string="Table"
    )
    field_id = fields.Many2one(
        "ir.model.fields",
        string="Field"
    )
    field_type = fields.Selection(string="Type", related="field_id.ttype")
    label = fields.Char(string="Label")

    _sql_constraints = [
        (
            'table_column_label_unique',
            'unique (table_id,label)',
            'Table column label must be unique.',
        )
    ]

    @api.onchange('field_id')
    def onchange_field(self):
        label = self.field_id.field_description
        self.label = label and label.replace(' ', '_')

    @api.constrains("label")
    def validate_table_column_label(self):
        for column in self:
            if column.label:
                if not bool(re.fullmatch(r'[A-Za-z0-9_]*', column.label)):
                    raise UserError(
                        _("Column label can only contain alphabets, digits or underscore."))

    @api.model_create_multi
    def create(self, vals_list):
        res = super(PowerbiTableColumn, self).create(vals_list)
        if res:
            for vals in vals_list:
                if vals.get("table_id"):
                    table = self.env["powerbi.table"].browse(
                        vals.get("table_id"))
                    if table.is_published and table.dataset_type == 'push':
                        table.is_modified = True
        return res
