# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class OfficeRequestMarketingWizard(models.TransientModel):
    _name = 'office.request.marketing.wizard'
    _description = 'Create / Edit Office Marketing Request Wizard'

    office_request_id = fields.Many2one('office.request', string='Office Request', required=True)
    name = fields.Char(string='Project Name / Request Title', required=True)

    city_id = fields.Many2one('res.country.state', string='City', domain="[('country_id.code', '=', 'SA'), ('code', 'ilike', 'CT_')]")
    district_id = fields.Many2one('res.city', string='District', domain="[('state_id', '=', city_id)]")
    property_type_id = fields.Many2one('property.type', string='Property Type')
    area_sqm = fields.Float(string='Area (sqm)')
    sale_price = fields.Float(string='Sale Price')
    description = fields.Text(string='Request Description', required=True)
    department_id = fields.Many2one('office.department', string='Department')
    requested_by_id = fields.Many2one('res.users', string='Requested By')
    attachments_ids = fields.Many2many('ir.attachment', string='Attachments')
    marketing_id = fields.Many2one('bussma.marketing', string='Related Marketing Record')
    office_request_type = fields.Selection([
        ('id_card', 'ID Card'),
        ('business_card', 'Business Card'),
        ('email_signature', 'Email Signature'),
        ('signboard_design', 'Signboard Design'),
        ('design_request', 'Design Request'),
        ('internal_communication', 'Internal Communication'),
        ('project_request', 'Project'),
        ('change_request', 'Change Request'),
        ('thank_you_certificate', 'Thank You Certificate'),
        ('other', 'Other'),
    ], string='Office Request Type')
    employee_name = fields.Char(string='Employee Name')
    job_title = fields.Char(string='Job Title')
    employee_number = fields.Char(string='Employee Number')
    employee_email = fields.Char(string='Employee Email')
    phone_number = fields.Char(string='Phone Number')
    extension_number = fields.Char(string='Extension Number')
    region_id = fields.Many2one('res.country.state', string='Region')
    property_code = fields.Char(string='Property Code')
    signboard_size = fields.Char(string='Signboard Size')
    needs_identity = fields.Boolean(string='Needs Identity?')
    needs_content_writing = fields.Boolean(string='Needs Content Writing?')
    # Project Request Fields
    project_name = fields.Char(string='Project Name')
    project_type_selection = fields.Selection([
        ('sales', 'Direct Sale'),
        ('auction_pvt', 'Private Auction'),
        ('auction_enf', 'Enforcement Auction'),
        ('city', 'Cities'),
        ('other', 'Other'),
    ], string='Project Type')
    has_proposed_project_name = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Has Proposed Project Name?')
    proposed_project_name = fields.Char(string='Proposed Project Name')
    is_masterplan = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Is Project a Masterplan/Scheme?')
    # Change Request Fields
    change_request_type = fields.Selection([
        ('add_property', 'Add Property'),
        ('remove_property', 'Remove Property'),
        ('other', 'Other'),
    ], string='Change Request Type')
    target_marketing_project_id = fields.Many2one('bussma.marketing', string='Target Marketing Project to Edit')
    # Shared New Fields
    delivery_date = fields.Date(string='Delivery Date')
    has_attachments = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Has Attachments?')

    @api.model
    def default_get(self, fields_list):
        res = super(OfficeRequestMarketingWizard, self).default_get(fields_list)
        req_id = res.get('office_request_id') or self.env.context.get('default_office_request_id')
        if req_id:
            req = self.env['office.request'].browse(req_id)
            if not res.get('department_id') and req.department_id:
                res['department_id'] = req.department_id.id
            if not res.get('requested_by_id') and req.requested_by_id:
                res['requested_by_id'] = req.requested_by_id.id
            res.update({
                'office_request_type': req.office_request_type,
                'employee_name': req.employee_name,
                'job_title': req.job_title,
                'employee_number': req.employee_number,
                'employee_email': req.employee_email,
                'phone_number': req.phone_number,
                'extension_number': req.extension_number,
                'region_id': req.region_id.id if req.region_id else False,
                'property_code': req.property_code,
                'signboard_size': req.signboard_size,
                'needs_identity': req.needs_identity,
                'needs_content_writing': req.needs_content_writing,
                'project_name': req.project_name,
                'project_type_selection': req.project_type_selection,
                'has_proposed_project_name': req.has_proposed_project_name,
                'proposed_project_name': req.proposed_project_name,
                'is_masterplan': req.is_masterplan,
                'change_request_type': req.change_request_type,
                'target_marketing_project_id': req.target_marketing_project_id.id if req.target_marketing_project_id else False,
                'delivery_date': req.delivery_date,
                'has_attachments': req.has_attachments,
            })
            if req.marketing_id:
                res['marketing_id'] = req.marketing_id.id
                if not res.get('description') and req.marketing_id.notes:
                    res['description'] = req.marketing_id.notes
        return res

    def action_create_or_update_marketing_request(self):
        self.ensure_one()
        req = self.office_request_id
        m_rec = self.marketing_id or req.marketing_id

        if m_rec:
            # Update Marketing Request and resend
            m_rec.sudo().with_context(bypass_marketing_check=True).write({
                'name': self.name,
                'city_id': self.city_id.id if self.city_id else False,
                'district_id': self.district_id.id if self.district_id else False,
                'property_type_id': self.property_type_id.id if self.property_type_id else False,
                'area_sqm': self.area_sqm,
                'sale_price': self.sale_price,
                'office_department_id': self.department_id.id if self.department_id else False,
                'requested_by_id': self.requested_by_id.id if self.requested_by_id else False,
                'office_request_type': self.office_request_type,
                'employee_name': self.employee_name,
                'job_title': self.job_title,
                'employee_number': self.employee_number,
                'employee_email': self.employee_email,
                'phone_number': self.phone_number,
                'extension_number': self.extension_number,
                'region_id': self.region_id.id if self.region_id else False,
                'property_code': self.property_code,
                'signboard_size': self.signboard_size,
                'needs_identity': self.needs_identity,
                'needs_content_writing': self.needs_content_writing,
                'request_description': self.description,
                'project_name': self.project_name,
                'project_type_selection': self.project_type_selection,
                'has_proposed_project_name': self.has_proposed_project_name,
                'proposed_project_name': self.proposed_project_name,
                'is_masterplan': self.is_masterplan,
                'change_request_type': self.change_request_type,
                'target_marketing_project_id': self.target_marketing_project_id.id if self.target_marketing_project_id else False,
                'delivery_date': self.delivery_date,
                'has_attachments': self.has_attachments,
                'is_office_request': True,
                'notes': self.description,
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

            if req:
                req.write({
                    'state': 'in_progress',
                    'return_to_requester_notes': False,
                    'attachment_return_ids': [(5, 0, 0)],
                    'is_returned_to_requester': False,
                })
                req.message_post(body=_("Marketing request updated and resent successfully."))

            m_rec.message_post(body=_("Marketing request updated and resent after notes completion."))
        else:
            # Create Marketing Request
            m_rec = self.env['bussma.marketing'].sudo().with_context(bypass_marketing_check=True).create({
                'name': self.name,
                'city_id': self.city_id.id if self.city_id else False,
                'district_id': self.district_id.id if self.district_id else False,
                'property_type_id': self.property_type_id.id if self.property_type_id else False,
                'area_sqm': self.area_sqm,
                'sale_price': self.sale_price,
                'partner_id': req.partner_id.id if req.partner_id else False,
                'office_request_id': req.id,
                'office_department_id': self.department_id.id if self.department_id else False,
                'requested_by_id': self.requested_by_id.id if self.requested_by_id else False,
                'office_request_type': self.office_request_type,
                'employee_name': self.employee_name,
                'job_title': self.job_title,
                'employee_number': self.employee_number,
                'employee_email': self.employee_email,
                'phone_number': self.phone_number,
                'extension_number': self.extension_number,
                'region_id': self.region_id.id if self.region_id else False,
                'property_code': self.property_code,
                'signboard_size': self.signboard_size,
                'needs_identity': self.needs_identity,
                'needs_content_writing': self.needs_content_writing,
                'request_description': self.description,
                'project_name': self.project_name,
                'project_type_selection': self.project_type_selection,
                'has_proposed_project_name': self.has_proposed_project_name,
                'proposed_project_name': self.proposed_project_name,
                'is_masterplan': self.is_masterplan,
                'change_request_type': self.change_request_type,
                'target_marketing_project_id': self.target_marketing_project_id.id if self.target_marketing_project_id else False,
                'delivery_date': self.delivery_date,
                'has_attachments': self.has_attachments,
                'notes': self.description,
                'project_status': 'new',
                'is_office_request': True,
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

            if req:
                req.write({
                    'marketing_id': m_rec.id,
                    'state': 'in_progress',
                })
                req.message_post(body=_("Marketing request created successfully and moved to in progress."))

        return {'type': 'ir.actions.act_window_close'}
