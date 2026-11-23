from odoo import models, fields, api, _

class SalesAuctionRequestWizardInherit(models.TransientModel):
    _inherit = 'sales.auction.request.wizard'

    name = fields.Char(string='Project Name / Request Title')
    marketing_id = fields.Many2one('bussma.marketing', string='Marketing Request')
    attachments_ids = fields.Many2many('ir.attachment', string='Attachments')
    description = fields.Text(string='Requester Notes')

    @api.model
    def default_get(self, fields_list):
        res = super(SalesAuctionRequestWizardInherit, self).default_get(fields_list)
        project_id = res.get('project_id') or self.env.context.get('default_project_id')
        if not project_id and self.env.context.get('active_model') == 'bussma.project':
            project_id = self.env.context.get('active_id')

        if project_id:
            res['project_id'] = project_id
            proj = self.env['bussma.project'].browse(project_id)
            if proj:
                if not res.get('name') and proj.name:
                    res['name'] = proj.name

                props = proj.entry_ids
                if props:
                    res['property_ids'] = [(6, 0, props.ids)]

                if proj.marketing_id:
                    res['marketing_id'] = proj.marketing_id.id
                    if not res.get('description') and proj.marketing_id.notes:
                        res['description'] = proj.marketing_id.notes
        return res

    def action_confirm(self):
        self.ensure_one()
        if self.request_type == 'marketing':
            m_rec = False
            if self.project_id:
                m_rec = self.marketing_id or getattr(self.project_id, 'marketing_id', False)
                prop_ids = self.property_ids.ids if self.property_ids else (self.project_id.entry_ids.ids if self.project_id else [])
                if m_rec:
                    update_vals = {
                        'name': self.name or m_rec.name,
                        'notes': self.description,
                        'return_to_requester_notes': False,
                        'attachment_return_ids': [(5, 0, 0)],
                        'is_returned_to_requester': False,
                        'bussma_project_id': self.project_id.id,
                    }
                    if prop_ids:
                        update_vals['sales_auction_ids'] = [(6, 0, prop_ids)]
                    m_rec.sudo().with_context(bypass_marketing_check=True).write(update_vals)
                else:
                    create_vals = {
                        'name': self.name or self.project_id.name or _('New Marketing Request'),
                        'bussma_project_id': self.project_id.id,
                        'notes': self.description,
                        'project_status': 'new',
                        'requested_by_id': self.env.user.id,
                    }
                    if prop_ids:
                        create_vals['sales_auction_ids'] = [(6, 0, prop_ids)]
                    m_rec = self.env['bussma.marketing'].sudo().with_context(bypass_marketing_check=True).create(create_vals)

                self.project_id.sudo().write({
                    'marketing_id': m_rec.id,
                    'return_to_requester_notes': False,
                    'attachment_return_ids': [(5, 0, 0)],
                    'is_returned_to_requester': False,
                })

            if m_rec:
                if self.attachments_ids:
                    att_ids = []
                    for att in self.attachments_ids:
                        existing_att = self.env['ir.attachment'].sudo().search([
                            ('res_model', '=', 'bussma.marketing'),
                            ('res_id', '=', m_rec.id),
                            ('name', '=', att.name),
                            ('checksum', '=', att.checksum)
                        ], limit=1)
                        if not existing_att:
                            copied = att.sudo().copy({
                                'res_model': 'bussma.marketing',
                                'res_id': m_rec.id,
                            })
                            att_ids.append(copied.id)
                        else:
                            att_ids.append(existing_att.id)
                    if att_ids:
                        m_rec.sudo().with_context(bypass_marketing_check=True).write({
                            'attachments_request_ids': [(6, 0, att_ids)]
                        })

                draft_stage = self.env.ref('marketing_opportunity_management.stage_marketing_draft', raise_if_not_found=False)
                if draft_stage:
                    m_rec.sudo().with_context(bypass_marketing_check=True).write({'stage_id': draft_stage.id})

            return {'type': 'ir.actions.act_window_close'}
        else:
            return super(SalesAuctionRequestWizardInherit, self).action_confirm()
