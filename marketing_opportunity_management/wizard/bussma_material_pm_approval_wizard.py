from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class BussmaMaterialPmApprovalWizard(models.TransientModel):
    _name = 'bussma.material.pm.approval.wizard'
    _description = 'Project Manager Material Approval Wizard'

    material_id = fields.Many2one('bussma.marketing.material', string='Marketing Material', required=True, readonly=True)
    marketing_id = fields.Many2one(related='material_id.marketing_id', string='Marketing')
    bussma_project_id = fields.Many2one(related='material_id.bussma_project_id', readonly=True)
    is_opportunity_request = fields.Boolean(related='material_id.is_opportunity_request', readonly=True)
    is_office_request = fields.Boolean(related='material_id.is_office_request', readonly=True)
    name = fields.Char(related='material_id.name', string='Material Name', readonly=True)
    activity_id = fields.Many2one(related='material_id.activity_id', string='Marketing Activity', readonly=True)
    user_id = fields.Many2one(related='material_id.user_id', string='Responsible User', readonly=True)
    result_notes = fields.Text(related='material_id.result_notes', string='Notes / Results', readonly=True)
    material_stage_selection = fields.Selection(related='material_id.material_stage_selection', string='Stage Selection', readonly=True)
    pm_rejection_notes = fields.Text(string='Project Manager Return Notes')
    pm_rejection_attachment_ids = fields.Many2many(
        'ir.attachment',
        'bussma_material_pm_rej_wiz_att_rel',
        'wiz_id',
        'att_id',
        string='Return Attachments'
    )

    def action_approve(self):
        self.ensure_one()
        if self.material_id:
            self.material_id.with_context(bypass_marketing_check=True).action_pm_approve_material()
        return {'type': 'ir.actions.act_window_close'}

    def action_reject(self):
        self.ensure_one()
        if not self.pm_rejection_notes:
            raise UserError(_("Please enter return notes before rejecting."))
        if self.material_id:
            mat = self.material_id.with_context(bypass_marketing_check=True)
            mat.write({
                'pm_rejection_notes': self.pm_rejection_notes,
                'pm_rejection_attachment_ids': [(6, 0, self.pm_rejection_attachment_ids.ids)],
                'last_return_type': 'pm_rejection',
            })
            mat.action_pm_reject_material()

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
                'return_type': 'rejected',
                'marketion_requst_type': request_type,
                'user_id': self.env.user.id,
                'date': fields.Datetime.now(),
                'notes': self.pm_rejection_notes,
                'attachment_ids': [(6, 0, self.pm_rejection_attachment_ids.ids)],
            })
        return {'type': 'ir.actions.act_window_close'}
