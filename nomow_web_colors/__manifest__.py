{
    'name': 'Nomow Colors', 
    'summary': 'Customize your Odoo colors',
    'description': '''
        This module gives you options to customize the theme colors.
    ''',
    'version': '18.0', 
    'category': 'Tools/UI',
    'license': 'LGPL-3', 
    'author': 'Nomow Soft',
    'website': 'https://nomowsoft.com/',
    'depends': ['base_setup','web_editor'],
    'data': [
        'templates/webclient.xml',
        'views/res_config_settings.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'nomow_web_colors/static/src/scss/colors.scss'),
            (
                'before', 
                'nomow_web_colors/static/src/scss/colors.scss', 
                'nomow_web_colors/static/src/scss/colors_light.scss'
            ),
            (
                'after', 
                'web/static/src/scss/primary_variables.scss', 
                'nomow_web_colors/static/src/scss/variables.scss'
            ),
        ],
        'web.assets_web_dark': [
            (
                'after', 
                'nomow_web_colors/static/src/scss/colors.scss',
                'nomow_web_colors/static/src/scss/colors_dark.scss'
            ),
        ],
    },
   
    'installable': True,
    'application': False,
    'auto_install': False,
    'uninstall_hook': '_uninstall_cleanup',
}
