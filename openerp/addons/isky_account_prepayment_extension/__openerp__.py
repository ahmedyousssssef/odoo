# -*- coding: utf-8 -*-
{
    'name': 'Account Prepayment for real estate',
    'version': '1.0',
    'category': 'Account',
    'sequence': 19,
    'summary': 'Account Prepayment',
    'description': """
Prepayment Process with payment wizard
==================================================
Create the possibility to generate the prepayment  directly from the payment wizard:
** add the prepayment account in the partner

** add a check box in the payment form Prepayment: if checked the prepayment account in the partner will be chosen

** Usage for Supplier:
Normal Payment (Choose the invoice in the payment form)
AP 		debit 	3000
Bank 	Credit 	-3000


** Prepayment Move (At money reception, use the payment form with prepayment and select no invoice). It creates:
Prepayment 		debit 	1000
Bank 			Credit 	-1000

** Create an Invoice
AP				Credit 	-3000
Sales 			Debit 	3000

** New Payment (after invoice is created)
Use the payment form (no prepayment option and select the invoice and already existing Prepayment move)
Prepayment 		Credit 	-1000
AP	 			Debit 	3000
Bank			Credit	-2000

    """,
    'author': 'Isky',
    'website': 'http://www.iskydev.com',
    'images' : [],
    'depends': ['account', 'account_voucher'],
    'data': [
        'views/account_view.xml',
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
