# -*- coding: utf-8 -*-
{
    'name': 'Bussmah Attachment Security',
    'version': '18.0.1.0.0',
    'summary': 'Restrict Attachment Deletion to System Administrators',
    'description': """
Bussmah Attachment Security Module:
Restricts attachment deletion across specified Bussmah modules:
- bussma_system
- financial_management
- helpdesk_ticket
- hr_requests
- marketing_opportunity_management
- sales_and_auction_management

Only users with base.group_system (System Administrators) are allowed to delete attachments.
    """,
    'author': 'NomowSoft',
    'website': 'https://www.nomowsoft.com',
    'category': 'Security',
    'depends': [
        'base',
        'mail',
        'bussma_system',
        'financial_management',
        'helpdesk_ticket',
        'hr_requests',
        'marketing_opportunity_management',
        'sales_and_auction_management',
    ],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
