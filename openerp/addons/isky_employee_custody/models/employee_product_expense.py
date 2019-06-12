#	-*-	coding:	utf-8	-*-
from openerp import models, fields, api, _
from datetime import date, datetime
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError


class isky_employee_product_expense(models.Model):
    _name = 'employee.product.expense'

    @api.one
    @api.depends('payment_amount', 'price_unit', 'quantity',
                 'product_id', 'employee_custody_id.currency_id', 'employee_custody_id.company_id')
    def _compute_price(self):
        if self.payment_amount:
            self.price_subtotal = price_subtotal_signed = self.payment_amount
        else:
            price = self.price_unit
            self.price_subtotal = price_subtotal_signed = self.quantity * price

        if self.employee_custody_id.currency_id and self.employee_custody_id.currency_id != self.employee_custody_id.company_id.currency_id:
            price_subtotal_signed = self.employee_custody_id.currency_id.compute(price_subtotal_signed,
                                                                                 self.employee_custody_id.company_id.currency_id)
        self.price_subtotal_signed = price_subtotal_signed

    name = fields.Text(string='Description')
    product_id = fields.Many2one('product.product', string='Product',
                                 ondelete='restrict', index=True)
    account_id = fields.Many2one('account.account', string='Account',
                                 related='product_id.product_tmpl_id.property_account_expense_id',
                                 help="The expense account related to the selected product.")
    price_unit = fields.Monetary(string='Unit Price')

    price_subtotal = fields.Monetary(string='Amount',
                                     store=True, compute='_compute_price')

    price_subtotal_signed = fields.Monetary(string='Amount Signed', currency_field='company_currency_id',
                                            store=True, readonly=True, compute='_compute_price',
                                            help="Total amount in the currency of the company, negative for credit notes.")

    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1)
    company_id = fields.Many2one('res.company', string='Company',
                                 related='employee_custody_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='employee_custody_id.currency_id', store=True)
    company_currency_id = fields.Many2one('res.currency', related='employee_custody_id.company_currency_id',
                                          readonly=True)
    partner_id = fields.Many2one('res.partner', string='Supplier')
    check_invoice = fields.Boolean(string='Invoice?')
    type = fields.Selection([('payment', 'Payment'),
                             # ('invoice', 'Invoice'), To remove type 'invoice'
                             ('direct_expense', 'Direct Expense'),('payback', 'Payback')],
                            'Type', required=True, default='direct_expense')

    account_analytic_id = fields.Many2one('account.analytic.account',
                                          string='Analytic Account')
    employee_custody_id = fields.Many2one('employee.custody', string='Employee Custody')
    employee_id = fields.Many2one('hr.employee',related='employee_custody_id.employee_id', string='Employee', store=True)
    state = fields.Selection([('draft', 'New'),
                              ('open', 'Open'),  # used by cash statements
                              ('receiving_custody', 'Receiving Custody'),  # used by cash statements
                              ('pay', 'Payment'),  # used by cash statements
                              ('done', 'Closed'),
                              ('cancel', 'Cancelled')],
                             'Status', related='employee_custody_id.state', store=True)
    uom_id = fields.Many2one('product.uom', string='Unit of Measure',
                             ondelete='set null', readonly=True,
                             default=lambda self: self.env['product.uom'].search([], limit=1, order='id'))

    date = fields.Date('Date', default=fields.Date.context_today, required=True)

    attachment_ids = fields.Many2many(comodel_name='ir.attachment',
                                      relation='employee_expense_attachment_rel',
                                      column1='employee_expense_line_id',
                                      column2='attachment_id', string='Attachments')
    journal_id = fields.Many2one('account.journal', string='Payment Method',
                                 domain=[('type', 'in', ('bank', 'cash'))])
    payment_amount = fields.Monetary(string='Payment Amount')
    is_validated = fields.Boolean(string='Is validated?')
    amount_before_transaction = fields.Monetary(string='Amount Before Transaction', readonly=True)
    amount_after_transaction = fields.Monetary(string='Amount After Transaction', compute='_calc_amount_after_transaction')

    @api.model
    def create(self, vals):
        if 'payment_amount' in vals or 'price_unit' in vals:
            res = super(isky_employee_product_expense, self).create(vals)
            remaining_amount = res.employee_custody_id.close_balance
            res.amount_before_transaction = remaining_amount
            return res
        else:
            return super(isky_employee_product_expense, self).create(vals)


    @api.multi
    @api.depends('amount_before_transaction','price_subtotal','payment_amount','price_unit','quantity')
    def _calc_amount_after_transaction(self):
        for rec in self:
            rec.amount_after_transaction = rec.amount_before_transaction - rec.price_subtotal


    @api.constrains('date')
    def constrain_date(self):
        if datetime.strptime(self.date, "%Y-%m-%d").date() > date.today():
            raise UserError('Date can not be greater than today!')

    @api.v8
    def get_invoice_line_account(self, product):
        accounts = product.product_tmpl_id.get_product_accounts()
        return accounts['expense']

    @api.onchange('date')
    def _onchange_date(self):
        # price_unit = self.env['employee.custody'].search([('employee_custody_id', '=', self.ids)]).date
        for line in self.employee_custody_id.move_line_ids:
            if line.date > self.date:
                raise UserError("Transaction date should't be less than opening balance date")
            break
        return

    @api.onchange('type')
    def _onchange_type(self):
        return {'value': {'product_id': False, 'name': False, 'partner_id': False, 'account_analytic_id': False}}

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.ensure_one()
        domain = {}
        if not self.employee_custody_id:
            return

        company = self.employee_custody_id.company_id
        currency = self.employee_custody_id.currency_id

        if not self.product_id:
            self.price_unit = 0.0
            domain['uom_id'] = []
        else:
            product = self.product_id
            self.name = product.description_purchase
            account = self.get_invoice_line_account(product)
            if account:
                self.account_id = account.id

            if product.name:
                self.name = product.name

            if product.list_price:
                self.price_unit = product.list_price

            if not self.uom_id or product.uom_id.category_id.id != self.uom_id.category_id.id:
                self.uom_id = product.uom_id.id
            domain['uom_id'] = [('category_id', '=', product.uom_id.category_id.id)]

            if company and currency:
                if company.currency_id != currency:
                    self.price_unit = self.price_unit * currency.with_context(
                        dict(self._context or {}, date=fields.Date.today())).rate

                if self.uom_id and self.uom_id.id != product.uom_id.id:
                    self.price_unit = self.env['product.uom'].browse(self.uom_id.id)._compute_price(self.price_unit,product.uom_id)
        return {'domain': domain}

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        warning = {}
        result = {}
        self._onchange_product_id()
        if not self.uom_id:
            self.price_unit = 0.0
        if self.product_id and self.uom_id:
            if self.product_id.uom_id.category_id.id != self.uom_id.category_id.id:
                warning = {
                    'title': _('Warning!'),
                    'message': _(
                        'The selected unit of measure is not compatible with the unit of measure of the product.'),
                }
                self.uom_id = self.product_id.uom_id.id
        if warning:
            result['warning'] = warning
        return result

    @api.multi
    def _get_analytic_line(self):
        ref = self.employee_custody_id.name
        return {
            'name': self.employee_custody_id.name,
            'date': fields.Date.today(),
            'account_id': self.account_analytic_id.id,
            'unit_amount': self.quantity,
            'amount': self.price_subtotal_signed,
            'product_id': self.product_id.id,
            'product_uom_id': self.uom_id.id,
            'general_account_id': self.account_id.id,
            'ref': ref,
        }

    @api.multi
    def unlink(self):
        for line in self:
            if line.is_validated:
                raise UserError(_('You cannot delete a validated transaction.'))

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(isky_employee_product_expense, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        if 'amount_before_transaction' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    inv_value = 0.0
                    for line2 in lines:
                        inv_value += line2.amount_before_transaction
                        break
                    line['amount_before_transaction'] = inv_value
        return res