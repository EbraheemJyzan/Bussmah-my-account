from odoo import models, fields, api, _

class BussmaProjectInherit(models.Model):
    _inherit = 'bussma.project'

    marketing_id = fields.Many2one('bussma.marketing', string='Related Marketing Record', tracking=True)
    return_to_requester_notes = fields.Text(string='Return Notes from Marketing', tracking=True)
    attachment_return_ids = fields.Many2many('ir.attachment', 'bussma_project_mkt_return_att_rel', 'project_id', 'att_id', string='Return Attachments')
    is_returned_to_requester = fields.Boolean(string='Returned from Marketing', default=False)
    material_ids = fields.Many2many(related='marketing_id.material_ids', string='Marketing Materials Results', readonly=True)
    marketing_stage_selection = fields.Selection(related='marketing_id.marketing_stage_selection', string='Marketing Stage', readonly=True)
    has_pm_or_done_materials = fields.Boolean(
        string='Has PM or Done Materials',
        compute='_compute_has_pm_or_done_materials'
    )

    @api.depends('marketing_id', 'marketing_id.material_ids', 'marketing_id.material_ids.material_stage_selection')
    def _compute_has_pm_or_done_materials(self):
        for rec in self:
            if rec.marketing_id and rec.marketing_id.material_ids:
                rec.has_pm_or_done_materials = any(
                    m.material_stage_selection in ('mat_pm_approve', 'mat_done')
                    for m in rec.marketing_id.material_ids
                )
            else:
                rec.has_pm_or_done_materials = False

    def action_raise_marketing_request_wizard(self):
        self.ensure_one()
        attachments = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'bussma.project'),
            ('res_id', '=', self.id)
        ])
        return {
            'name': _('Resend Marketing Request') if (self.marketing_id and self.is_returned_to_requester) else _('Create Marketing Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'sales.auction.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_project_id': self.id,
                'default_request_type': 'marketing',
                'default_name': self.name or '',
                'default_marketing_id': self.marketing_id.id if self.marketing_id else False,
                'default_description': self.marketing_id.notes if (self.marketing_id and self.marketing_id.notes) else '',
                'default_attachments_ids': [(6, 0, attachments.ids)],
            }
        }

