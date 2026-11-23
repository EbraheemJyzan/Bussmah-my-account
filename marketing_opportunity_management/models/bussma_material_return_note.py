from odoo import models, fields, api, _

class BussmaMaterialReturnNote(models.Model):
    _name = 'bussma.material.return.note'
    _description = 'Marketing Material Return Notes'
    _order = 'date desc, id desc'

    material_id = fields.Many2one(
        'bussma.marketing.material',
        string='Marketing Material',
        ondelete='cascade',
        required=True
    )
    marketing_id = fields.Many2one(
        related='material_id.marketing_id',
        string='Marketing Record',
        store=True,
        readonly=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Requested By',
        default=lambda self: self.env.user,
        required=True
    )
    date = fields.Datetime(
        string='Request Date',
        default=fields.Datetime.now,
        required=True
    )
    notes = fields.Text(
        string='Modification Notes',
        required=True
    )
    return_type = fields.Selection([
        ('rejected', 'Rejected'),
        ('modification', 'Modification'),
    ], string='Return Type', required=True)
    marketion_requst_type = fields.Selection([
        ('project_request', 'Project Request'),
        ('opportunity_request', 'Opportunity Request'),
        ('office_request', 'Office Request'),
    ], string='Marketing Request Type', required=True) 
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'bussma_mat_return_note_att_rel',
        'note_id',
        'att_id',
        string='Attachments'
    )
