# -*- coding: utf-8 -*-
{
    'name': "helpdesk_ticket",

    'summary': "Gestion des tickets d’assistance client",

    'description': """
Module de gestion des tickets d'assistance avec workflow, séquence et notifications.
    """,

    'author': "NomowSoft",
    'website': "https://www.nomowsoft.com",
    'category': 'Services/Helpdesk',
    'version': '18.0.1.0',
    'depends': ['base', 'mail', 'bussma_system'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ticket_sequence.xml',
        'reports/ticket_report_templates.xml',
        'reports/ir_action_report.xml',
        'views/ticket_views.xml',
        'views/ticket_menu.xml',
    ],
    'image': ['static/description/Miniature.gif'],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

