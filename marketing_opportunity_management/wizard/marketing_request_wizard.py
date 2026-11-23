# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class BussmaMarketingRequestWizard(models.TransientModel):
    _name = 'bussma.marketing.request.wizard'
    _description = 'Create Marketing Request Wizard'

    opportunity_id = fields.Many2one('bussma.opportunity', string='Opportunity', required=True)
    opportunity_name = fields.Char(string='Opportunity Name', required=True)
    partner_id = fields.Many2one('res.partner', string='Client', required=True)
    property_name = fields.Char(string='Property Name')
    property_type_id = fields.Many2one('property.type', string='Property Type')
    city_id = fields.Many2one('res.country.state', string='City', domain="[('country_id.code', '=', 'SA'), ('code', 'ilike', 'CT_')]")
    district_id = fields.Many2one('res.city', string='District', domain="[('state_id', '=', city_id)]")
    area_sqm = fields.Float(string='Area (sqm)')
    sale_price = fields.Float(string='Sale Price')
    opportunity_type = fields.Selection([
        ('commercial_lease', 'Commercial Lease'),
        ('property_sale', 'Property Sale'),
        ('investment', 'Investment'),
        ('development', 'Development')
    ], string='Opportunity Type')
    source = fields.Selection([
        ('system', 'Studies System (Automatic)'),
        ('email', 'Email'),
        ('website', 'Website'),
        ('external_source', 'External Source'),
    ], string='Source', default='system')
    opportunity_source = fields.Selection([
        ('system', 'Studies System'),
        ('email', 'Email'),
        ('etimad', 'Etimad Platform'),
        ('forsa', 'Forsa Platform'),
        ('iskan', 'Housing Platform'),
        ('entifa', 'Entifa Platform'),
        ('sec', 'Saudi Electricity Company Platform'),
        ('external_source', 'Other'),
    ], string='Source')
    source_other = fields.Char(string='Other Source')
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Priority')
    client_requirements = fields.Text(string='Client Requirements')
    name = fields.Char(string='Marketing Request Title', required=True)
    marketing_id = fields.Many2one('bussma.marketing', string='Related Marketing Record')
    description = fields.Text(string='Request Description / Notes')
    attachments_ids = fields.Many2many('ir.attachment', string='Attachments')
    entry_ids = fields.Many2many('entries', string='Properties', domain="[('opportunity_id', '=', opportunity_id)]")

    @api.model
    def default_get(self, fields_list):
        res = super(BussmaMarketingRequestWizard, self).default_get(fields_list)
        opp_id = res.get('opportunity_id') or self.env.context.get('default_opportunity_id')
        if opp_id:
            opp = self.env['bussma.opportunity'].browse(opp_id)
            if opp.entry_ids:
                res['entry_ids'] = [(6, 0, opp.entry_ids.ids)]
            if not res.get('opportunity_type'):
                res['opportunity_type'] = opp.opportunity_type
            if not res.get('source'):
                res['source'] = opp.source
            if not res.get('opportunity_source'):
                res['opportunity_source'] = opp.opportunity_source
            if not res.get('source_other'):
                res['source_other'] = opp.source_other
            if not res.get('priority'):
                res['priority'] = opp.priority
            if not res.get('client_requirements'):
                res['client_requirements'] = opp.client_requirements
            if not res.get('property_name'):
                res['property_name'] = opp.property_name
            if not res.get('property_type_id') and opp.property_type_id:
                res['property_type_id'] = opp.property_type_id.id
            if not res.get('city_id') and opp.property_city_id:
                res['city_id'] = opp.property_city_id.id
            if not res.get('district_id') and opp.property_district_id:
                res['district_id'] = opp.property_district_id.id
            if not res.get('area_sqm'):
                res['area_sqm'] = opp.area_sqm
            if not res.get('sale_price'):
                res['sale_price'] = opp.approved_pricing
            if opp.marketing_id:
                res['marketing_id'] = opp.marketing_id.id
                if not res.get('description') and opp.marketing_id.notes:
                    res['description'] = opp.marketing_id.notes
        return res

    def action_create_marketing_request(self):
        self.ensure_one()
        if self.opportunity_id:
            self.opportunity_id._check_opportunity_edit_permission()
        opp_entry_ids = self.entry_ids.ids if self.entry_ids else (self.opportunity_id.entry_ids.ids if (self.opportunity_id and self.opportunity_id.entry_ids) else [])
        m_rec = self.env['bussma.marketing'].sudo().with_context(bypass_marketing_check=True).create({
            'name': self.name,
            'opportunity_id': self.opportunity_id.id,
            'entry_ids': [(6, 0, opp_entry_ids)],
            'partner_id': self.partner_id.id,
            'property_name': self.property_name,
            'property_type_id': self.property_type_id.id if self.property_type_id else False,
            'city_id': self.city_id.id if self.city_id else False,
            'district_id': self.district_id.id if self.district_id else False,
            'area_sqm': self.area_sqm,
            'sale_price': self.sale_price,
            'opportunity_type': self.opportunity_type,
            'source': self.source,
            'opportunity_source': self.opportunity_source,
            'source_other': self.source_other,
            'priority': self.priority,
            'client_requirements': self.client_requirements,
            'notes': self.description,
            'project_status': 'new',
            'is_opportunity_request': True,
            'requested_by_id': self.env.user.id,
        })
        if self.attachments_ids:
            att_ids = []
            for att in self.attachments_ids:
                copied = att.sudo().copy({
                    'res_model': 'bussma.marketing',
                    'res_id': m_rec.id,
                })
                att_ids.append(copied.id)
            if att_ids:
                m_rec.sudo().with_context(bypass_marketing_check=True).write({
                    'attachments_request_ids': [(6, 0, att_ids)]
                })

        if self.opportunity_id:
            opp_vals = {'marketing_id': m_rec.id}
            opp_mkt_stage = self.env.ref('marketing_opportunity_management.stage_opportunity_marketing_request', raise_if_not_found=False)
            if opp_mkt_stage:
                opp_vals['stage_id'] = opp_mkt_stage.id
            self.opportunity_id.sudo().write(opp_vals)
            if self.description:
                self.opportunity_id.message_post(body=_("Marketing Request Description: %s") % self.description)

        return {'type': 'ir.actions.act_window_close'}

    def action_update_marketing_request(self):
        self.ensure_one()
        if self.opportunity_id:
            self.opportunity_id._check_opportunity_edit_permission()
        m_rec = self.marketing_id or self.opportunity_id.marketing_id
        if not m_rec:
            return self.action_create_marketing_request()

        old_desc = (m_rec.notes or '').strip()
        new_desc = (self.description or '').strip()
        opp_entry_ids = self.entry_ids.ids if self.entry_ids else (self.opportunity_id.entry_ids.ids if (self.opportunity_id and self.opportunity_id.entry_ids) else [])
        m_rec.sudo().with_context(bypass_marketing_check=True).write({
            'name': self.name,
            'partner_id': self.partner_id.id,
            'entry_ids': [(6, 0, opp_entry_ids)],
            'property_name': self.property_name,
            'property_type_id': self.property_type_id.id if self.property_type_id else False,
            'city_id': self.city_id.id if self.city_id else False,
            'district_id': self.district_id.id if self.district_id else False,
            'area_sqm': self.area_sqm,
            'sale_price': self.sale_price,
            'opportunity_type': self.opportunity_type,
            'source': self.source,
            'opportunity_source': self.opportunity_source,
            'source_other': self.source_other,
            'priority': self.priority,
            'notes': self.description,
            'client_requirements': self.client_requirements,
            'return_to_requester_notes': False,
            'attachment_return_ids': [(5, 0, 0)],
            'is_returned_to_requester': False,
        })

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

        review_stage = self.env.ref('marketing_opportunity_management.stage_marketing_review', raise_if_not_found=False)
        if review_stage:
            m_rec.sudo().with_context(bypass_marketing_check=True).write({'stage_id': review_stage.id})

        opp_mkt_stage = self.env.ref('marketing_opportunity_management.stage_opportunity_marketing_request', raise_if_not_found=False)
        if self.opportunity_id:
            opp_vals = {'return_to_requester_notes': False, 'is_returned_to_requester': False}
            if opp_mkt_stage:
                opp_vals['stage_id'] = opp_mkt_stage.id
            self.opportunity_id.sudo().write(opp_vals)
            if new_desc != old_desc:
                body = _("Marketing Request Description: %s") % self.description if self.description else _("Marketing Request Description was cleared.")
            else:
                body = _("Marketing request updated and resent successfully.")
            self.opportunity_id.message_post(body=body)

        m_rec.message_post(body=_("Marketing request updated and resent after notes completion."))

        return {'type': 'ir.actions.act_window_close'}
