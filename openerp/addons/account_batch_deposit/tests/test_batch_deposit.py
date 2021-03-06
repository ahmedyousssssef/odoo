# -*- coding: utf-8 -*-

import time

from openerp.addons.account.tests.account_test_classes import AccountingTestCase
from openerp.modules.module import get_module_resource

class TestBatchDeposit(AccountingTestCase):

    def setUp(self):
        super(TestBatchDeposit, self).setUp()

        # Get some records
        self.customers = self.env['res.partner'].search([('customer', '=', True)])
        self.batch_deposit = self.env.ref('account_batch_deposit.account_payment_method_batch_deposit')

        # Create a bank journal
        journal_account = self.env['account.account'].create({
            'code': 'BNKT',
            'name': 'Bank Test',
            'user_type_id': self.ref('account.data_account_type_liquidity')
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Bank Test',
            'code': 'BNKT',
            'type': 'bank',
            'default_debit_account_id': journal_account.id,
            'default_credit_account_id': journal_account.id,
            'company_id': self.env.ref('base.main_company').id
        })

        # Create some payments
        self.payments = [
            self.createPayment(self.customers[0], 100),
            self.createPayment(self.customers[1], 200),
            self.createPayment(self.customers[2], 500),
        ]

    def createPayment(self, partner, amount):
        """ Create a batch deposit payment """
        return self.env['account.payment'].create({
            'journal_id': self.journal.id,
            'payment_method_id': self.batch_deposit.id,
            'payment_type': 'inbound',
            'payment_date': time.strftime('%Y') + '-07-15',
            'amount': amount,
            'partner_id': partner.id,
            'partner_type': 'customer',
        })

    def test_DepositLifeCycle(self):
        # Create and "print" a deposit
        deposit = self.env['account.batch.deposit'].create({
            'journal_id': self.journal.id,
            'payment_ids': [(4, payment.id, None) for payment in self.payments],
        })
        deposit.print_batch_deposit()
        self.assertTrue(all(payment.state == 'sent' for payment in self.payments))
        self.assertTrue(deposit.state == 'sent')
        # Create a bank statement
        bank_statement = self.env['account.bank.statement'].create({
            'balance_start': 0.0,
            'balance_end_real': 800.0,
            'date': time.strftime('%Y') + '-08-01',
            'journal_id': self.journal.id,
            'company_id': self.env.ref('base.main_company').id,
        })
        bank_statement_line = self.env['account.bank.statement.line'].create({
            'amount': 800,
            'date': time.strftime('%Y') + '-07-18',
            'name': 'DEPOSIT',
            'statement_id': bank_statement.id,
        })
        # Simulate the process of reconciling the statement line using the batch deposit
        deposits_reconciliation_data = bank_statement.get_batch_deposits_data()
        self.assertTrue(len(deposits_reconciliation_data), 1)
        self.assertTrue(deposits_reconciliation_data[0]['id'], deposit.id)
        deposit_reconciliation_lines = bank_statement_line.get_move_lines_for_reconciliation_widget_by_batch_deposit_id(deposit.id)
        self.assertTrue(len(deposit_reconciliation_lines), 3)
        move_line_ids = [line['id'] for line in deposit_reconciliation_lines]
        move_line_recs = self.env['account.move.line'].browse(move_line_ids)
        bank_statement_line.process_reconciliation(payment_aml_rec=move_line_recs)
        self.assertTrue(all(payment.state == 'reconciled' for payment in self.payments))
        self.assertTrue(deposit.state == 'reconciled')
