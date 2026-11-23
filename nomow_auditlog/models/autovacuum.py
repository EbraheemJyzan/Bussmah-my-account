# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import api, fields, models


class AuditlogAutovacuum(models.TransientModel):
    _name = "auditlog.autovacuum"
    _description = "Auditlog - Delete old logs"

    name = fields.Char(string="Name")
    from_date = fields.Date(
        "From Date",
        help="Delete logs older than this date. If not set, all logs older than the number of days specified in the cron will be deleted.",
    )
    to_date = fields.Date(
        "To Date",
        help="Delete logs older than this date. If not set, all logs older than the number of days specified in the cron will be deleted.",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("done", "Done"),
        ],
        default="draft",
        string="State",
        help="State of the autovacuum operation.",
    )
    
    def autovacuum(self):
        for record in self:
            data_models = ("auditlog.log", "auditlog.http.request", "auditlog.http.session")
            for data_model in data_models:
                records = self.env[data_model].search(
                    [("create_date", ">=", record.from_date),("create_date", "<=", record.to_date)])                  
                records.unlink()
            record.state = "done"
