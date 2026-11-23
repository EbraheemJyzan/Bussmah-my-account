from odoo import models, fields

class OfficeDepartment(models.Model):
    _name = 'office.department'
    _description = 'Office Department'
    _order = 'name asc'

    name = fields.Char(string='Department Name', required=True)
    code = fields.Char(string='Department Code')
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')
