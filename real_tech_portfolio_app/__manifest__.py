{
    'name': 'Real Tech Portfolio App',
    'version': '18.0.1.0.0',
    'category': 'Sales/Portfolios',
    'summary': 'Manage Real Tech Portfolios and Dedicated Menu Access',
    'description': """
Real Tech Portfolio App Module:
1. Enables setting projects as Real Tech Portfolios.
2. Provides a dedicated Real Tech Portfolio App menu.
3. Manages dynamic menu visibility for Real Tech App users via ir.ui.menu.
    """,
    'author': 'Bussma',
    'depends': [
        'base',
        'bussma_system',
        'sales_and_auction_management',
        'marketing_opportunity_management',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/bussma_project_inherit_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
