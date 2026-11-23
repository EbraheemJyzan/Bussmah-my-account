# -*- coding: utf-8 -*-
{
    'name': 'Studies Enhancements',
    'version': '18.0.1.0.0',
    'summary': 'Add enhancements and actions to the studies form',
    'author': 'NomowSoft',
    'website': 'https://www.nomowsoft.com',
    'category': 'Sales',
    'depends': ['base', 'bussma_system'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sector_manager_entries_wizard_views.xml',
        'wizard/committee_entries_wizard_views.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
