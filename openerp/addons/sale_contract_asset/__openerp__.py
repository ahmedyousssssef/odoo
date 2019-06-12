# -*- coding: utf-8 -*-

{
    'name': 'Deferred revenue management for contracts',
    'version': '1.0',
    'category': 'Sales',
    'description': """
This module allows you to set a deferred revenue on your subscription contracts.
""",
    'website': 'https://www.odoo.com/',
    'depends': ['sale_contract', 'account_asset'],
    'data': [
        'views/account_analytic_account_views.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
