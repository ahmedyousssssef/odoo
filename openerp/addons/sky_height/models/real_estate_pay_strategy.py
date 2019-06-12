# -*- coding: utf-8 -*-
from openerp import models, fields, api, _, exceptions
import datetime
from openerp.exceptions import ValidationError

TYPE_SELECTION = [('sale', _('Sale')),
                  ('sale_refund', _('Sale Refund')),
                  ('purchase', _('Purchase')),
                  ('purchase_refund', _('Purchase Refund')),
                  ('cash', _('Cash')),
                  ('bank', _('Bank and Checks')),
                  ('general', _('General')),
                  ('situation', _('Opening/Closing Situation'))]


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    @api.model
    def create(self, vals):
        obj = super(AccountPaymentTermLine, self).create(vals)
        return obj

    journal_id = fields.Many2one('account.journal', _('Journal'))
    payment_description = fields.Char(string="Description")
    deposit = fields.Boolean('Deposit')
    add_extension = fields.Boolean('Extension')
    value_amount = fields.Float(string='Value', digits=(20, 15), help="For percent enter a ratio between 0-100.")


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    payment_detail_ids = fields.One2many('rs.payment_strategy_details', 'payment_strategy_id', ondelete='cascade',
                                         string="Details", copy=True)
    total_percentage = fields.Float(compute="_total_percentage", string="Total Percentage", store=True)
    virtual = fields.Boolean(_("Virtual"))
    computed = fields.Boolean(_("Computed"))
    payment_term_discount = fields.Float(string='Discount', digits=(16,6))
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved')], string='State',copy=False)

    @api.constrains('payment_term_discount')
    def check_payment_term_discount(self):
        for rec in self:
            if rec.payment_term_discount > 100.0 or rec.payment_term_discount < 0.0:
                raise ValidationError(_('Discount should less than 100.0 and greater than 0.0'))

    @api.constrains('line_ids')
    @api.one
    def _check_lines(self):
        return True

    @api.multi
    def approved_payment(self):
        for rec in self:
            rec.state = 'approved'

    @api.multi
    def copy_payment(self):
        for rec in self:
            copied_obj = self.copy(default={
                'virtual': True,
                'name': 'Copy' + ' ' + rec.name,
            })
            view_id = self.env.ref('account.view_payment_term_form')
            return {
                'type': 'ir.actions.act_window',
                'name': _('Payment Term'),
                'res_model': 'account.payment.term',
                'res_id': copied_obj.id,
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id.id,
                'target': 'current',
                'nodestroy': True,
            }

    """
    there are some cases:
        1- biannual >>  6 months incremental
        2- quarterly >> 3 months   ,,
        3- Annual >> 12 month incremental
        4- Monthly >> month incremental
    # in the above four cases the day=0.
        5- BY Month >> amount of months incremental
    """

    ## TOTAL NUMBER OF INSTALLMENTS = TOTAL NUMBER OF COMPUTATIONS
    ## THE ALGORITHM GOES LIKE THIS >>>
    """
        1- retrieve all the detail object.
        2- for every object, get the case (x), percentage(y), number of installments(z).
        3- (z) number of computations will be created.
        4- for any computation, the percentage(of computation) will be the amount(y/z).
        5- the computation will be chosen as percent. [[CONSTANT]]
        6- amount will be the new percent.
        7- the days will be incremental by time. 
    """

    @api.multi
    def cr_computation(self):
        for rec in self:
            # Prevent computation if The total Percentage of payment Strategy Not Equal 100.00
            if rec.total_percentage != 100.0:
                raise exceptions.ValidationError(
                    "The total Percentage of payment Strategy Not Equal 100.00 : %s" % rec.total_percentage)

            # check on line_ids field
            # then Delete old payment term lines
            rec.line_ids.unlink() if rec.line_ids else None
            # step1: retrieve all the details objects, initial version
            # step2: retrieve all the information needed from the objects.
            details_list = []
            for payment in self.payment_detail_ids:
                tmp = {}
                tmp['id'] = payment.id
                tmp['percentage'] = (payment.inst_percentage / 100.0) / payment.number_of_inst
                tmp['no_inst'] = payment.number_of_inst
                tmp['name'] = payment.name

                # calculate shifting days
                if payment.shift_by == 2:  # by months
                    tmp['shifting_days'] = payment.shifting_months * 30
                else:
                    tmp['shifting_days'] = payment.shifting_days

                if payment.inst_range == 1:
                    tmp['increment'] = payment.by_days
                    tmp['days'] = 0
                    tmp['journal_id'] = payment.journal_id.id
                    tmp['payment_description'] = payment.name
                    tmp['deposit'] = payment.deposit
                    tmp['add_extension'] = payment.add_extension
                else:
                    tmp['journal_id'] = payment.journal_id.id
                    tmp['payment_description'] = payment.name
                    tmp['deposit'] = payment.deposit
                    tmp['add_extension'] = payment.add_extension
                    tmp['days'] = 0
                    selection = payment.by_period
                    if selection == 1:
                        tmp['increment'] = 30
                    elif selection == 2:
                        tmp['increment'] = 90
                    elif selection == 3:
                        tmp['increment'] = 180
                    elif selection == 4:
                        tmp['increment'] = 360
                    elif selection == 5:
                        tmp['increment'] = 0
                details_list.append(tmp)
            computations_list = []

            f_days_count = 0  # days no. of the first payment term line resulted from last payment strategy
            for detail_obj in details_list:
                lines_count = len(range(0, detail_obj['no_inst']))
                l_index = 1
                for installment in range(0, detail_obj['no_inst']):
                    tmp = {}
                    tmp['payment_id'] = rec.id
                    tmp['value'] = 'percent'
                    tmp['value_amount'] = detail_obj['percentage']

                    if detail_obj['shifting_days']:
                        tmp['days'] = detail_obj['increment'] * (installment + 1) + detail_obj['shifting_days']

                        if detail_obj['shifting_days'] < 0 and l_index == 1 and tmp['days'] < f_days_count:
                            max_allowed_days = (detail_obj['increment'] * (installment + 1)) - f_days_count
                            if max_allowed_days <= 0:
                                raise ValidationError(
                                    _('Number of shifting days/months in %s should be greater than or equal 0') % (
                                    detail_obj['name'],))
                            else:
                                max_allowed_months = max_allowed_days / 30
                                raise ValidationError(_(
                                    'Number of shifting days/months %s should be greater than or equal (-%s days) or (-%s months)') % (
                                                      detail_obj['name'], max_allowed_days, max_allowed_months))
                    else:
                        tmp['days'] = detail_obj['increment'] * (installment + 1)

                    # set f_days_count on the first iteration
                    if l_index == 1:
                        f_days_count = tmp['days']

                    l_index += 1

                    tmp['journal_id'] = detail_obj['journal_id']
                    tmp['payment_description'] = detail_obj['payment_description']
                    tmp['deposit'] = detail_obj['deposit']
                    tmp['add_extension'] = detail_obj['add_extension']
                    computations_list.append(tmp)
            for computation in computations_list:
                obj = self.env['account.payment.term.line'].sudo().create(computation)
            if rec.total_percentage == 100.0:
                rec.sudo().write(({'computed': True}))

    @api.multi
    @api.depends('payment_detail_ids', 'payment_detail_ids.inst_percentage')
    def _total_percentage(self):
        for rec in self:
            inst_percents = self.env['rs.payment_strategy_details'].search([('payment_strategy_id', '=', rec.id),
                                                                            ('add_extension', '=', False)])
            total = 0.0
            for installment in inst_percents:
                total += installment.inst_percentage
            rec.total_percentage = total


