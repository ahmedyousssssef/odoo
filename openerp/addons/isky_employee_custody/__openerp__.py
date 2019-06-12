# -*- encoding: utf-8 -*-

{
    'name': 'Employee Custody',
    'description': '''
    This module allows employees to take custodies from the company.\n
     you have to configure the accounting for the custody first from the custody configuration menu.
    ''',
    'author': 'iSky Development',
    'website': 'www.iskydev.com',
    'version': '10.0',
    'depends': ['base', 'sale', 'account', 'hr', 'hr_payroll', 'account_accountant'],
    'data': [
        'security/isky_custody_group_security.xml',
        'security/ir.model.access.csv',
        'views/custody_transactions_view.xml',
        'views/hr_employee_inherit.xml',
        'views/employee_custody_view.xml',
        'views/account_invoice_inherit.xml',
        'views/isky_sequence_view.xml',
        'reports/isky_employee_custody_wizard.xml',
        'reports/isky_employee_custody_display.xml',
        'reports/isky_custody_report.xml',
        'reports/isky_custody_journal_entries_report.xml',
        'views/menuitems.xml',
    ]
}
