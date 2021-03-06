# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Indian - Accounting Reports',
    'version': '1.1',
    'description': """
Accounting reports for India
================================
    """,
    'category': 'Localization',
    'depends': ['l10n_in', 'account_reports'],
    'data': [
        'account_financial_html_report.xml'
    ],
    'demo': [],
    'auto_install': True,
    'installable': True,
    'license': 'OEEL-1',
}
