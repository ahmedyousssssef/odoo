# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) 2014 InnOpen Group Kft (<http://www.innopen.eu>).


{
    'name': 'Hungarian - Accounting Reports',
    'version': '1.1',
    'category': 'Localization',
    'description': """
        Accounting reports for Hungarian
 """,
    'author': 'InnOpen Group Kft',
    'website': 'http://www.innopen.eu',
    'depends': [
        'l10n_hu', 'account_reports',
    ],
    'data': [
        'account_financial_html_report.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'OEEL-1',
}
