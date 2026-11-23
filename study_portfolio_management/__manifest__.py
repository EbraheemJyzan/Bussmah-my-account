# -*- coding: utf-8 -*-
{
    'name': 'Study Portfolio Management',
    'version': '18.0.1.0.0',
    'category': 'Real Estate/Studies',
    'summary': 'Manage Study Portfolios and assign properties',
    'description': """
Study Portfolio Management Module:
==================================
- Create and manage study portfolios.
- Link portfolios to properties (entries) via One2many.
- Dedicated menu under Studies (direct_sale_menu).
- Assign properties to portfolios using assign wizard.
- Import properties with portfolio linkage (Entries and Eanfaz).
- Filter out portfolio-assigned properties from standard study actions.
    """,
    'author': 'Bussma',
    'depends': [
        'base',
        'mail',
        'bussma_system',
        'sales_and_auction_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/study_portfolio_views.xml',
        'views/entries_inherit_views.xml',
        'views/import_wizard_inherit_views.xml',
        'views/actions_inherit_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
