# -*- coding: utf-8 -*-
{
    'name': 'Bussmah Templates',
    'version': '18.0.1.0.0',
    'category': 'Custom',
    'summary': 'Templates screen to simplify record creation',
    'description': """
    Bussmah Templates Module
    ========================
    Provides a "Templates" screen displaying Kanban cards for pre-configured templates.
    Clicking a card opens the designated form view directly in creation mode.
    """,
    'author': 'NomowSoft',
    'website': 'https://www.nomowsoft.com',
    'depends': [
        'base',
        'web',
        'bussma_system',
        'hr_requests',
        'marketing_opportunity_management',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/bussma_template_data.xml',
        'views/bussma_template_views.xml',
        'views/menus.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
