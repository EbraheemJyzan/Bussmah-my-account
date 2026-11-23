from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RecordControlWizard(models.TransientModel):
    _inherit = 'record.control.wizard'

    control_type = fields.Selection(
        selection_add=[
            ('opportunity', 'Opportunity'),
            ('marketing', 'Marketing'),
            ('marketing_material', 'Marketing Material'),
            ('marketing_task', 'Marketing Task'),
        ],
        ondelete={
            'opportunity': 'set default',
            'marketing': 'set default',
            'marketing_material': 'set default',
            'marketing_task': 'set default',
        }
    )
    opportunity_id = fields.Many2one('bussma.opportunity', string='Opportunity')
    marketing_id = fields.Many2one('bussma.marketing', string='Marketing')
    marketing_material_id = fields.Many2one('bussma.marketing.material', string='Marketing Material')
    marketing_task_id = fields.Many2one('bussma.marketing.task', string='Marketing Task')

    @api.onchange('control_type')
    def _onchange_control_type(self):
        super()._onchange_control_type()
        self.opportunity_id = False
        self.marketing_id = False
        self.marketing_material_id = False
        self.marketing_task_id = False
        if self.control_type in ['opportunity', 'marketing', 'marketing_material', 'marketing_task']:
            self.is_delete = True

    def action_delete_record(self):
        self.ensure_one()
        if self.control_type == 'opportunity':
            if not self.opportunity_id:
                raise UserError(_("Please select an Opportunity to delete."))
            return self._reset_stage_and_unlink(self.opportunity_id, 'bussma.opportunity')

        elif self.control_type == 'marketing':
            if not self.marketing_id:
                raise UserError(_("Please select a Marketing record to delete."))
            return self._reset_stage_and_unlink(self.marketing_id, 'bussma.marketing')

        elif self.control_type == 'marketing_material':
            if not self.marketing_material_id:
                raise UserError(_("Please select a Marketing Material to delete."))
            return self._reset_stage_and_unlink(self.marketing_material_id, 'bussma.marketing.material')

        elif self.control_type == 'marketing_task':
            if not self.marketing_task_id:
                raise UserError(_("Please select a Marketing Task to delete."))
            target_name = self.marketing_task_id.display_name or str(self.marketing_task_id.id)
            self.marketing_task_id.sudo().unlink()
            return self._delete_notification(target_name)

        return super().action_delete_record()

    def action_confirm(self):
        self.ensure_one()
        if not self.is_delete:
            res_model = False
            res_id = False
            name = ''
            if self.control_type == 'opportunity' and self.opportunity_id:
                res_model = 'bussma.opportunity'
                res_id = self.opportunity_id.id
                name = _('Opportunity')
            elif self.control_type == 'marketing' and self.marketing_id:
                res_model = 'bussma.marketing'
                res_id = self.marketing_id.id
                name = _('Marketing')
            elif self.control_type == 'marketing_material' and self.marketing_material_id:
                res_model = 'bussma.marketing.material'
                res_id = self.marketing_material_id.id
                name = _('Marketing Material')
            elif self.control_type == 'marketing_task' and self.marketing_task_id:
                res_model = 'bussma.marketing.task'
                res_id = self.marketing_task_id.id
                name = _('Marketing Task')

            if res_model and res_id:
                return {
                    'name': name,
                    'type': 'ir.actions.act_window',
                    'res_model': res_model,
                    'res_id': res_id,
                    'view_mode': 'form',
                    'target': 'current',
                }
        return super().action_confirm()
