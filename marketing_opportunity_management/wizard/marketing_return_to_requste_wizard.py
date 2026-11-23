from odoo import models, fields, api, _

class MarketingReturnToRequsteWizard(models.TransientModel):
    _name = 'marketing.return.to.requste.wizard'
    _description = 'Return Request to Requester Wizard'

    marketing_id = fields.Many2one('bussma.marketing', string='Marketing Record', required=True)
    return_to_requester_notes = fields.Text(string='Return to Requester Notes', required=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    @api.model
    def default_get(self, fields_list):
        res = super(MarketingReturnToRequsteWizard, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and self.env.context.get('active_model') == 'bussma.marketing':
            res['marketing_id'] = active_id
        return res

    def action_confirm_return(self):
        self.ensure_one()
        marketing = self.marketing_id
        if marketing:
            mkt_att_ids = []
            if self.attachment_ids:
                for att in self.attachment_ids:
                    copied = att.copy({
                        'res_model': 'bussma.marketing',
                        'res_id': marketing.id,
                    })
                    mkt_att_ids.append(copied.id)

            marketing.write({
                'return_to_requester_notes': self.return_to_requester_notes,
                'attachment_return_ids': [(6, 0, mkt_att_ids)],
                'is_returned_to_requester': True,
            })

            # Move marketing stage back to draft
            draft_stage = self.env.ref('marketing_opportunity_management.stage_marketing_draft', raise_if_not_found=False)
            if draft_stage:
                marketing.write({'stage_id': draft_stage.id})

            body_marketing = _("Request returned to requester with the following notes:\n%s") % self.return_to_requester_notes
            marketing.message_post(body=body_marketing)

            if marketing.opportunity_id:
                opp = marketing.opportunity_id
                opp_att_ids = []
                if self.attachment_ids:
                    for att in self.attachment_ids:
                        copied = att.copy({
                            'res_model': 'bussma.opportunity',
                            'res_id': opp.id,
                        })
                        opp_att_ids.append(copied.id)

                opp.write({
                    'return_to_requester_notes': self.return_to_requester_notes,
                    'attachment_return_ids': [(6, 0, opp_att_ids)],
                    'is_returned_to_requester': True,
                })
                # Create internal activity notification for opportunity managers
                opp._create_opportunity_activity(
                    summary='marketing_returned: %s' % (opp.code or ''),
                    note=_(
                        "تم إرجاع طلب التسويق رقم <b>%s</b> من إدارة التسويق إلى الفرصة <b>%s</b>."
                        " سبب الإرجاع: %s"
                    ) % (marketing.code or '', opp.code or '', self.return_to_requester_notes or '')
                )

                body_opp = _("Request returned to requester with the following notes:\n%s") % self.return_to_requester_notes
                opp.message_post(body=body_opp)

            if marketing.office_request_id:
                off_req = marketing.office_request_id
                off_att_ids = []
                if self.attachment_ids:
                    for att in self.attachment_ids:
                        copied = att.copy({
                            'res_model': 'office.request',
                            'res_id': off_req.id,
                        })
                        off_att_ids.append(copied.id)

                off_req.write({
                    'return_to_requester_notes': self.return_to_requester_notes,
                    'attachment_return_ids': [(6, 0, off_att_ids)],
                    'is_returned_to_requester': True,
                    'state': 'new',
                })

                body_off = _("Marketing request returned from marketing department with the following notes:\n%s") % self.return_to_requester_notes
                off_req.message_post(body=body_off)

            if marketing.bussma_project_id:
                proj = marketing.bussma_project_id
                proj_att_ids = []
                if self.attachment_ids:
                    for att in self.attachment_ids:
                        copied = att.copy({
                            'res_model': 'bussma.project',
                            'res_id': proj.id,
                        })
                        proj_att_ids.append(copied.id)
                proj.write({
                    'return_to_requester_notes': self.return_to_requester_notes,
                    'attachment_return_ids': [(6, 0, proj_att_ids)],
                    'is_returned_to_requester': True,
                })
                if hasattr(proj, 'message_post'):
                    body_proj = _("Marketing request returned from marketing department with the following notes:\n%s") % self.return_to_requester_notes
                    proj.message_post(body=body_proj)

        return {'type': 'ir.actions.act_window_close'}
