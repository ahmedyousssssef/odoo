# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (C) 2011- Slobodni programi d.o.o., Zagreb

{
    'name': 'Croatia - RRIF 2012 COA - Accounting Reports',
    'version': '1.1',
    'description': """
Accounting reports for Croatia
================================
    """,
    'author': ['OpenERP Croatian Community'],
    'website': 'https://code.launchpad.net/openobject-croatia',
    'category': 'Localization',
    'depends': ['l10n_hr', 'account_reports'],
    'data': [
        'account_financial_html_report.xml'
    ],
    'demo': [],
    'auto_install': True,
    'installable': True,
    'license': 'OEEL-1',
}
