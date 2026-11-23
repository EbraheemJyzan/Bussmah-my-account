from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BussmaMaterialRequestModificationWizard(models.TransientModel):
    _name = 'bussma.material.request.modification.wizard'
    _description = 'Request Marketing Material Modification Wizard'

    material_id = fields.Many2one('bussma.marketing.material', string='Marketing Material', required=True, readonly=True)
    notes = fields.Text(string='Modification Notes', required=True)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'bussma_mat_mod_req_wiz_att_rel',
        'wiz_id',
        'att_id',
        string='Attachments'
    )

    @api.model
    def default_get(self, fields_list):
        res = super(BussmaMaterialRequestModificationWizard, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and self.env.context.get('active_model') == 'bussma.marketing.material':
            res['material_id'] = active_id
        return res

    def action_confirm(self):
        self.ensure_one()
        if not self.notes or not self.notes.strip():
            raise UserError(_("Please enter modification description notes."))

        if self.material_id:
            stage = self.env.ref('marketing_opportunity_management.stage_mat_marketing_approve', raise_if_not_found=False)
            vals = {
                'modification_request_notes': self.notes,
                'modification_attachment_ids': [(6, 0, self.attachment_ids.ids)],
                'last_return_type': 'modification',
            }
            if stage:
                vals['stage_id'] = stage.id
                vals['returned_stage_id'] = stage.id

            self.material_id.write(vals)

            if self.material_id.marketing_id:
                mkt_stage = self.env.ref('marketing_opportunity_management.stage_marketing_supervisor_approval', raise_if_not_found=False)
                if mkt_stage:
                    self.material_id.marketing_id.write({'stage_id': mkt_stage.id})

            request_type = 'project_request'
            if self.material_id.marketing_id:
                mkt = self.material_id.marketing_id
                if mkt.is_opportunity_request or mkt.opportunity_id:
                    request_type = 'opportunity_request'
                elif mkt.bussma_project_id:
                    request_type = 'project_request'
                elif mkt.is_office_request or mkt.office_request_id:
                    request_type = 'office_request'

            self.env['bussma.material.return.note'].create({
                'material_id': self.material_id.id,
                'return_type': 'modification',
                'marketion_requst_type': request_type,
                'user_id': self.env.user.id,
                'date': fields.Datetime.now(),
                'notes': self.notes,
                'attachment_ids': [(6, 0, self.attachment_ids.ids)],
            })
        return {'type': 'ir.actions.act_window_close'}
