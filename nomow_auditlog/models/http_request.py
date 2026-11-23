# -*- coding: utf-8 -*-
from psycopg2.extensions import AsIs
from odoo import api, fields, models
from odoo.http import request


class AuditlogHTTPRequest(models.Model):
    _name = "auditlog.http.request"
    _description = "Auditlog - HTTP request log"
    _order = "create_date DESC"

    display_name = fields.Char("Name", compute="_compute_display_name", store=True)
    name = fields.Char("Path")
    root_url = fields.Char("Root URL")
    user_id = fields.Many2one("res.users", string="User")
    http_session_id = fields.Many2one(
        "auditlog.http.session", string="Session", index=True
    )
    user_context = fields.Char("Context")
    log_ids = fields.One2many("auditlog.log", "http_request_id", string="Logs")

    ip_address = fields.Char("IP Address")
    browser = fields.Char("Browser")
    os = fields.Char("OS")

    @api.depends("create_date", "name")
    def _compute_display_name(self):
        for httprequest in self:
            create_date = httprequest.create_date or fields.Datetime.now()
            tz_create_date = fields.Datetime.context_timestamp(httprequest, create_date)
            httprequest.display_name = "{} ({})".format(
                httprequest.name or "?", fields.Datetime.to_string(tz_create_date)
            )

    @api.model
    def current_http_request(self):
        if not request:
            return False
        http_session_model = self.env["auditlog.http.session"]
        httprequest = request.httprequest
        if httprequest:
            auditlog_req_id = getattr(httprequest, "auditlog_http_request_id", None)
            if auditlog_req_id:
                self.env.cr.execute(
                    "SELECT id FROM %s WHERE id = %s",
                    (AsIs(self._table), auditlog_req_id),
                )
                if self.env.cr.fetchone():
                    return auditlog_req_id
            
            headers = httprequest.headers
            ip_address = headers.get('X-Forwarded-For', '').split(',')[0].strip() or httprequest.remote_addr
            ua = httprequest.user_agent
            
            vals = {
                "name": httprequest.path,
                "root_url": httprequest.url_root,
                "user_id": request.uid,
                "http_session_id": http_session_model.current_http_session(),
                "user_context": request.context,
                "ip_address": ip_address,
                "browser": ua.browser,
                "os": ua.platform,
            }
            new_id = self.create(vals).id
            setattr(httprequest, "auditlog_http_request_id", new_id)
            return new_id
        return False
