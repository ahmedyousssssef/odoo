# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Norway - Accounting Reports',
    'version': '1.1',
    'description': """
Accounting reports for Norway
================================
    """,
    'author': 'Rolv Råen',
    'category': 'Localization',
    'depends': [
        'l10n_no', 'account_reports',
    ],
    'data': [
        'account_financial_report.xml'
    ],
    'demo': [],
    'auto_install': True,
    'installable': True,
    'license': 'OEEL-1',
}
