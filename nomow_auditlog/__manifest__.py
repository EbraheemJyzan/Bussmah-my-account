# -*- coding: utf-8 -*-
{
    "name": "Nomow Audit Log",
    "version": "18.0.1.0.4",
    "license": "AGPL-3",
    'author': "NomowSoft",
    'website': "https://www.nomowsoft.com",
    "category": "Tools",
    "depends": ["base"],
    "data": [
        "security/auditlog_security.xml",
        "security/ir.model.access.csv",
        "views/auditlog_autovacuum_views.xml",
        "views/auditlog_view.xml",
        "views/http_request_view.xml",
        "views/http_session_view.xml",
        "views/menu_item.xml",
    ],
    "application": True,
    "installable": True,
}
