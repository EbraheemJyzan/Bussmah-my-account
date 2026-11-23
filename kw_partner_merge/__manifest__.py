{
    'name': 'Partner merge',

    'author': 'NomowSoft Team',
    'website': "https://www.nomowsoft.com",

    'category': 'Extra Tools',
    'version': '18.0.0.0.1',

    'depends': ['base', ],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_jobs.xml',
        'views/kw_partner_duplicate_views.xml',
    ],

    'images': [
        'static/description/cover.png',
        'static/description/icon.png',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
