# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            res_model = vals.get('res_model')
            res_id = vals.get('res_id')
            if res_model in ['entries', 'sales.auction.management'] and res_id:
                # Get the record to retrieve entrie_name
                record = self.env[res_model].sudo().browse(res_id)
                if record.exists() and hasattr(record, 'entrie_name') and record.entrie_name:
                    original_name = vals.get('name', '')
                    # Check if the reference is already part of the name to avoid redundancy
                    if original_name and record.entrie_name not in original_name:
                        vals['name'] = f"{record.entrie_name} - {original_name}"
        return super(IrAttachment, self).create(vals_list)
