# -*- coding: utf-8 -*-
{
    'name': 'Bussmah Kanban & List View Open Access Settings',
    'version': '18.0.1.0.0',
    'summary': 'Control record open access from Kanban and List views based on user groups',
    'description': """
Bussmah Kanban & List View Open Access Settings:
================================================
- Create 'Kanban View Settings' model (kanban.view.setting)
- Configure models and groups allowed to open records from Kanban or List view
- If a user lacks permission, record opening is disabled (can_open="0" / no_open="1")
- Preserves native Odoo rules (if kanban is natively non-clickable, it remains disabled)
    """,
    'author': 'NomowSoft',
    'website': 'https://www.nomowsoft.com',
    'category': 'Technical',
    'depends': [
        'base',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/kanban_view_setting_views.xml',
        'views/tree_view_setting_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bussmah_kanban_view_settings/static/src/views/kanban/kanban_controller.js',
            'bussmah_kanban_view_settings/static/src/views/list/list_controller.js',
            'bussmah_kanban_view_settings/static/src/views/list/list_renderer.js',
            'bussmah_kanban_view_settings/static/src/views/list/list_renderer.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
