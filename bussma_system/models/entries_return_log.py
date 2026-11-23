# -*- coding: utf-8 -*-
from odoo import api, fields, models

class EntriesReturnLog(models.Model):
    _name = 'entries.return.log'
    _description = 'Entries Return Log'
    _order = 'date desc'

    entry_id = fields.Many2one('entries', string='Entry', required=True, ondelete='cascade')
    return_type = fields.Selection([
        ('study_to_analyst', 'Study to Analyst'),
        ('manager_to_committee', 'Manager to Committee'),
        ('manager_to_department', 'Manager to Department'),
        ('contract_to_negotiator', 'Contract to Negotiator'),
        ('deputy_to_negotiator', 'Deputy Studies Manager to Negotiator'),
        ('return_to_lister', 'Return to Lister'),
        ('data_completion', 'Data Completion'),
    ], string='Return Type', required=True)
    
    study_type_detail = fields.Selection([
        ('standard', 'Standard'),
        ('specialized', 'Specialized'),
        ('cities', 'Cities'),
    ], string='Study Type Details')

    note = fields.Text(string='Note / Reason')
    date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', string='Returned By', default=lambda self: self.env.user, required=True)
