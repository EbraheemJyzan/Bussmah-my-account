from odoo import models, fields, api, _

class MarketingReturnToOpportunityWizard(models.TransientModel):
    _name = 'marketing.return.to.opportunity.wizard'
    _description = 'Return Request to Requester Wizard'

    marketing_id = fields.Many2one('bussma.marketing', string='Marketing Record', required=True)
    return_to_requester_notes = fields.Text(string='Return to Requester Notes', required=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    @api.model
    def default_get(self, fields_list):
        res = super(MarketingReturnToOpportunityWizard, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and self.env.context.get('active_model') == 'bussma.marketing':
            res['marketing_id'] = active_id
        return res

    def action_confirm_return(self):
        self.ensure_one()
        marketing = self.marketing_id
        if marketing:
            marketing.write({
                'return_to_requester_notes': self.return_to_requester_notes,
            })

            # Move marketing stage back to draft
            draft_stage = self.env.ref('marketing_opportunity_management.stage_marketing_draft', raise_if_not_found=False)
            if draft_stage:
                marketing.write({'stage_id': draft_stage.id})

            if self.attachment_ids:
                for att in self.attachment_ids:
                    att.copy({
                        'res_model': 'bussma.marketing',
                        'res_id': marketing.id,
                    })

            body_marketing = _("Request returned to requester with the following notes:") 
            marketing.message_post(body=body_marketing)

            if marketing.opportunity_id:
                opp = marketing.opportunity_id
                opp.write({
                    'return_to_requester_notes': self.return_to_requester_notes,
                })
                # Move opportunity stage back to data completion
                opp_stage = self.env.ref('marketing_opportunity_management.stage_opportunity_data_completion', raise_if_not_found=False)
                if opp_stage:
                    opp.write({'stage_id': opp_stage.id})

                if self.attachment_ids:
                    for att in self.attachment_ids:
                        att.copy({
                            'res_model': 'bussma.opportunity',
                            'res_id': opp.id,
                        })

                body_opp = _("Marketing request returned from marketing department with the following notes:\n%s") % self.return_to_requester_notes
                opp.message_post(body=body_opp)

        return {'type': 'ir.actions.act_window_close'}
