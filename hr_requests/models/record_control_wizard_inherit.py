# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RecordControlWizard(models.TransientModel):
    _inherit = 'record.control.wizard'

    control_type = fields.Selection(
        selection_add=[
            ('hr_request', 'HR Request'),
        ],
        ondelete={
            'hr_request': 'set default',
        }
    )
    hr_request_id = fields.Many2one('hr.request', string='HR Request')

    @api.onchange('control_type')
    def _onchange_control_type(self):
        super()._onchange_control_type()
        self.hr_request_id = False
        if self.control_type == 'hr_request':
            self.is_delete = True

    def action_delete_record(self):
        self.ensure_one()
        if self.control_type == 'hr_request':
            if not self.hr_request_id:
                raise UserError(_("Please select an HR Request to delete."))
            return self._reset_stage_and_unlink(self.hr_request_id, 'hr.request')

        return super().action_delete_record()

    def action_confirm(self):
        self.ensure_one()
        if not self.is_delete:
            if self.control_type == 'hr_request' and self.hr_request_id:
                return {
                    'name': _('HR Request'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'hr.request',
                    'res_id': self.hr_request_id.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
        return super().action_confirm()
