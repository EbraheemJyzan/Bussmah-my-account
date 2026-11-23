from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BussmaOpportunityDepartment(models.Model):
    _name = 'bussma.opportunity.department'
    _description = 'Opportunity Department'
    _order = 'id'

    name = fields.Char(string='Department Name', required=True, translate=True, default='Opportunity Department')
    code = fields.Char(string='Department Code', default='OPPORTUNITY')
    member_ids = fields.Many2many(
        'res.users',
        'bussma_opportunity_dept_user_rel',
        'dept_id',
        'user_id',
        string='Opportunity Department Members'
    )
    active = fields.Boolean(string='Active', default=True)

    @api.model
    def get_opportunity_department(self):
        dept = self.env.ref('marketing_opportunity_management.dept_opportunity', raise_if_not_found=False)
        if not dept:
            dept = self.search([('code', '=', 'OPPORTUNITY')], limit=1)
        if not dept:
            dept = self.search([], limit=1)
        return dept

    @api.model
    def get_opportunity_members(self):
        dept = self.get_opportunity_department()
        if dept and dept.member_ids:
            return dept.member_ids.filtered(lambda u: u.active)
        return self.env['res.users']

    @api.model
    def get_opportunity_member_emails(self):
        members = self.get_opportunity_members()
        return list(set(u.email.strip() for u in members if u.email and u.email.strip()))

    def unlink(self):
        protected_xml_ids = [
            'marketing_opportunity_management.dept_opportunity',
        ]
        protected_records = self.env['bussma.opportunity.department']
        for xml_id in protected_xml_ids:
            rec = self.env.ref(xml_id, raise_if_not_found=False)
            if rec:
                protected_records |= rec

        for record in self:
            if record in protected_records or (record.code and record.code.upper() == 'OPPORTUNITY'):
                raise UserError(_("Sorry, you cannot delete the default opportunity department."))

        return super().unlink()