class RsPaymentStrategyDetails(models.Model):
    _name = 'rs.payment_strategy_details'

    name = fields.Char(ondelete='cascade', string="Name")
    payment_strategy_id = fields.Many2one('account.payment.term', ondelete='cascade', string="Payment Strategy")
    inst_percentage = fields.Float(string="Installment Percentage")
    number_of_inst = fields.Integer(string="Number of Installments", default=1)
    # simple calculator
    calculate_by = fields.Selection([('percentage', _('Percentage')),
                                     ('value', _('Value'))], 'Calculate By',
                                    default='percentage')

    unit_price = fields.Float(string="Unit Price")
    amount = fields.Float(string="Amount")
    inst_value = fields.Float(string="Installment Value")
    calc_no_inst = fields.Integer(string="Number of Installments")
    # installment range
    inst_range = fields.Selection([(1, _('By Days')),
                                   (2, _('By Period'))], 'Installment Range', default=2,
                                  required=True)
    by_days = fields.Integer(string="By Days")
    by_period = fields.Selection([(5, _('Once')),
                                  (1, _('Monthly')),
                                  (2, _('Quarterly')),
                                  (3, _('Semiannual')),
                                  (4, _('Annual'))])
    date = fields.Date(string="Date")
    # date of the first installment
    date_select = fields.Selection([(1, _("Fixed Date")),
                                    (2, _("By Contract Date"))], 'Date', default=2, required=False)
    contract_date = fields.Date(string="Contract Date", required=False)
    first_inst_date = fields.Date(string="First Date Installment")
    payment_type = fields.Selection([('cash', _('Cash')), ('bank', _('Bank'))], _('Payment Type'))
    journal_id = fields.Many2one('account.journal', _('Journal'))
    deposit = fields.Boolean('Deposit')
    add_extension = fields.Boolean('Maintenance')

    shift_by = fields.Selection([(1, _('Days')),
                                 (2, _('Months'))], string='Shift by', default=1)
    shifting_days = fields.Integer(string='Shift Days')
    shifting_months = fields.Integer(string='Shift Months')

    # @api.multi
    # @api.constrains('shifting_days')
    # def check_shifting_days(self):
    #     for record in self:
    #         if record.shifting_days and record.shifting_days < 1:
    #             raise ValidationError('Please insert positive value in shift days')

    @api.multi
    @api.onchange('unit_price', 'inst_percentage', 'number_of_inst', 'calculate_by', 'amount', 'calc_no_inst')
    def calc_total_price(self):
        for rec in self:
            if rec.calculate_by == 'percentage':
                amount = (rec.inst_percentage / 100.0) * rec.unit_price
                rec.amount = amount
                if rec.number_of_inst != 0:
                    rec.inst_value = amount / rec.number_of_inst
                rec.calc_no_inst = rec.number_of_inst
            if rec.calculate_by == 'value':
                if rec.unit_price != 0:
                    rec.inst_percentage = (rec.amount / rec.unit_price) * 100.0
                rec.number_of_inst = rec.calc_no_inst
                if rec.calc_no_inst != 0:
                    rec.inst_value = rec.amount / rec.calc_no_inst


