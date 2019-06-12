# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2008 JAILLET Simon - CrysaLEAD - www.crysalead.fr

{
    'name': 'France - Accounting Reports',
    'version': '1.1',
    'description': """
Accounting reports for France
================================

    """,
    'website': 'http://www.openerp.com',
    'category': 'Localization',
    'depends': ['l10n_fr', 'account_reports'],
    'data':[
        'account_financial_html_report.xml'
    ],
    'demo': [],
    'auto_install': True,
    'installable': True,
    'license': 'OEEL-1',
}
