from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RecordControlWizard(models.TransientModel):
    _inherit = 'record.control.wizard'

    control_type = fields.Selection(
        selection_add=[
            ('financial_request', 'Financial Request'),
        ],
        ondelete={
            'financial_request': 'set default',
        }
    )
    financial_request_id = fields.Many2one('financial.request', string='Financial Request')

    @api.onchange('control_type')
    def _onchange_control_type(self):
        super()._onchange_control_type()
        self.financial_request_id = False
        if self.control_type == 'financial_request':
            self.is_delete = True

    def action_delete_record(self):
        self.ensure_one()
        if self.control_type == 'financial_request':
            if not self.financial_request_id:
                raise UserError(_("Please select a Financial Request to delete."))
            return self._reset_stage_and_unlink(self.financial_request_id, 'financial.request')

        return super().action_delete_record()

    def action_confirm(self):
        self.ensure_one()
        if not self.is_delete:
            if self.control_type == 'financial_request' and self.financial_request_id:
                return {
                    'name': _('Financial Request'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'financial.request',
                    'res_id': self.financial_request_id.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
        return super().action_confirm()
