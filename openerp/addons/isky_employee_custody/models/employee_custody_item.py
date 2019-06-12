#	-*-	coding:	utf-8	-*-

from openerp import models, fields, api


class isky_employee_custody_item(models.Model):
    _name = 'employee.custody.item'

    # Fileds declaration

    employee_custody_id = fields.Many2one('employee.custody', string='Custody')
    name = fields.Char(related='employee_custody_id.name', readonly=True)
    loan_id = fields.Many2one('custody.category', related='employee_custody_id.loan_id', readonly=True)
    open_balance = fields.Monetary(related='employee_custody_id.open_balance', readonly=True)
    close_balance = fields.Monetary(related='employee_custody_id.close_balance', readonly=True)
    total_transactions = fields.Monetary(related='employee_custody_id.total_transactions', readonly=True)
    reconciled_amount = fields.Monetary(related='employee_custody_id.reconciled_amount', readonly=True)
    state = fields.Selection(related='employee_custody_id.state', readonly=True)
    employee_id = fields.Many2one('hr.employee', related='employee_custody_id.employee_id', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='employee_custody_id.currency_id')