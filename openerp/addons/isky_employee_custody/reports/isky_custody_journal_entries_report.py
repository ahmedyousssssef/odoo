# -*- coding: utf-8 -*-

from openerp import models, fields, api, tools


class IskyCustodyJournalEntries(models.Model):
    _name = 'isky.custody.journal.entries'
    _auto = False

    # Calculate balance for each employee
    @api.multi
    def _get_balance(self):
        self._cr.execute("SELECT DISTINCT(employee_id) FROM isky_custody_journal_entries")
        for each_emp in self._cr.fetchall():
            balance = 0
            emp_entries = self.env['isky.custody.journal.entries'].search([('employee_id', '=', each_emp[0])])
            for each_entr in emp_entries:
                if each_entr.debit:
                    balance += each_entr.debit
                if each_entr.credit:
                    balance -= each_entr.credit
                each_entr.balance = balance

    # Display balance in group
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(IskyCustodyJournalEntries, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                                    orderby=orderby, lazy=lazy)
        for line in res:
            line['balance'] = line['debit'] - line['credit']
        return res

    date = fields.Date(string="Date")
    debit = fields.Float('Debit')
    credit = fields.Float('Credit')
    custody_id = fields.Many2one('employee.custody')
    employee_id = fields.Many2one('hr.employee', string="Employee")
    type = fields.Selection([('payment', 'Payment'),
                             ('direct_expense', 'Direct Expense'), ('payback', 'Payback')],
                            'Type')
    balance = fields.Float(compute="_get_balance")

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'isky_custody_journal_entries')
        cr.execute("""
                create or replace view isky_custody_journal_entries as  (
                SELECT account_move_line.id as id,
                    account_move_line.date as date,
                    account_move_line.debit as debit,
                    account_move_line.credit as credit,
                    employee_custody.employee_id as employee_id,
                    account_move_line.custody_id as custody_id,
                    account_move_line.type as type
                    FROM
                        account_move_line
                    LEFT JOIN employee_custody
                    ON
                        employee_custody.id = account_move_line.custody_id
                    WHERE
                        account_move_line.custody_id IS NOT NULL AND ((account_move_line.ref IS NOT NULL AND account_move_line.credit = 0) or(account_move_line.ref IS NULL AND account_move_line.debit = 0))
                    ORDER BY account_move_line.id

     )""")

