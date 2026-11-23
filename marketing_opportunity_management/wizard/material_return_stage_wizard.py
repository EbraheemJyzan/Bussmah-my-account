from odoo import models, fields, api, _

class MaterialReturnStageWizard(models.TransientModel):
    _name = 'material.return.stage.wizard'
    _description = 'Return Marketing Material to Previous Stage Wizard'

    material_id = fields.Many2one('bussma.marketing.material', string='Marketing Material', required=True)
    stage_id = fields.Many2one(
        'request.stage',
        string='Stage to Return To',
        domain="[('res_model', '=', 'bussma.marketing.material')]",
        required=True
    )
    supervisor_notes = fields.Text(string='Marketing Supervisor Notes')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    @api.model
    def default_get(self, fields_list):
        res = super(MaterialReturnStageWizard, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and self.env.context.get('active_model') == 'bussma.marketing.material':
            material = self.env['bussma.marketing.material'].browse(active_id)
            res['material_id'] = material.id
            if material.stage_id:
                prev_stage = self.env['request.stage'].search([
                    ('res_model', '=', 'bussma.marketing.material'),
                    ('sequence', '<', material.stage_id.sequence)
                ], order='sequence desc', limit=1)
                if prev_stage:
                    res['stage_id'] = prev_stage.id
        return res

    def action_confirm_return(self):
        self.ensure_one()
        if self.material_id:
            old_stage_name = self.material_id.stage_id.name or ''
            vals = {
                'stage_id': self.stage_id.id,
                'returned_stage_id': self.stage_id.id,
                'supervisor_notes': self.supervisor_notes,
                'supervisor_attachment_ids': [(6, 0, self.attachment_ids.ids)],
            }
            self.material_id.write(vals)
            body = _("Returned from stage %s with attached notes.") % old_stage_name
            self.material_id.message_post(body=body)
        return {'type': 'ir.actions.act_window_close'}
