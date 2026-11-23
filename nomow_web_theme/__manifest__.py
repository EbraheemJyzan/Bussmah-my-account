{
    'name': 'Nomow Backend Theme', 
    'summary': 'Odoo Community Backend Theme',
    'description': '''
        This module offers a mobile compatible design for Odoo Community. 
        Furthermore it allows the user to define some design preferences.
    ''',
    'version': '18.0', 
    'category': 'Tools/UI',
    'license': 'LGPL-3', 
    'author': 'Nomow Soft',
    'website': 'https://nomowsoft.com/',
    'depends': ['nomow_web_colors', "auth_signup", "web_tour"],
    'data': [
        # Data 
        'data/nomow_image_logo_data.xml',

        'views/res_company.xml',
        'views/custom_tap_icon.xml',
        'views/apps_menu_views.xml', 
        'views/res_users_views.xml',
        'views/pages/login_template.xml',
        ],
    'assets': {
        'web._assets_primary_variables':[
            'nomow_web_theme/static/src/scss/primary_variable.scss',
        ],
        'web.assets_backend': [
           'nomow_web_theme/static/src/webclient/**/*',
            'nomow_web_theme/static/src/components/apps_menu_tools.esm.js',
            'nomow_web_theme/static/src/components/custom_tap_title.js',
            'nomow_web_theme/static/src/components/apps_menu_item/*',
            'nomow_web_theme/static/src/components/apps_menu/*',
            'nomow_web_theme/static/src/components/menu_canonical_searchbar/*',
            'nomow_web_theme/static/src/components/menu_odoo_searchbar/*',
            'nomow_web_theme/static/src/components/menu_fuse_searchbar/*',
            'nomow_web_theme/static/src/components/menu_searchbar/*',
        ],
        "web.assets_frontend": [
            # SCSS
            "nomow_web_theme/static/src/scss/login.scss",
        ],
    },
   
    'installable': True,
    'sequence': -1,
    'application': False,
    'auto_install': False,
}
