from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BussmaMarketingActivity(models.Model):
    _name = 'bussma.marketing.activity'
    _description = 'Marketing Activities'
    _order = 'id asc'

    name = fields.Char(string='Marketing Activity Name', required=True)
    code = fields.Char(string='Activity Code', readonly=True, copy=False, default='/')
    department_ids = fields.Many2many(
        'bussma.marketing.department',
        'bussma_activity_dept_rel',
        'activity_id',
        'dept_id',
        string='Departments'
    )
    active = fields.Boolean(string='Active', default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code') or vals.get('code') == '/':
                seq_code = self.env['ir.sequence'].next_by_code('bussma.marketing.activity')
                if not seq_code:
                    existing_codes = self.search([('code', '=like', 'ACT%')]).mapped('code')
                    max_num = 0
                    for c in existing_codes:
                        digits = ''.join(filter(str.isdigit, c or ''))
                        if digits:
                            max_num = max(max_num, int(digits))
                    seq_code = f"ACT{max_num + 1:04d}"
                vals['code'] = seq_code
        return super(BussmaMarketingActivity, self).create(vals_list)

    def unlink(self):
        protected_codes = ['ACT0001', 'ACT0002', 'ACT0003', 'ACT0004', 'ACT0005', 'ACT0006', 'ACT0007', 'ACT0008', 'ACT0009']
        protected_xml_ids = [
            'marketing_opportunity_management.activity_campaigns',
            'marketing_opportunity_management.activity_billboards',
            'marketing_opportunity_management.activity_messaging',
            'marketing_opportunity_management.activity_aerial_photo',
            'marketing_opportunity_management.activity_brochures',
            'marketing_opportunity_management.activity_av',
            'marketing_opportunity_management.activity_visual_identity',
            'marketing_opportunity_management.activity_social_media',
            'marketing_opportunity_management.activity_influencers',
        ]
        protected_records = self.env['bussma.marketing.activity']
        for xml_id in protected_xml_ids:
            rec = self.env.ref(xml_id, raise_if_not_found=False)
            if rec:
                protected_records |= rec

        for record in self:
            if record in protected_records or (record.code and record.code.upper() in protected_codes):
                raise UserError(_("Sorry, you cannot delete default marketing activity (%s).") % record.name)

        return super().unlink()