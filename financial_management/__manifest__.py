{
    'name': 'Financial Management',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Manage Invoice and Marketing Expense Requests',
    'description': """
Financial Management Module:
- Manage invoice and expense requests
- Multi-stage approval workflow (9 stages)
- Track request status from submission to archiving
    """,
    'author': 'Bussma',
    'depends': [
        'base',
        'mail',
        'request',
        'bussma_system',
        'sales_and_auction_management',
        'marketing_opportunity_management',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/financial_request_sequence.xml',
        'data/financial_request_stage_data.xml',
        'data/financial_request_mail_template_data.xml',
        'views/financial_request_views.xml',
        'views/bussma_marketing_material_inherit_views.xml',
        'views/record_control_wizard_inherit_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
