#	-*-	coding:	utf-8	-*-
from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError
from num2words import num2words
import datetime
from datetime import date


class CustodyCategory(models.Model):
    _name = 'custody.category'
    name = fields.Char('Custody Category Name', required=True)
    loan_description = fields.Text('Description', required=True)


class isky_employee_custody(models.Model):
    _name = 'employee.custody'
    _order = 'employee_code'

    # Read Group to display calcution of fields in group
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(isky_employee_custody, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                            orderby=orderby, lazy=lazy)
        if 'employee_id' in fields and 'employee_id' in groupby:
            for line in res:
                total_amount_curr = 0
                get_custody_obj = self.env['employee.custody'].search([('employee_id', '=', line['employee_id'][0])])
                for each_em in get_custody_obj:
                    total_amount_curr += each_em.amount_currency
                line.update({
                    'amount_currency': total_amount_curr
                })
        return res

    @api.multi
    def _get_default_payment_method(self):
        payment_method = self.env['ir.values'].get_default('account.config.settings',
                                                           'payment_method_id',
                                                           company_id=self.env.user.company_id.id)

        if payment_method:
            return payment_method

    @api.multi
    def _get_default_journal(self):
        journal_id = self.env['ir.values'].get_default('account.config.settings',
                                                       'journal_id',
                                                       company_id=self.env.user.company_id.id)

        if journal_id:
            return journal_id

    @api.model
    def _default_currency(self):
        journal = self._get_default_journal()
        journal_obj = self.env['account.journal']
        if journal:
            journal = journal_obj.search([('id', '=', journal)])
            return journal.currency_id or journal.company_id.currency_id
        else:
            return self.env.user.company_id.currency_id.id

    @api.multi
    def _get_amount_currency(self):
        for each_rec in self:
            each_rec.amount_currency = each_rec.open_balance / each_rec.currency_id.rate

    @api.depends('employee_id')
    @api.one
    def _get_employee_custody_ids(self):
        employee_custody_objs = self.search([('employee_id', '=', self.employee_id.id)])
        employee_custody_item_obj = self.env['employee.custody.item']

        for custody in employee_custody_objs:
            custody_item = employee_custody_item_obj.search([('employee_custody_id', '=', custody.id)])
            if not custody_item:
                employee_custody_item_obj.create({'employee_custody_id': custody.id})

        employee_custody_item_objs = employee_custody_item_obj.search(
            [('employee_id', '=', self.employee_id.id), ('employee_custody_id', '!=', self.id)])

        self.employee_custody_item_ids = employee_custody_item_objs.ids

    name = fields.Char(string='Name', readonly=True, )
    loan_id = fields.Many2one('custody.category', 'Custody Category', required=True, readonly=True,
                              states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, readonly=True,
                                  states={'draft': [('readonly', False)]})
    employee_code = fields.Char(string='Employee Code', related='employee_id.employee_code', store=True)

    custody_date = fields.Date('Date', default=fields.Date.context_today, readonly=True,
                               states={'draft': [('readonly', False)]})
    custody_close_date = fields.Date(string='Closing Date')

    open_balance = fields.Monetary(string='Amount', readonly=True, states={'draft': [('readonly', False)]})
    close_balance = fields.Monetary(string='Remaining Amount',
                                    store=True, readonly=True, compute='_calc_close_balance')

    total_transactions = fields.Monetary(string='Total Transactions',
                                         store=True, readonly=True, compute='_calc_total_transactions')
    reconciled_amount = fields.Monetary(string='Reconciled Amount', readonly=True)
    line_ids = fields.One2many('employee.product.expense', 'employee_custody_id', string='Transactions', readonly=True,
                               states={'draft': [('readonly', False)], 'receiving_custody': [('readonly', False)]})
    state = fields.Selection([('draft', 'New'),
                              ('open', 'Open'),  # used by cash statements
                              ('receiving_custody', 'Receiving Custody'),  # used by cash statements
                              ('pay', 'Payment'),  # used by cash statements
                              ('done', 'Closed'),
                              ('cancel', 'Cancelled')],
                             'Status', required=True, readonly="1", default='draft')
    journal_id = fields.Many2one('account.journal', 'Journal', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]}, default=_get_default_journal)
    move_line_ids = fields.One2many('account.move.line', 'custody_id',
                                    'Entry lines', readonly=True)
    move_id = fields.Many2one('account.move', 'Journal Entry', readonly=True, states={'draft': [('readonly', False)]})

    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company']._company_default_get('account.invoice'))

    description = fields.Text('Description')
    payment_method_id = fields.Many2one('account.journal', string='Payment Method', readonly=True,
                                        states={'draft': [('readonly', False)]}, required=True,
                                        domain=[('type', 'in', ('bank', 'cash'))], default=_get_default_payment_method)

    currency_id = fields.Many2one('res.currency', string='Currency',
                                  required=True, readonly=True, states={'draft': [('readonly', False)]},
                                  default=_default_currency, track_visibility='always')
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    journal_entries_count = fields.Integer('Journal Entries Count', compute='_get_entries_count')
    invoices_count = fields.Integer('Invoices Count', compute='_get_invoices_count')

    employee_custody_item_ids = fields.One2many(compute='_get_employee_custody_ids',
                                                comodel_name='employee.custody.item',
                                                relation='employee_custody_id', string='Employee Custodies')
    reconcile_from_all = fields.Boolean(string='Reconcile From All?', readonly=True,
                                        states={'receiving_custody': [('readonly', False)]}, default=False)
    arrears = fields.Boolean(string='arrears?', help='Indicates if there are arrears on the current custody')
    arabic_amount = fields.Char(compute='_arabic_date')
    amount_currency = fields.Float(string='Amounted Currency', compute="_get_amount_currency")

    @api.one
    def _arabic_date(self):
        self.arabic_amount = num2words(float(self.open_balance), lang='en')

    @api.depends('employee_id')
    @api.one
    def _get_employee_code(self):
        emp_obj = self.env['hr.employee'].browse(self.employee_id.id)
        self.employee_code = emp_obj.employee_code

    @api.depends('move_id', 'line_ids')
    @api.one
    def _get_entries_count(self):
        self.journal_entries_count = self.env['account.move'].search_count([('custody_id', '=', self.id)])

    @api.depends('line_ids')
    @api.one
    def _get_invoices_count(self):
        self.invoices_count = self.env['account.invoice'].search_count([('custody_id', '=', self.id)])

    @api.model
    def create(self, vals):
        if vals:
            vals.update({'name': self.env['ir.sequence'].next_by_code('custody.form.sequence')})
        return super(isky_employee_custody, self).create(vals)

    @api.one
    @api.depends('reconciled_amount', 'open_balance', 'total_transactions', 'state', 'line_ids')
    def _calc_close_balance(self):
        if self.state == 'done':
            self.close_balance = 0
        else:
            self.close_balance = self.open_balance - abs(self.total_transactions) - self.reconciled_amount
        return True

    @api.one
    @api.depends('line_ids.price_subtotal', 'currency_id', 'company_id')
    def _calc_total_transactions(self):
        self.total_transactions = sum(line.price_subtotal for line in self.line_ids)

    @api.multi
    def button_validate(self):
        flag = self.env['res.users'].has_group('isky_employee_custody.isky_custody_group')
        if flag:
            self.ensure_one()
            if self.open_balance == 0.0:
                raise UserError('Please Add Amount First!')
            if self.open_balance < 0.0:
                self.with_context(button_type='receive').button_journal_entry()
                self.write({'arrears': True, 'state': 'pay'})
            else:
                self.state = 'open'
        else:
            raise UserError('Only Custody Manager Can Validate!')

    @api.multi
    def paid_custody(self):
        self.write({'state': 'done', 'custody_close_date': fields.Date.today()})

    @api.multi
    def cancel_custody(self, reason):
        self.write({'state': 'cancel'})
        if self.employee_id.user_id:
            body = (_(
                "Your Expense %s has been refused.<br/><ul class=o_timeline_tracking_value_list><li>Reason<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (
                        self.name, reason))
            self.message_post(body=body, partner_ids=[self.employee_id.user_id.partner_id.id])

    @api.multi
    def unlink(self):
        if any(custody.state not in ['draft', 'cancel'] for custody in self):
            raise UserError(_('You can only delete draft or cancelled custody!'))
        return super(isky_employee_custody, self).unlink()

    @api.multi
    def _compute_expense_totals(self, company_currency, account_move_lines):
        self.ensure_one()
        total = 0.0
        total_currency = 0.0
        for line in account_move_lines:
            line['currency_id'] = False
            line['amount_currency'] = False
            if self.currency_id != company_currency:
                line['currency_id'] = self.currency_id.id
                line['amount_currency'] = line['price']
                line['price'] = self.currency_id.with_context(
                    date=self.custody_date or fields.Date.context_today(self)).compute(line['price'], company_currency)
            total -= line['price']
            total_currency -= line['amount_currency'] or line['price']
        return total, total_currency, account_move_lines

    def _prepare_move_line(self, line):
        partner_id = self.employee_id.address_home_id.commercial_partner_id.id
        return {
            'date_maturity': line['date'],
            'partner_id': partner_id,
            'name': line['name'][:64],
            'date': line['date'],
            'debit': line['price'] > 0 and line['price'],
            'credit': line['price'] < 0 and -line['price'],
            'account_id': line['account_id'],
            'analytic_line_ids': line.get('analytic_line_ids', []),
            'amount_currency': line['price'] > 0 and abs(line.get('amount_currency')) or -abs(
                line.get('amount_currency')),
            'currency_id': line.get('currency_id'),
            'ref': line.get('ref'),
            'quantity': line.get('quantity', 1.00),
            'product_id': line.get('product_id'),
            'product_uom_id': line.get('uom_id'),
            'custody_id': self.id,
            'analytic_account_id': line.get('account_analytic_id'),
            'type': line.get('line_type')
        }

    @api.constrains('custody_close_date')
    def constrain_custody_close_date(self):
        if self.custody_close_date:
            if datetime.datetime.strptime(self.custody_close_date, "%Y-%m-%d").date() > date.today():
                raise ValidationError('Closing Date can not be greater than today!')

    @api.onchange('custody_close_date')
    def _onchange_date(self):
        if self.custody_close_date:
            if datetime.datetime.strptime(self.custody_close_date, "%Y-%m-%d").date() > date.today():
                raise ValidationError('Closing Date can not be greater than today!')
            for line in self.move_line_ids:
                if line.date > self.custody_close_date:
                    raise UserError('The closing date should be greater than or equal to opening')

    def _add_custody_journal(self, custody, amount, type=None, line=None, src_account=None, dest_account=None,
                             date=None):

        company_currency = custody.company_id.currency_id
        diff_currency_p = custody.currency_id != company_currency
        move_lines = []

        if type == 'direct_expense':
            # create journal entry for each line
            move = self.env['account.move'].create({
                'journal_id': custody.journal_id.id,
                'company_id': self.env.user.company_id.id,
                'date': line.date,
            })

            # create journal items of line
            move_line = {
                'type': 'src',
                'name': custody.name.split('\n')[0][:64],
                'price_unit': line.price_unit,
                'quantity': line.quantity,
                'price': amount,
                'account_id': line.account_id.id,
                'product_id': line.product_id.id,
                'uom_id': line.uom_id.id,
                'account_analytic_id': line.account_analytic_id.id,
                'date': line.date,
                'line_type': type
            }

            if line['account_analytic_id']:
                move_line['analytic_line_ids'] = [(0, 0, line._get_analytic_line())]
            move_lines.append(move_line)
            # create one more move line, a counterline for the total on payable account
            total, total_currency, move_lines = custody._compute_expense_totals(company_currency,
                                                                                move_lines)
            move_lines.append({
                'type': 'dest',
                'name': custody.name,
                'price': total,
                'account_id': custody.journal_id.default_credit_account_id.id,
                'date': line.date,
                'amount_currency': diff_currency_p and total_currency or False,
                'currency_id': diff_currency_p and custody.currency_id.id or False,
                'ref': custody.employee_id.address_home_id.ref or False,
                'line_type': type
            })
        elif type in ['payment', 'payback']:
            # create journal entry for each line
            print "create entry"
            move = self.env['account.move'].create({
                'journal_id': custody.journal_id.id,
                'company_id': self.env.user.company_id.id,
                'date': line.date,
            })

            if type == 'payment':
                account_id = line.partner_id.property_account_payable_id.id
            elif type == 'payback':
                account_id = custody.payment_method_id.default_credit_account_id.id
            # create journal items of line
            move_line = {
                'type': 'src',
                'name': custody.name.split('\n')[0][:64],
                'price': amount,
                'account_id': account_id,
                'date': line.date,
                'currency_id': diff_currency_p and custody.currency_id.id or False,
                'ref': custody.name or False,
                'account_analytic_id': line.account_analytic_id.id,
                'line_type': type
            }
            move_lines.append(move_line)
            # create one more move line, a counterline for the total on payable account
            total, total_currency, move_lines = custody._compute_expense_totals(company_currency,
                                                                                move_lines)
            move_lines.append({
                'type': 'dest',
                'name': custody.name,
                'price': total,
                'account_id': custody.journal_id.default_debit_account_id.id,
                'date': line.date,
                'amount_currency': diff_currency_p and total_currency or False,
                'currency_id': diff_currency_p and custody.currency_id.id or False,
                'ref': custody.employee_id.address_home_id.ref or False,
                'line_type': type
            })
        else:
            # create journal entry for the payment
            move = self.env['account.move'].create({
                'journal_id': custody.journal_id.id,
                'company_id': self.env.user.company_id.id,
                'date': fields.Date.today(),
            })

            move_lines.append({
                'type': 'src',
                'name': custody.name,
                'price': amount,
                'account_id': src_account,
                'date': date or fields.Date.today(),
                'currency_id': diff_currency_p and custody.currency_id.id or False,
                'ref': custody.payment_method_id.code or False,
                'line_type': type
            })
            total, total_currency, move_lines = custody._compute_expense_totals(company_currency, move_lines)

            move_lines.append({
                'type': 'dest',
                'name': custody.name,
                'price': -amount,
                'account_id': dest_account,
                'date': date or fields.Date.today(),
                'amount_currency': diff_currency_p and total_currency or False,
                'currency_id': diff_currency_p and custody.currency_id.id or False,
                'ref': custody.name or False,
                'line_type': type
            })

        # convert eml into an osv-valid format
        lines = map(lambda x: (0, 0, custody._prepare_move_line(x)), move_lines)
        move.write({'line_ids': lines, 'custody_id': custody.id})
        move.post()
        return True

    def _reconcile_custody(self, custody, amount, line):
        payment_amount = amount
        for custody_item in custody.employee_custody_item_ids:
            custody_old = custody_item.employee_custody_id
            if ((custody_old.state == 'receiving_custody' and not custody_old.line_ids)
                or custody_old.state == 'pay') \
                    and custody_old.close_balance > 0 and payment_amount > 0:
                if payment_amount > custody_old.close_balance:
                    self._add_custody_journal(custody_old, custody_old.close_balance, line.type, line)
                    payment_amount -= custody_old.close_balance
                    custody.reconciled_amount -= custody_old.close_balance
                    custody_old.reconciled_amount += custody_old.close_balance
                    custody_old.write({'state': 'pay'})
                elif payment_amount == custody_old.close_balance:
                    self._add_custody_journal(custody_old, custody_old.close_balance, line.type, line)
                    payment_amount -= custody_old.close_balance
                    custody.reconciled_amount -= custody_old.close_balance
                    custody_old.reconciled_amount += custody_old.close_balance
                    custody_old.write({'state': 'pay'})
                else:  # payment_amount < custody_old.close_balance
                    self._add_custody_journal(custody_old, payment_amount, line.type or False, line)
                    custody.reconciled_amount -= payment_amount
                    custody_old.reconciled_amount += payment_amount
                    payment_amount = 0
                    custody_old.write({'state': 'pay'})
        return True

    def _calc_prev_amounts_total(self, custody):
        total_amount = 0
        for custody_item in custody.employee_custody_item_ids:
            custody_old = custody_item.employee_custody_id
            if ((custody_old.state == 'receiving_custody' and not custody_old.line_ids)
                or custody_old.state == 'pay') \
                    and custody_old.close_balance > 0:
                total_amount += custody_old.close_balance
        return total_amount

    @api.multi
    def button_journal_entry(self):
        for custody in self:
            if self.env.context.get('button_type') == 'entry' and not custody.line_ids:
                raise UserError('Please Add Transactions First!')
            if not custody.employee_id.address_home_id:
                raise UserError(_("No Home Address found for the employee %s, please configure one.") % (
                    custody.employee_id.name))
            if not custody.payment_method_id.default_credit_account_id or not custody.payment_method_id.default_debit_account_id:
                raise UserError(_("Please Configure Payment Method's Debit and Credit Accounts!"))
            if not custody.journal_id.default_credit_account_id.id or not custody.journal_id.default_debit_account_id.id:
                raise UserError(_("Please Configure Journal's Debit and Credit Accounts in Journal!"))

            custody_account = custody.journal_id.default_credit_account_id.id

            company_currency = custody.company_id.currency_id
            diff_currency_p = custody.currency_id != company_currency
            remaining_amount = custody.open_balance
            if self.env.context.get('button_type') == 'entry':
                for line in custody.line_ids:
                    if line.is_validated:
                        remaining_amount -= line.price_subtotal
                    else:
                        if line.product_id:
                            account = line.product_id.product_tmpl_id._get_product_accounts()['expense']
                            if not account:
                                raise UserError(_(
                                    "No Expense account found for the product %s (or for it's category), please configure one.") % (
                                                    line.product_id.name))
                        else:
                            account = self.env['ir.property'].with_context(force_company=line.company_id.id).get(
                                'property_account_expense_categ_id', 'product.category')
                            if not account and line.type == 'direct_expenses':
                                raise UserError(_(
                                    'Please configure Default Expense account for Product expense: `property_account_expense_categ_id`.'))
                        if line.price_subtotal > remaining_amount and custody.reconcile_from_all:
                            if remaining_amount < 0:
                                amount = line.price_subtotal
                            else:
                                amount = line.price_subtotal - remaining_amount

                            if remaining_amount > 0:
                                self._add_custody_journal(custody, remaining_amount, line.type, line)
                                remaining_amount = 0
                            self._reconcile_custody(custody, amount, line)
                        else:
                            self._add_custody_journal(custody, line.price_subtotal, line.type, line)
                            remaining_amount -= line.price_subtotal

                        line.is_validated = True

                # check if there is extra expense
                if custody.close_balance < 0:
                    custody.write({'arrears': True, 'state': 'pay'})
                prev_amounts = self._calc_prev_amounts_total(custody)

                if custody.close_balance == 0:
                    if not (custody.reconcile_from_all and prev_amounts > 0):
                        custody.write({'state': 'pay'})
            else:
                move_lines = []

                # create the move that will contain the accounting entries
                move = self.env['account.move'].create({
                    'journal_id': custody.journal_id.id,
                    'company_id': self.env.user.company_id.id,
                    'date': fields.Date.today(),
                })

                if self.env.context.get('button_type') == 'receive':
                    move_lines.append({
                        'type': 'src',
                        'name': custody.name,
                        'price': custody.open_balance,
                        'account_id': custody.journal_id.default_debit_account_id.id,
                        'date': fields.Date.today(),
                        'currency_id': diff_currency_p and custody.currency_id.id or False,
                        'ref': custody.name or False
                    })
                    total, total_currency, move_lines = custody._compute_expense_totals(company_currency, move_lines)

                    move_lines.append({
                        'type': 'dest',
                        'name': custody.name,
                        'price': total,
                        'account_id': custody.payment_method_id.default_credit_account_id.id,
                        'date': fields.Date.today(),
                        'amount_currency': diff_currency_p and total_currency or False,
                        'currency_id': diff_currency_p and custody.currency_id.id or False,
                        'ref': custody.payment_method_id.code or False
                    })
                    custody.write({'move_id': move.id, 'state': 'receiving_custody'})
                if self.env.context.get('button_type') == 'close':
                    for line in self.move_line_ids:
                        if self.custody_close_date:
                            if line.date > self.custody_close_date:
                                raise UserError('The closing date should be greater than or equale to opening')
                    if not self.custody_close_date:
                        raise UserError("Please set the closing date")
                    if custody.close_balance == 0.0:
                        custody.write({'state': 'done'})
                        move.unlink()
                        return
                    else:
                        move_lines.append({
                            'type': 'src',
                            'name': custody.name,
                            'price': custody.close_balance,
                            'account_id': custody.payment_method_id.default_credit_account_id.id,
                            # 'date': fields.Date.today(),
                            'date': custody.custody_close_date,
                            'currency_id': diff_currency_p and custody.currency_id.id or False,
                            'ref': custody.payment_method_id.code or False
                        })
                        total, total_currency, move_lines = custody._compute_expense_totals(company_currency,
                                                                                            move_lines)
                        move_lines.append({
                            'type': 'dest',
                            'name': custody.name,
                            'price': -custody.close_balance,
                            'account_id': custody.journal_id.default_debit_account_id.id,
                            # 'date': fields.Date.today(),
                            'date': custody.custody_close_date,
                            'amount_currency': diff_currency_p and total_currency or False,
                            'currency_id': diff_currency_p and custody.currency_id.id or False,
                            'ref': custody.name or False
                        })
                        custody.write({'move_id': move.id, 'state': 'done'})

                # convert eml into an osv-valid format
                lines = map(lambda x: (0, 0, custody._prepare_move_line(x)), move_lines)
                move.write({'line_ids': lines, 'custody_id': custody.id})
                move.post()
        return True

    @api.multi
    def reconcile_arrears(self):
        self.ensure_one()
        extra_amount = abs(self.close_balance)
        self._add_custody_journal(self, extra_amount, False, False,
                                  self.journal_id.default_debit_account_id.id,
                                  self.payment_method_id.default_credit_account_id.id)
        self.open_balance += extra_amount
        self.write({'arrears': False})


class isky_account_move_inherit(models.Model):
    _inherit = 'account.move'
    custody_id = fields.Many2one('employee.custody', 'Employee Custody')


class isky_account_move_line_inherit(models.Model):
    _inherit = 'account.move.line'
    custody_id = fields.Many2one('employee.custody', 'Employee Custody')
    type = fields.Selection([('payment', 'Payment'),
                             ('direct_expense', 'Direct Expense'), ('payback', 'Payback')],
                            'Type')