class PaymentBank(models.Model):
    _name = "payment.bank"

    name = fields.Char(_('Bank Name'), required=True)
    bank_account_id = fields.Many2one('account.account', _('Account'), required=False)


class PaymentBankCustomer(models.Model):
    _name = "payment.bank.cus"

    name = fields.Char(_('Bank Name'), required=True)


class PaymentStrg(models.Model):
    _name = 'payment.strg'
    _order = "id asc"

    @api.multi
    def get_group_of_logged_user(self):
        for obj in self:
            user = self.env['res.users'].browse(obj.env.uid)
            obj.accountant_status = True if user.has_group('account.group_account_manager') or user.has_group(
                'account.group_account_user') else False

    @api.multi
    def _compute_days_diff(self):
        days_diff = 0
        for rec in self:
            if rec.payment_date:
                d1 = datetime.date.today()
                d2 = rec.payment_date
                d2 = datetime.datetime.strptime(d2, "%Y-%m-%d").date()
                days_diff = (d2 - d1).days
            rec.days_diff = days_diff

    name = fields.Char(string='Name')
    accountant_status = fields.Boolean('Is accountant', compute='get_group_of_logged_user', default=True)
    reserve_id = fields.Many2one('rs.reservation', _('Reservation'), ondelete="cascade")
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    payment_code = fields.Char(_('Code'))
    partner_id = fields.Many2one('res.partner', string='Customer', related='reserve_id.customer_id')
    customer_id = fields.Many2one('res.partner', string='Customer', related='reserve_id.customer_id', store=True)
    project_id = fields.Many2one('project.project', string='Project', related='reserve_id.project_id')
    property_ids = fields.Many2many('product.product', string='Properties')
    payment_date = fields.Date(_('Date'))
    amount = fields.Float(_('Amount'), digits=(16, 6))
    penalty_fees = fields.Float(_('Penalty Fees'))
    deduction_amount = fields.Float(_('Deduction Amount'))
    penalty_date = fields.Date(_('Deduction Payment Date'))
    penalty_journal_id = fields.Many2one('account.journal', _('Deduction Journal'))
    apply_penalty = fields.Boolean(string='Apply Penalty')
    old_value = fields.Float(_('Old Value'), digits=(16, 6))
    penalty_journal_entry_id = fields.Many2one('account.move', _('Penalty Fees Journal Entry'))
    description = fields.Char(_('Description'))
    move_check = fields.Boolean(string='Paid')
    journal_id = fields.Many2one('account.journal', _('Journal'))
    under_collected_journal_entry_id = fields.Many2one('account.move', _('Under Collected Journal Entry'))
    collected_journal_entry_id = fields.Many2one('account.move', _('Collected Journal Entry'))
    type = fields.Selection(selection=TYPE_SELECTION, related='journal_id.type', store=True, string='Payment Type')
    cus_bank = fields.Many2one('payment.bank.cus', _("Customer Bank Name"))
    bank_name = fields.Many2one('payment.bank', _("Bank Name"))
    cheque = fields.Char(_("Cheque Number"))
    is_bank_transfer = fields.Boolean(string='Is Bank Transfer', related='journal_id.show_checks')
    cheque_status = fields.Selection([('draft', _("Draft")),
                                      ('received', _("Received")),
                                      ('under_collection', _("Under Collection")),
                                      ('collection', _("Collection")),
                                      ('rejected', _("Rejected"))], _('Check Status'),
                                     default='draft')
    deposite = fields.Boolean(string='Deposit')
    maintainance_fees = fields.Float(string='Fees', digits=(16, 6))
    add_extension = fields.Boolean(string='Maintenance')
    use_unearned_revenu_account = fields.Boolean(string='Unearned Account')
    rejected = fields.Boolean(string='Rejected')
    days_diff = fields.Integer(compute='_compute_days_diff', string='Days Diff')
    cancelled = fields.Boolean(string='Cancelled')
    payment_id = fields.Many2one('account.payment', _("Payment"))
    move_id = fields.Many2one('account.move', _("Move"))
    maintaince_id = fields.Many2one('account.payment', _("Maintenance"))
    is_bank_transfer = fields.Boolean(string='Bank Transfer', related='journal_id.show_checks')
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Type', oldname="payment_method")
    rejection_action = fields.Selection([('transfer', _('Transfer To Cash')),
                                         ('reject', _('Reject'))], 'Rejection Action')
    rejection_cash_payment_id = fields.Many2one('account.payment', _("Payment"))

    _defaults = {
        'payment_code': lambda self, cr, uid, context: self.pool.get('ir.sequence').get(cr, uid,
                                                                                        'real.estate.payment.code.seq')
    }

    @api.multi
    @api.depends('description', 'payment_code')
    def name_get(self):
        result = []
        for val in self:
            if val.payment_code:
                name = str(val.payment_code)
                if val.description:
                    name += ' - ' + val.description
            result.append((val.id, name))
        return result

    @api.multi
    def under_collection_deposit(self):
        account_move_obj = self.env['account.move']
        for rec in self:
            under_collection_journal_id = self.env['ir.values'].get_default('sky.height.settings',
                                                                            'under_collection_journal_id')
            if not under_collection_journal_id:
                raise ValidationError(_("Please set under collection journal from skyheights configuration."))
            under_collection_journal_obj = self.env['account.journal'].browse(under_collection_journal_id)

            if not rec.journal_id.default_credit_account_id or not rec.journal_id.default_debit_account_id:
                raise ValidationError(
                    _('Please define default credit/debit accounts on the journal "%s".') % (rec.journal_id.name))

            if rec.deposite and rec.journal_id.type == 'bank':
                if rec.journal_id.show_checks:
                    # create deposite under collection move
                    debit_arr = {}
                    debit_arr['date'] = datetime.date.today()
                    debit_arr['date_maturity'] = rec.payment_date
                    debit_arr['journal_id'] = rec.journal_id.id
                    debit_arr['account_id'] = rec.journal_id.under_collected_account_id.id
                    debit_arr['partner_id'] = rec.partner_id.id
                    debit_arr['project_id'] = rec.project_id.id
                    debit_arr['name'] = rec.description
                    debit_arr['debit'] = rec.amount
                    debit_arr['credit'] = 0
                    debit_arr['amount_currency'] = 0

                    credit_arr = {}
                    credit_arr['date'] = datetime.date.today()
                    credit_arr['date_maturity'] = rec.payment_date
                    credit_arr['journal_id'] = rec.journal_id.id
                    credit_arr['account_id'] = rec.journal_id.default_credit_account_id.id
                    credit_arr['partner_id'] = rec.partner_id.id
                    credit_arr['name'] = rec.description
                    credit_arr['credit'] = rec.amount
                    credit_arr['debit'] = 0
                    credit_arr['amount_currency'] = 0

                    under_collection_deposite_entry = account_move_obj.create({
                        'date': rec.payment_date,
                        'journal_id': under_collection_journal_obj.id,
                        'line_ids': [(0, 0, debit_arr), (0, 0, credit_arr)]
                    })
                    under_collection_deposite_entry.post()
                    rec.write({'cheque_status': 'under_collection',
                               'under_collected_journal_entry_id': under_collection_deposite_entry.id})
                else:
                    rec.write({'cheque_status': 'collection'})

    @api.multi
    def create_deposite_entry(self):
        move_obj = self.env['account.move']
        for rec in self:
            #  generate deposite entry
            debit_arr = {}
            debit_arr['date'] = datetime.date.today()
            debit_arr['date_maturity'] = rec.payment_date
            debit_arr['journal_id'] = rec.journal_id.id
            debit_arr['account_id'] = rec.journal_id.default_credit_account_id.id
            debit_arr['partner_id'] = rec.partner_id.id
            debit_arr['project_id'] = rec.project_id.id
            debit_arr['name'] = '/'
            debit_arr['debit'] = rec.amount
            debit_arr['credit'] = 0
            debit_arr['amount_currency'] = 0
            debit_arr['currency_id'] = self.env.user.company_id.currency_id.id
            debit_arr['company_id'] = self.env.user.company_id.id

            credit_arr = {}
            credit_arr['date'] = datetime.date.today()
            credit_arr['date_maturity'] = rec.payment_date
            credit_arr['journal_id'] = rec.journal_id.id
            credit_arr['account_id'] = rec.partner_id.property_account_prereceivable.id
            credit_arr['partner_id'] = rec.partner_id.id
            credit_arr['name'] = 'customer payment'
            credit_arr['credit'] = rec.amount
            credit_arr['debit'] = 0
            credit_arr['amount_currency'] = 0
            credit_arr['currency_id'] = self.env.user.company_id.currency_id.id
            credit_arr['company_id'] = self.env.user.company_id.id

            move_id = move_obj.create({
                'date': rec.payment_date,
                'journal_id': rec.journal_id.id,
                'state': 'draft',
                'reserve_id': rec.reserve_id.id,
                'company_id': self.env.user.company_id.id,
                'line_ids': [(0, 0, debit_arr), (0, 0, credit_arr)]
            })
            move_id.post()
            rec.write({'move_check': True, 'move_id': move_id.id, 'partner_id': rec.partner_id.id,
                       'property_ids': rec.reserve_id.unit_ids.ids})
            user = self.env['res.users'].browse(self.env.uid)
            rec.reserve_id.client_accountant_id = user.id
            if not rec.journal_id.show_checks:
                rec.write({'cheque_status': 'collection'})
            else:
                rec.write({'cheque_status': 'received'})

    @api.multi
    def penalty_fees_check(self):
        for rec in self:
            if len(self) > 1:
                is_penalty = False
                is_penalty = True if rec.days_diff < 0 else None
                if is_penalty:
                    view_id = self.env.ref('sky_height.form_select_clerk_view').id
                    ctx = {
                        'default_payment_strg_ids': self.env.context.get('active_ids', []),
                        'default_apply_penalty': is_penalty
                    }
                    return {
                        'name': _("Collection Check"),
                        'view_mode': 'form',
                        'view_id': view_id,
                        'view_type': 'form',
                        'res_model': 'select.clerk',
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'context': ctx,
                    }
                else:
                    rec.apply_penalty = False
                    rec.collection_check()
            else:
                name = "Penalty Fess Approval"
                if rec.days_diff < 0:
                    if rec.days_diff < 0:
                        rec.penalty_fees = self.env['ir.values'].get_default('sky.height.settings',
                                                                             'penalty_percentage')
                        total_amount = rec.amount
                        for day in range(-1 * rec.days_diff):
                            total_amount = total_amount + ((rec.penalty_fees * total_amount) / 100)

                        rec.deduction_amount = total_amount - rec.amount
                        rec.apply_penalty = True
                    else:
                        name = "Collection Check"
                    view_id = self.env.ref('sky_height.view_penalty_fees_confirm').id
                    return {
                        'name': name,
                        'view_mode': 'form',
                        'view_id': view_id,
                        'view_type': 'form',
                        'res_id': rec.id,
                        'res_model': 'payment.strg',
                        'type': 'ir.actions.act_window',
                        'nodestroy': True,
                        'target': 'new',
                    }
                else:
                    rec.apply_penalty = False
                    rec.collection_check()

    @api.multi
    def apply(self):
        for rec in self:
            rec.collection_check()

    @api.multi
    def ignore(self):
        for rec in self:
            rec.apply_penalty = False if rec.days_diff < 0 else None
            rec.collection_check()

    @api.multi
    def collection_check(self):
        account_move_obj = self.env['account.move']
        account_move_line_obj = self.env['account.move.line']
        for rec in self:
            if not rec.collected_journal_entry_id:
                if rec.journal_id.type == 'bank':
                    if not rec.journal_id.collection_account_id:
                        raise ValidationError(_('Please Choose Collection Account'))

                    if not rec.journal_id.default_credit_account_id or not rec.journal_id.default_debit_account_id:
                        raise ValidationError(_('Please define default credit/debit accounts on the journal "%s".') % (
                            rec.journal_id.name))
                    if not rec.description:
                        raise exceptions.ValidationError(_('You Must Choose Description'))

                    collection_move_obj = account_move_obj.create({'date': datetime.date.today(),
                                                                   'journal_id': rec.journal_id.id})
                    if rec.maintainance_fees > 0.0:
                        maintaince_journal_id = self.env['ir.values'].get_default('sky.height.settings',
                                                                                  'maintaince_journal_id')
                        if not maintaince_journal_id:
                            raise ValidationError(_("Please set maintaince journal from configuration."))
                        maintaince_journal_obj = self.env['account.journal'].browse(maintaince_journal_id)
                        if maintaince_journal_obj and not maintaince_journal_obj.collection_account_id:
                            raise ValidationError(
                                _("Please set collection account in maintaince journal from configuration."))
                        # create debit line for maintaince
                        account_move_line_obj.with_context(check_move_validity=False).create({
                            'move_id': collection_move_obj.id,
                            'date': datetime.date.today(),
                            'date_maturity': rec.payment_date,
                            'journal_id': maintaince_journal_obj.id,
                            'account_id': maintaince_journal_obj.collection_account_id.id,
                            'partner_id': rec.partner_id.id,
                            'name': rec.description,
                            'debit': rec.maintainance_fees,
                            'credit': 0.0,
                            'amount_currency': 0.0})
                        # create debit line for payment
                        account_move_line_obj.with_context(check_move_validity=False).create({
                            'move_id': collection_move_obj.id,
                            'date': datetime.date.today(),
                            'date_maturity': rec.payment_date,
                            'journal_id': rec.journal_id.id,
                            'account_id': rec.journal_id.collection_account_id.id,
                            'partner_id': rec.partner_id.id,
                            'name': rec.description,
                            'debit': rec.amount - rec.maintainance_fees,
                            'credit': 0.0,
                            'amount_currency': 0.0})

                        # create credit line for maintaince
                        account_move_line_obj.with_context(check_move_validity=False).create({
                            'move_id': collection_move_obj.id,
                            'date': datetime.date.today(),
                            'date_maturity': rec.payment_date,
                            'journal_id': maintaince_journal_obj.id,
                            'account_id': maintaince_journal_obj.under_collected_account_id.id,
                            'partner_id': rec.partner_id.id,
                            'name': rec.description,
                            'credit': rec.maintainance_fees,
                            'debit': 0.0,
                            'amount_currency': 0.0})

                        # create credit line for payment
                        account_move_line_obj.with_context(check_move_validity=False).create({
                            'move_id': collection_move_obj.id,
                            'date': datetime.date.today(),
                            'date_maturity': rec.payment_date,
                            'journal_id': rec.journal_id.id,
                            'account_id': rec.journal_id.under_collected_account_id.id,
                            'partner_id': rec.partner_id.id,
                            'name': rec.description,
                            'credit': rec.amount - rec.maintainance_fees,
                            'debit': 0.0,
                            'amount_currency': 0.0})
                    else:
                        # create debit line for payment
                        account_move_line_obj.with_context(check_move_validity=False).create({
                            'move_id': collection_move_obj.id,
                            'date': datetime.date.today(),
                            'date_maturity': rec.payment_date,
                            'journal_id': rec.journal_id.id,
                            'account_id': rec.journal_id.collection_account_id.id,
                            'partner_id': rec.partner_id.id,
                            'name': rec.description,
                            'debit': rec.amount,
                            'credit': 0.0,
                            'amount_currency': 0.0})

                        # create credit line for payment
                        account_move_line_obj.with_context(check_move_validity=False).create({
                            'move_id': collection_move_obj.id,
                            'date': datetime.date.today(),
                            'date_maturity': rec.payment_date,
                            'journal_id': rec.journal_id.id,
                            'account_id': rec.journal_id.under_collected_account_id.id,
                            'partner_id': rec.partner_id.id,
                            'name': rec.description,
                            'credit': rec.amount,
                            'debit': 0.0,
                            'amount_currency': 0.0})

                    collection_move_obj.journal_id = rec.journal_id.id
                    collection_move_obj.post()
                    if rec.days_diff < 0 and rec.apply_penalty:
                        if not rec.penalty_journal_id:
                            raise ValidationError(_('Please Select Deduction Journal'))
                        if not rec.penalty_date:
                            raise ValidationError(_('Please Select Deduction Payment Date'))

                        # create penalty entry
                        penalty_move_obj = account_move_obj.create({'date': datetime.date.today(),
                                                                    'journal_id': rec.penalty_journal_id.id})
                        # create debit line for payment
                        penalty_revenue_account_id = self.env['ir.values'].get_default('sky.height.settings',
                                                                                       'penalty_revenue_account_id')
                        if not penalty_revenue_account_id:
                            raise ValidationError(_("Please configure penalty account from setting!!"))
                        penalty_revenue_account_obj = self.env['account.account'].browse(penalty_revenue_account_id)
                        account_move_line_obj.with_context(check_move_validity=False).create({
                            'move_id': penalty_move_obj.id,
                            'date': datetime.date.today(),
                            'date_maturity': rec.payment_date,
                            'journal_id': rec.penalty_journal_id.id,
                            'account_id': rec.penalty_journal_id.default_debit_account_id.id,
                            'partner_id': rec.partner_id.id,
                            'name': rec.description,
                            'debit': rec.deduction_amount,
                            'credit': 0.0,
                            'amount_currency': 0.0})

                        # create credit line for payment
                        account_move_line_obj.with_context(check_move_validity=False).create({
                            'move_id': penalty_move_obj.id,
                            'date': datetime.date.today(),
                            'date_maturity': rec.payment_date,
                            'journal_id': rec.penalty_journal_id.id,
                            'account_id': penalty_revenue_account_obj.id,
                            'partner_id': rec.partner_id.id,
                            'name': rec.description,
                            'credit': rec.deduction_amount,
                            'debit': 0.0,
                            'amount_currency': 0.0})

                        penalty_move_obj.journal_id = rec.penalty_journal_id.id
                        penalty_move_obj.post()
                        rec.write({'penalty_journal_entry_id': penalty_move_obj.id})

                    rec.write({'cheque_status': 'collection', 'collected_journal_entry_id': collection_move_obj.id})

    @api.multi
    def rejected_check(self):
        for rec in self:
            res = self.env['ir.model.data'].get_object_reference('sky_height', 'form_rejected_check_view')
            view_id = res and res[1] or False
            is_penalty = False
            deduction_amount = 0

            if rec.days_diff < 0:
                rec.penalty_fees = self.env['ir.values'].get_default('sky.height.settings',
                                                                     'penalty_percentage')
                total_amount = rec.amount
                for day in range(-1 * rec.days_diff):
                    total_amount = total_amount + ((rec.penalty_fees * total_amount) / 100)

                deduction_amount = total_amount - rec.amount
                is_penalty = True

            ctx = {
                'default_payment_strg_id': self.id,
                'default_apply_penalty': is_penalty,
                'default_deduction_amount': deduction_amount,
            }

            return {
                'name': _("Rejection"),
                'view_mode': 'form',
                'view_id': view_id,
                'res_model': 'rejected.check',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'domain': '[]',
                'context': ctx
            }

    @api.multi
    def unlink(self):
        for record in self:
            if record.under_collected_journal_entry_id:
                raise ValidationError(
                    _("Sorry .. You cannot delete this payment which in 'Under collection' or 'Collection'"))
        return super(PaymentStrg, self).unlink()
