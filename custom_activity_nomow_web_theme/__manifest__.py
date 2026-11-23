{
    'name': 'Custom Activity Nomow Web Theme',
    'version': '18.0.1.0.0',
    'summary': 'Display user activity notification counter badge on route menu',
    'description': """
        This module inherits nomow_web_theme to add the user activity notification 
        counter badge on the route menu / sidebar button.
    """,
    'category': 'Tools/UI',
    'author': 'Nomow Soft',
    'website': 'https://nomowsoft.com/',
    'license': 'LGPL-3',
    'depends': ['nomow_web_theme', 'mail', 'web', 'bussma_system', 'financial_management', 'marketing_opportunity_management', 'hr_requests', 'sales_and_auction_management'],
    'data': [
        'security/security.xml',
        'views/entries_kanban_view.xml',
        'views/financial_request_kanban_view.xml',
        'views/hr_request_kanban_view.xml',
        'views/opportunity_kanban_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_activity_nomow_web_theme/static/src/scss/custom_activity_badge.scss',
            'custom_activity_nomow_web_theme/static/src/scss/custom_breadcrumb.scss',
            'custom_activity_nomow_web_theme/static/src/webclient/navbar/navbar_activity_patch.js',
            'custom_activity_nomow_web_theme/static/src/webclient/navbar/navbar_activity_patch.xml',
            'custom_activity_nomow_web_theme/static/src/chatter/chatter_delete_patch.js',
            'custom_activity_nomow_web_theme/static/src/chatter/chatter_delete_patch.xml',
            'custom_activity_nomow_web_theme/static/src/chatter/chatter_edit_patch.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
