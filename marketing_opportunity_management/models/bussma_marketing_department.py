from odoo import models, fields, _
from odoo.exceptions import UserError

class BussmaMarketingDepartment(models.Model):
    _name = 'bussma.marketing.department'
    _description = 'Marketing Departments'
    _order = 'sequence, id'

    name = fields.Char(string='Department Name', required=True, translate=True)
    code = fields.Char(string='Department Code')
    color = fields.Integer(string='Color Index')
    sequence = fields.Integer(string='Sequence', default=10)
    manager_id = fields.Many2one('res.users', string='Department Manager', tracking=True)
    member_ids = fields.Many2many(
        'res.users',
        'bussma_marketing_dept_user_rel',
        'dept_id',
        'user_id',
        string='Department Members'
    )
    active = fields.Boolean(string='Active', default=True)

    def unlink(self):
        protected_codes = ['CONTENT', 'DESIGN', 'DIGITAL', 'OPS']
        protected_xml_ids = [
            'marketing_opportunity_management.dept_content',
            'marketing_opportunity_management.dept_design',
            'marketing_opportunity_management.dept_digital',
            'marketing_opportunity_management.dept_ops',
        ]
        protected_records = self.env['bussma.marketing.department']
        for xml_id in protected_xml_ids:
            rec = self.env.ref(xml_id, raise_if_not_found=False)
            if rec:
                protected_records |= rec

        for record in self:
            if record in protected_records or (record.code and record.code.upper() in protected_codes):
                raise UserError(_("Sorry, you cannot delete default department (%s).") % record.name)

        return super().unlink()
