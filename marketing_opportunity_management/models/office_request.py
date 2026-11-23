# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class OfficeRequest(models.Model):
    _name = 'office.request'
    _description = 'Office Requests'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    code = fields.Char(string='Request Number', required=True, readonly=True, copy=False, default='/')
    name = fields.Char(string='Request Title', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Client', tracking=True)

    project_code = fields.Char(string='Project Code', tracking=True)
    project_name = fields.Char(string='Project Name', tracking=True)
    city_id = fields.Many2one('res.country.state', string='City', domain="[('country_id.code', '=', 'SA'), ('code', 'ilike', 'CT_')]", tracking=True)
    district_id = fields.Many2one('res.city', string='District', domain="[('state_id', '=', city_id)]", tracking=True)

    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.city_id and self.district_id and self.district_id.state_id != self.city_id:
            self.district_id = False
    property_type_id = fields.Many2one('property.type', string='Property Type', tracking=True)
    area_sqm = fields.Float(string='Area (sqm)', tracking=True)
    sale_price = fields.Float(string='Sale Price', tracking=True)

    request_date = fields.Date(string='Request Date', default=fields.Date.context_today, readonly=True)
    department_id = fields.Many2one('office.department', string='Department', tracking=True)
    requested_by_id = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Priority', default='medium', tracking=True)
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
    ], string='Request Type', tracking=True)
    employee_name = fields.Char(string='Employee Name', tracking=True)
    job_title = fields.Char(string='Job Title', tracking=True)
    employee_number = fields.Char(string='Employee Number', tracking=True)
    employee_email = fields.Char(string='Employee Email', tracking=True)
    phone_number = fields.Char(string='Phone Number', tracking=True)
    extension_number = fields.Char(string='Extension Number', tracking=True)
    region_id = fields.Many2one('res.country.state', string='Region', domain="[('country_id.code', '=', 'SA')]", tracking=True)
    property_code = fields.Char(string='Property Code', tracking=True)
    signboard_size = fields.Char(string='Signboard Size', tracking=True)
    needs_identity = fields.Boolean(string='Needs Identity?', tracking=True)
    needs_content_writing = fields.Boolean(string='Needs Content Writing?', tracking=True)
    # Project Request Fields
    project_type_selection = fields.Selection([
        ('sales', 'Direct Sale'),
        ('auction_pvt', 'Private Auction'),
        ('auction_enf', 'Enforcement Auction'),
        ('city', 'Cities'),
        ('other', 'Other'),
    ], string='Project Type', tracking=True)
    has_proposed_project_name = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Has Proposed Project Name?', tracking=True)
    proposed_project_name = fields.Char(string='Proposed Project Name', tracking=True)
    is_masterplan = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Is Project a Masterplan/Scheme?', tracking=True)
    # Change Request Fields
    change_request_type = fields.Selection([
        ('add_property', 'Add Property'),
        ('remove_property', 'Remove Property'),
        ('other', 'Other'),
    ], string='Change Request Type', tracking=True)
    target_marketing_project_id = fields.Many2one('bussma.marketing', string='Target Marketing Project to Edit', tracking=True)
    # Shared New Fields
    delivery_date = fields.Date(string='Delivery Date', tracking=True)
    has_attachments = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Has Attachments?', tracking=True)
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed')
    ], string='Status', default='new', tracking=True)
    description = fields.Text(string='Request Description', required=True)
    marketing_id = fields.Many2one('bussma.marketing', string='Related Marketing Record', tracking=True)
    return_to_requester_notes = fields.Text(string='Return Notes from Marketing', tracking=True)
    attachment_return_ids = fields.Many2many(
        'ir.attachment',
        'office_req_return_att_rel',
        'req_id',
        'att_id',
        string='Return Attachments'
    )
    is_returned_to_requester = fields.Boolean(string='Returned from Marketing', default=False, tracking=True)
    material_ids = fields.Many2many(related='marketing_id.material_ids', string='Marketing Materials Results', readonly=True)
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

    def init(self):
        super().init()
        self.env.cr.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'office_request' AND column_name = 'request_description'
                ) THEN
                    UPDATE office_request
                    SET description = CASE 
                        WHEN (description IS NULL OR trim(description) = '') THEN request_description
                        WHEN (request_description IS NOT NULL AND trim(request_description) != '' AND position(trim(request_description) in description) = 0) 
                            THEN description || E'\n\n' || request_description
                        ELSE description
                    END
                    WHERE request_description IS NOT NULL AND trim(request_description) != '';
                END IF;
            END $$;
        """)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', '/') == '/':
                vals['code'] = self.env['ir.sequence'].next_by_code('office.request') or '/'
        return super(OfficeRequest, self).create(vals_list)

    def action_open_marketing_wizard(self):
        self.ensure_one()
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'office.request'),
            ('res_id', '=', self.id)
        ])
        return {
            'name': _('Resend Marketing Request') if (self.marketing_id and self.is_returned_to_requester) else _('Create Marketing Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'office.request.marketing.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_office_request_id': self.id,
                'default_name': self.name,
                'default_project_name': self.project_name,
                'default_city_id': self.city_id.id if self.city_id else False,
                'default_district_id': self.district_id.id if self.district_id else False,
                'default_property_type_id': self.property_type_id.id if self.property_type_id else False,
                'default_area_sqm': self.area_sqm,
                'default_sale_price': self.sale_price,
                'default_description': self.description,
                'default_department_id': self.department_id.id if self.department_id else False,
                'default_requested_by_id': self.requested_by_id.id if self.requested_by_id else False,
                'default_marketing_id': self.marketing_id.id if self.marketing_id else False,
                'default_attachments_ids': [(6, 0, attachments.ids)],
            }
        }

