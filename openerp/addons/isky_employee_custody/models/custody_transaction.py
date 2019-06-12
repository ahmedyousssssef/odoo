# -*- coding: utf-8 -*-
from openerp import models, fields, api, tools

class IskyCustodyTransactions(models.Model):
    _name = 'isky.custody.transaction'
    _auto = False


    @api.multi
    def get_after_before_amount(self):
        for rec in self:
            objs = rec.search([('custody_id','=',rec.custody_id.id)])
            if len(objs):
                objs[0].amount_before = objs[0].custody_id.open_balance
                objs[0].amount_after = objs[0].custody_id.open_balance - objs[0].amount
                for index in range(1,len(objs)):
                    objs[index].amount_before = objs[index - 1].amount_after
                    objs[index].amount_after = objs[index].amount_before - objs[index].amount


    employee_id = fields.Many2one('hr.employee', string="Employee")
    date = fields.Date(string="Date")
    custody_id = fields.Many2one('employee.custody',string="Custody")
    custody_amount = fields.Monetary(string="Custody Amount",related='custody_id.open_balance')
    type = fields.Selection([('payment', 'Payment'),
                             ('direct_expense', 'Direct Expense'),('payback', 'Payback')],
                            'Type', required=True, default='direct_expense')

    supplier_id = fields.Many2one('res.partner',string="Supplier")
    product_id = fields.Many2one('product.product',string="Product")
    amount = fields.Monetary(string="Amount")
    amount_before = fields.Monetary(string="Amount Before",compute='get_after_before_amount')
    amount_after = fields.Monetary(string="Remaining Amount",compute='get_after_before_amount')
    currency_id = fields.Many2one('res.currency',string="Currency")
    state = fields.Char(string="Status")

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(IskyCustodyTransactions, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                                    orderby=orderby, lazy=lazy)
        if 'custody_amount' in fields and 'employee_id' in fields and 'custody_id' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.env['employee.custody'].search(line['__domain'])
                    inv_value = 0.0
                    for line2 in lines:
                        inv_value += line2.open_balance
                    line['custody_amount'] = inv_value
                    line['amount_after'] = line['custody_amount'] - line['amount']
        return res

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'isky_custody_transaction')
        cr.execute("""
                create or replace view isky_custody_transaction as  (
                SELECT emp_expenses.id,
                emp_expenses.employee_id as employee_id,
                emp_expenses.employee_custody_id as custody_id,
                emp_expenses.date as date,
                emp_expenses.currency_id as currency_id,
                emp_expenses.product_id as product_id,
                emp_expenses.price_subtotal as amount,
                emp_expenses.type as type,
                emp_expenses.partner_id as supplier_id,
                emp_expenses.state as state
                
                        
                FROM
                    employee_product_expense as emp_expenses
                
                

            )""")
