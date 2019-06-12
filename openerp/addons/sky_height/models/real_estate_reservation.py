from openerp import models, fields, api, _
import datetime
import dateutil.parser
from openerp.exceptions import ValidationError
import time
from datetime import date
from dateutil.relativedelta import relativedelta
from openerp.tools import float_compare


class ReportReservationPayment(models.AbstractModel):
    _name = 'report.sky_height.reservation_payment_report_template'

    @api.multi
    def render_html(self, data):
        account_moves_lines = []
        account_moves = []
        self.model = self.env.context.get('active_model')

        if not data.get('ids'):
            data['ids'] = self.ids
        docs = self.env['rs.reservation'].browse(data['ids'])
        if docs:
            for doc in docs:
                for payment_strg in doc.payment_strg_ids:
                    for move_line in payment_strg.payment_id.move_line_ids:
                        account_moves_lines.append(move_line)
                        if move_line.move_id not in account_moves:
                            account_moves.append(move_line.move_id)

            updated_moves = []
            all_lines = []
            key_list = []
            if account_moves and len(account_moves) > 0:
                for x in range(0, len(account_moves)):
                    move_from_to = str(account_moves[x].line_ids[0].account_id.id) + ' ' + \
                                   str(account_moves[x].line_ids[1].account_id.id)
                    updated_moves.append({'move_from_to': move_from_to, 'move': account_moves[x]})
                    if move_from_to not in key_list:
                        key_list.append(move_from_to)

            filter_updated_moves = []
            for key in key_list:
                append_list = []
                filter_results = filter(lambda move: move['move_from_to'] == key, updated_moves)
                for result in filter_results:
                    append_list.append(result['move'])
                filter_updated_moves.append(append_list)

            debit_amount = 0
            credit_amount = 0
            partner_name = ''
            payment_method = ''
            debit_account = ''
            credit_account = ''
            updated_date = ''
            if filter_updated_moves and len(filter_updated_moves) > 0:
                for x in range(0, len(filter_updated_moves)):
                    if filter_updated_moves[x] and len(filter_updated_moves[x]) > 0:
                        for y in range(0, len(filter_updated_moves[x])):
                            for move_line in filter_updated_moves[x][y].line_ids:
                                partner_name = move_line.partner_id.name
                                payment_method = move_line.journal_id.name
                                updated_date = move_line.date
                                if move_line.debit != 0:
                                    debit_amount += move_line.debit
                                    debit_account = move_line.account_id.name

                                elif move_line.credit != 0:
                                    credit_amount += move_line.credit
                                    credit_account = move_line.account_id.name

                    all_lines.append({'partner_id': partner_name, 'date': updated_date,
                                      'journal_id': payment_method, 'account_id': debit_account,
                                      'debit': debit_amount, 'credit': 0})

                    all_lines.append({'partner_id': partner_name, 'date': updated_date,
                                      'journal_id': payment_method, 'account_id': credit_account,
                                      'debit': 0, 'credit': credit_amount})
                    debit_amount = 0
                    credit_amount = 0
                    partner_name = ''
                    payment_method = ''
                    debit_account = ''
                    credit_account = ''
                    updated_date = ''

            docargs = {
                'doc_ids': self.ids,
                'doc_model': self.model,
                'docs': docs,
                'lines': all_lines
            }

            return self.env['report'].render('sky_height.reservation_payment_report_template', docargs)
        else:
            pass


class RsReservation(models.Model):
    _name = 'rs.reservation'
    # _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'id desc'

    @api.onchange('lead_id')
    def get_unit_ids(self):
        for val in self:
            if val.lead_id and val.lead_id.property_id:
                val.unit_ids = [(6, 0, [val.lead_id.property_id.id])]

    # Add constrain for save value in readonly condition
    @api.constrains('unit_ids')
    def _check_unit_ids(self):
        for val in self:
            # TODO Append responsible User to sales persons
            if val.unit_ids:
                for unit in val.unit_ids:
                    val.user_ids |= unit.resp_user_id

    @api.onchange('unit_ids')
    def check_property_responsible(self):
        for val in self:
            # TODO Append responsible User to sales persons
            if val.unit_ids:
                for unit in val.unit_ids:
                    val.user_ids |= unit.resp_user_id

            # Empty payment term when change units
            val.pay_strategy_id = False

    @api.multi
    @api.depends('unit_ids')
    def get_properties_prices(self):
        for rec in self:
            if rec.unit_ids:
                rec.property_price = sum(unit.lst_price for unit in rec.unit_ids)
            else:
                rec.property_price = 0.0

    @api.multi
    def get_group_of_logged_user(self):
        for obj in self:
            user = self.env['res.users'].browse(obj.env.uid)
            obj.admin_status = False if not user.has_group('sky_height.group_sky_height_admin') else True
            obj.sales_status = True if user.has_group('base.group_sale_salesman') or user.has_group(
                'base.group_sale_salesman_all_leads') or user.has_group('base.group_sale_manager') else False

    @api.multi
    @api.onchange('customer_id')
    def get_partners(self):
        partners = []
        partner_obj = self.env['res.partner'].search([('customer', '=', True)])
        for partner in partner_obj:
            partners.append(partner.id)
        return {'domain': {'partner_ids': [('id', 'in', partners)]}}

    @api.model
    def _default_users(self):
        users = self.env.user
        active_id = self._context.get('active_id')
        if self._context.get('active_model') == 'res.users' and active_id:
            if active_id not in users.ids:
                users |= self.env['res.users'].browse(active_id)
        return users

    @api.constrains('user_ids')
    @api.onchange('user_ids')
    def get_sales_team_domain(self):
        team_ids = []
        team_obj = self.env['crm.team']
        teams = team_obj.search([])
        for user in self.user_ids:
            if user.sale_team_id:
                team_ids.append(user.sale_team_id.id)
            for team in teams:
                if team.user_id.id == user.id and team.id not in team_ids:
                    team_ids.append(team.id)
        self.sales_team_ids = team_obj.search([('id', 'in', team_ids)])

    @api.onchange('user_ids')
    def get_domain_users(self):
        domain_users = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group('base.group_sale_salesman') or \
                    user.has_group('base.group_sale_salesman_all_leads') or \
                    user.has_group('base.group_sale_manager') or \
                    user.has_group('sky_height.sale_team_leader_group'):
                domain_users.append(user.id)
        return {'domain': {'user_ids': [('id', 'in', domain_users)]}}

    name = fields.Char(string="Reservation Name")
    reservation_code = fields.Char(string="Reservation Code", readonly=True, copy=False)
    conditions = fields.Text(string="Conditions")
    project_id = fields.Many2one('project.project', _("Project"), required=True, domain=[('is_kpi', '=', False)])
    phase_id = fields.Many2one('project.phase', _('Phase'), required=True)
    unit_ids = fields.Many2many('product.product', string="Properties", required=True)
    pay_strategy_id = fields.Many2one('account.payment.term', string="Payment Strategy")
    payment_strg_name = fields.Char(string="Payment Strategy", related='pay_strategy_id.name', store=True)
    payment_term_discount = fields.Float(string="Payment Term Discount",
                                         related="pay_strategy_id.payment_term_discount", store=True, digits=(16, 6))
    lead_id = fields.Many2one('crm.lead', string="Lead")
    client_accountant_id = fields.Many2one('res.users', string="Client Accountant")
    marital_status = fields.Selection([('single', _("Single")),
                                       ('married', _("Married")),
                                       ('widowed', _("Widowed")),
                                       ('divorced', _("Divorced"))], _('Marital Status'),
                                      related='lead_id.marital_status')
    no_of_kids = fields.Integer(_('No. Of Family Member'))
    sales_type = fields.Selection([('direct', _("Direct")), ('indirect', _("Indirect")),
                                   ('individual_broker', _("Individual Broker")),
                                   ('client_referral', _("Client Referral")),
                                   ('employee_referral', _("Employee Referral")), ('resale', _("Resale")),
                                   ('upgrade', _("Upgrade")), ('supplier_through_sales', _("Supplier Through Sales")),
                                   ('supplier_through_company', _("Supplier Through Company")), ], _('Sales Type'))

    source = fields.Selection([('facebook', _("Facebook")), ('callcenter', _("Call Center")), ('website', _("Website")),
                               ('broker', _("Broker")), ('referral', _("Referral")), ('ambassador', _("Ambassador")),
                               ('other', _("Other")), ('self_generated', _("Self Generated"))],
                              string='Source')

    # related='lead_id.source'
    expire_date = fields.Datetime(string="Expiry Date", compute='_compute_expire_dates')
    reservation_date = fields.Datetime(string="Reservation Date")
    reservation_expiry_date = fields.Datetime(string="Reservation Expiry Date", compute='_compute_expire_dates')
    expire_date_difference = fields.Integer(string='Expire Difference', compute='_compute_expire_dates',
                                            store=True)
    confirm_date = fields.Datetime(string="Confirmation Date")
    customer_id = fields.Many2one('res.partner', string="Customer", required=True,
                                  domain=[('customer', '=', True), ('parent_id', '=', False)])
    address = fields.Char(string="Address", related='customer_id.street')
    phone = fields.Char(string="Phone", related='customer_id.phone')
    mobile = fields.Char(string="Mobile1", related='customer_id.mobile')
    email = fields.Char(string="Email", related='customer_id.email')
    user_ids = fields.Many2many('res.users', string="Sales Representative", required=True, default=_default_users,
                                )
    team_leader_ids = fields.Many2many('res.users', 'leader_reservation_user_rel', 'reservation_id', 'user_id',
                                       string='Team Leaders', compute='get_leader_and_manager', store=True)
    sales_manager_ids = fields.Many2many('res.users', 'manager_reservation_user_rel', 'reservation_id', 'user_id',
                                         string='Sales Manager', compute='get_leader_and_manager', store=True)
    id_no = fields.Char(string="Identification No.")
    id_type = fields.Selection([('id', _("ID")), ('passport', _("Passport"))], string="Identification Type")
    id_photo = fields.Binary("Photo ID")
    property_price = fields.Float(string="Property Price", compute="get_properties_prices", readonly=True,
                                  digits=(16, 6))
    discount = fields.Float(string="Discount Percentage", digits=(16, 15))
    total_discount = fields.Float('Total Discount', compute='_compute_total_discount', store=True)
    add_extension = fields.Boolean(string="Add Extension")
    admin_status = fields.Boolean(string="under admin group", compute='get_group_of_logged_user', default=True)
    sales_status = fields.Boolean(string="under Sales group", compute='get_group_of_logged_user', default=False)
    net_price = fields.Float(string="Net Price", compute='_calc_net_price', store=True, digits=(16, 6))
    discount_approval = fields.Boolean(string='Discount Approval')
    broker_ids = fields.Many2many('res.partner', 'res_broker_rel', 'product_id', 'res_id', _('Brokers'),
                                  domain=[('is_broker', '=', True)])
    sales_team_ids = fields.Many2many('crm.team', string="Sales Team")
    hide_payment_button = fields.Boolean(string="Hide")
    button_broker_paid = fields.Boolean(string="Hide Broker Payment button")
    button_salescommission_paid = fields.Boolean(string="Hide Sales Commission Payment button", default=False)
    receive_checks = fields.Boolean(string="Receive Checks")
    undercollection_check = fields.Boolean(string="Under Collection")
    initalized_check = fields.Boolean(string="Initalize")
    reviewed_check = fields.Boolean(string="Review")
    cancelled = fields.Boolean('Cancelled')
    approve_cancellation = fields.Boolean('Approve Cancellation')
    payment_approval = fields.Boolean(string='Payment Approval')
    request_exception = fields.Text('Exception Request')
    sale_order_id = fields.Many2one('sale.order', _('Order'), readonly=True)
    payment_strg_ids = fields.One2many('payment.strg', 'reserve_id', _('Payment'))
    is_payment_strg = fields.Boolean('Is Payment', default=False)
    attach_ids = fields.One2many('ir.attachment', 'reserve_id', string='Legal Papers')
    payment_attach_ids = fields.One2many('ir.attachment', 'cancel_reserve_id', string='Cancellation Papers')
    account_invoice_ids = fields.One2many('account.invoice', 'reserve_id', string='Commissions')
    state = fields.Selection([('draft', _("Draft")), ('request_exception', _("Request For Exception")),
                              ('exception_approval', _("Exception Approved")), ('in_progress', _("Reserved")),
                              ('confirm', _("Checks Received")), ('under_collection', _("Under Collection")),
                              ('initialize', _("Contract Initialized")), ('review', _("Contract Reviewed")),
                              ('create_so', _("Contracted")), ('cancel', _("Cancel"))], _('Status'), default='draft')
    receive_checks_journal_entry_id = fields.Many2one('account.move', _('Receive Checks'))
    under_collection__journal_entry_id = fields.Many2one('account.move', _('Under Collection'))

    # log users
    request_user_id = fields.Many2one('res.users', string="Requested By")
    exception_approval_user_id = fields.Many2one('res.users', string="Exception Approved By")
    exception_rejection_user_id = fields.Many2one('res.users', string="Exception Rejected By")
    in_progress_user_id = fields.Many2one('res.users', string="Reserved By")
    confirm_user_id = fields.Many2one('res.users', string="Confirmed By")
    initialize_user_id = fields.Many2one('res.users', string="Contract Initialized By")
    review_user_id = fields.Many2one('res.users', string="Contract Reviewed By")
    contract_user_id = fields.Many2one('res.users', string="Contracted By")
    cancel_user_id = fields.Many2one('res.users', string="Cancelled By")

    mobile1_type = fields.Selection([('local', 'Local'), ('foreign', 'Foreign')], related='customer_id.mobile1_type',
                                    string="Mobile1 Type")
    mobile2 = fields.Char('Mobile 2', related='customer_id.mobile2')
    mobile2_type = fields.Selection([('local', 'Local'), ('foreign', 'Foreign')], related='customer_id.mobile2_type',
                                    string="Mobile2 Type")

    partner_ids = fields.Many2many('res.partner', string="Partners", domain=get_partners)
    partners_name = fields.Char('Partners', compute='_get_partners_name')
    function = fields.Char('Job Title', related='customer_id.function')
    pdc_id = fields.Many2one('pds.status', "Payment Method")
    sales_customer_id = fields.Many2one('res.partner', string="Customer")
    sales_employee_id = fields.Many2one('hr.employee', string="Employee")
    currency_id = fields.Many2one('res.currency', compute='_get_company_currency',
                                  string="Currency", help='Utility field to express amount currency')

    other = fields.Char("Other")
    commission_flag = fields.Boolean(compute='_commission_flag')
    is_commission_created = fields.Boolean('Is Commission Created')
    created_date = fields.Datetime(string="Created on", default=fields.datetime.today())

    _defaults = {
        'created_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }

    @api.depends('account_invoice_ids')
    def _commission_flag(self):
        for rec in self:
            if rec.account_invoice_ids and rec.account_invoice_ids.ids:
                rec.commission_flag = True

    @api.multi
    @api.depends('user_ids', 'sales_team_ids')
    def get_leader_and_manager(self):
        user_obj = self.env['res.users']
        for record in self:
            team_leader_ids = []
            sales_manager_ids = []
            teams = self.env['crm.team'].search([])

            for user in record.user_ids:
                if user.sale_team_id and user.sale_team_id.user_id:
                    if user.sale_team_id.user_id.id not in team_leader_ids:
                        team_leader_ids.append(user.sale_team_id.user_id.id)
                for team in teams:
                    if team.user_id.id == user.id and user.id not in team_leader_ids:
                        team_leader_ids.append(user.id)
            record.team_leader_ids = user_obj.search([('id', 'in', team_leader_ids)])

            for team in record.sales_team_ids:
                if team.sales_manager_id:
                    if team.sales_manager_id.id not in sales_manager_ids:
                        sales_manager_ids.append(team.sales_manager_id.id)

            record.sales_manager_ids = user_obj.search([('id', 'in', sales_manager_ids)])

    @api.one
    def _get_company_currency(self):
        self.currency_id = self.env.user.company_id.currency_id

    @api.multi
    @api.depends('partner_ids')
    def _get_partners_name(self):
        for rec in self:
            partners_name = ""
            for partner in rec.partner_ids:
                if not partners_name:
                    partners_name = partner.name
                else:
                    partners_name += ' - ' + partner.name
            rec.partners_name = partners_name

    @api.constrains('mobile', 'mobile1_type')
    def check_mobile1_no(self):
        for val in self:
            if val.mobile and not val.mobile1_type:
                raise ValidationError(_("Sorry .. you must choose mobile 1 type !!"))
            if val.mobile:
                mobile = val.mobile
                partner_obj = self.search(['|', ('mobile', '=', val.mobile), ('mobile2', '=', val.mobile)]).ids
                reservation_obj = self.env['rs.reservation'].search(
                    ['&', '|', ('mobile', '=', val.mobile), ('mobile2', '=', val.mobile), '&', ('active', '=', True),
                     ('partner_id', '=', False)])

                if len(mobile) != 11 and val.mobile1_type == 'local':
                    raise ValidationError(_("Sorry .. mobile number must be 11 digit !!"))

                if len(mobile) < 11 and val.mobile1_type == 'foreign':
                    raise ValidationError(_("Sorry .. mobile number must be at least 11 digit !!"))

                if not (mobile.isdigit()):
                    raise ValidationError(_("Sorry .. Mobile number must contain integers only !!"))

                if len(partner_obj) > 1:
                    if val.id in partner_obj:
                        partner_obj.remove(val.id)
                    raise ValidationError(
                        _('Mobile Number Already exist with customer (%s)') % self.search([('id', 'in', partner_obj)],
                                                                                          limit=1).name)

                if reservation_obj:
                    ctx = self._context
                    if 'force_create_customer' in ctx:
                        if not ctx['force_create_customer']:
                            raise ValidationError(_("Sorry .. This mobile is already exist with active lead"))
                    else:
                        raise ValidationError(_("Sorry .. This mobile is already exist with active lead"))

    @api.constrains('mobile2', 'mobile2_type')
    def check_mobile2_no(self):
        for val in self:
            if val.mobile2 and not val.mobile2_type:
                raise ValidationError(_("Sorry .. you must choose mobile 2 type !!"))
            if val.mobile2:
                mobile = val.mobile2
                partner_obj = self.search(['|', ('mobile', '=', val.mobile2), ('mobile2', '=', val.mobile2)]).ids
                reservation_obj = self.env['rs.reservation'].search(
                    ['&', '|', ('mobile', '=', val.mobile2), ('mobile2', '=', val.mobile2), '&', ('active', '=', True),
                     ('partner_id', '=', False)])

                if len(mobile) != 11 and val.mobile2_type == 'local':
                    raise ValidationError(_("Sorry .. mobile number must be 11 digit !!"))

                if len(mobile) < 11 and val.mobile2_type == 'foreign':
                    raise ValidationError(_("Sorry .. mobile number must be at least 11 digit !!"))

                if not (mobile.isdigit()):
                    raise ValidationError(_("Sorry .. Mobile number must contain integers only !!"))

                if len(partner_obj) > 1:
                    if val.id in partner_obj:
                        partner_obj.remove(val.id)
                    raise ValidationError(
                        _('Mobile Number Already exist with customer (%s)') % self.search([('id', 'in', partner_obj)],
                                                                                          limit=1).name)

                if reservation_obj:
                    ctx = self._context
                    if 'force_create_customer' in ctx:
                        if not ctx['force_create_customer']:
                            raise ValidationError(_("Sorry .. This mobile is already exist with active Reservation"))
                    else:
                        raise ValidationError(_("Sorry .. This mobile is already exist with active Reservation"))

    @api.multi
    def check_button_salescommission_paid(self):
        for val in self:
            val.button_salescommission_paid = True

    @api.model
    def create(self, values):
        values['reservation_code'] = self.env['ir.sequence'].next_by_code('real.estate.reservation.id.seq')
        lead_id = self.env.context.get('default_lead_id')
        if lead_id:
            self.env['crm.lead'].search([('id', '=', lead_id)], limit=1).write({'active': False})
        return super(RsReservation, self).create(values)

    @api.multi
    def unlink(self):
        for record in self:
            if record.state in ['request_exception', 'exception_approval', 'confirm', 'in_progress', 'under_collection',
                                'initialize', 'review', 'create_so']:
                raise ValidationError(_('You must cancel reservation first.'))
            for property in record.unit_ids:
                property.write({'status': 'available'})
        return super(RsReservation, self).unlink()

    # @api.multi
    # @api.depends('created_date','reservation_code')
    # def name_get(self):
    #     result = []
    #     for val in self:
    #         if val.created_date and val.reservation_code:
    #             print val.created_date
    #             print val.reservation_code
    #             print val.id
    #             created_date = dateutil.parser.parse(val.created_date).date()
    #             name = val.reservation_code + ' - ' + str(created_date)
    #         result.append((val.id, name))
    #         print result,len(result)
    #     return result

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = record.reservation_code
            if record.created_date:
                created_date = dateutil.parser.parse(record.created_date).date()
                name = record.reservation_code + ' - ' + str(created_date)
            res.append((record.id, name))
        return res

    @api.multi
    def reservation_server_action(self):
        for rec in self:
            reservation_ids = self.env['rs.reservation'].search([])
            for reservation in reservation_ids:
                if reservation.created_date:
                    d1 = datetime.datetime.strptime(reservation.created_date, "%Y-%m-%d %H:%M:%S").date()
                    reservation_expiry = self.env['ir.values'].get_default('sky.height.settings', 'reservation_expiry')
                    if (float_compare((datetime.date.today() - d1).days, reservation_expiry, 2) in [0,
                                                                                                    1]) and reservation.state == 'draft':
                        reservation.write({'state': 'cancel'})
                        for unit in reservation.unit_ids:
                            unit.write({'status': 'available'})

    @api.multi
    def write(self, vals):
        for record in self:
            if 'payment_strg_ids' in vals:
                # self._check_total_payment_amount()
                for payment_strg in vals['payment_strg_ids']:
                    if len(payment_strg) >= 2 and payment_strg[0] != 0 and payment_strg[1] != 0 and type(
                            payment_strg[2]) == dict and 'amount' in payment_strg[2]:
                        record.is_payment_strg = True

            current_record = super(RsReservation, self).write(vals)
            user = self.env['res.users'].search([('id', '=', self.env.uid)])
            if len(vals) > 0 and vals.has_key('payment_strg_ids') and user.has_group('account.group_account_manager'):
                pass
            elif len(vals) > 0 and vals.has_key('payment_strg_ids') and user.has_group('account.group_account_user'):
                for payment in vals['payment_strg_ids']:
                    if len(payment) == 3 and payment[2] != False:
                        if len(payment[2]) == 1:
                            if payment[2].has_key('journal_id'):
                                pass
                            else:
                                raise ValidationError('Accountant can only edit in payment method')
                        else:
                            raise ValidationError('Accountant can only edit in payment method')

            return current_record

    @api.multi
    def copy(self, default=None):
        raise ValidationError(_("Sorry .. You Can't Duplicate The Reservation With Same Data!!"))

    @api.multi
    @api.depends('discount', 'payment_term_discount')
    def _compute_total_discount(self):
        for record in self:
            record.total_discount = record.discount + record.payment_term_discount

    @api.multi
    @api.depends('discount', 'payment_term_discount', 'property_price')
    def _calc_net_price(self):
        for record in self:
            first_discount = record.property_price - (record.property_price * (record.payment_term_discount / 100.0))
            record.net_price = first_discount - (
                    first_discount * (record.discount / 100.0))

    @api.multi
    @api.depends('created_date', 'reservation_date', 'confirm_date')
    def _compute_expire_dates(self):
        for val in self:
            if val.created_date:
                val.expire_date = (datetime.datetime.strptime(val.created_date,
                                                              "%Y-%m-%d %H:%M:%S")) + datetime.timedelta(days=3)
            if val.reservation_date:
                val.reservation_expiry_date = (datetime.datetime.strptime(val.reservation_date, "%Y-%m-%d %H:%M:%S")) \
                                              + datetime.timedelta(days=40)

                day1 = datetime.datetime.strptime(val.reservation_expiry_date, "%Y-%m-%d %H:%M:%S")
                day2 = datetime.datetime.now()
                val.expire_date_difference = (day2 - day1).days

    @api.constrains('pay_strategy_id', 'discount')
    def _check_installments(self):
        self._onchange_pay_strategy()
        old_payments = self.env['payment.strg'].search([('reserve_id', '=', False)])
        if old_payments:
            old_payments.sudo().unlink()

    @api.onchange('pay_strategy_id', 'discount')
    def _onchange_pay_strategy(self):
        inbound_payments = self.env['account.payment.method'].search([('payment_type', '=', 'inbound')])
        for rec in self:
            payments = []
            for payment in rec.payment_strg_ids:
                payment.write({
                    'reserve_id': False
                })
            if rec.pay_strategy_id and rec.pay_strategy_id.id:
                for payment_line in rec.pay_strategy_id.line_ids:
                    payment_methods = inbound_payments and payment_line.journal_id.inbound_payment_method_ids or \
                                      payment_line.journal_id.outbound_payment_method_ids
                    if rec.created_date:
                        date_order_format = datetime.datetime.strptime(rec.created_date, "%Y-%m-%d %H:%M:%S")
                    else:
                        date_order_format = datetime.date.today()
                    payment_date = date_order_format
                    if payment_line.days > 0:
                        no_months = payment_line.days / 30
                        date_order_day = date_order_format.day
                        date_order_month = date_order_format.month
                        date_order_year = date_order_format.year
                        payment_date = date(date_order_year, date_order_month, date_order_day) + relativedelta(
                            months=+no_months)
                    cheque_status = 'draft'

                    if payment_line.deposit:
                        cheque_status = 'received'

                    first_discount = rec.property_price - (
                            rec.property_price * (rec.payment_term_discount / 100.0))
                    net_price = first_discount - (
                            first_discount * (rec.discount / 100.0))
                    # net_price = rec.property_price - (
                    #         rec.property_price * ((rec.discount + rec.payment_term_discount)/ 100))

                    # Todo If line is Maintenance Fee
                    if payment_line.add_extension:
                        payment_amount = payment_line.value_amount * rec.property_price

                    else:
                        payment_amount = payment_line.value_amount * net_price
                    payment_arr = {'amount': payment_amount,
                                   'payment_date': payment_date,
                                   'journal_id': payment_line.journal_id.id,
                                   'description': payment_line.payment_description,
                                   'deposite': payment_line.deposit,
                                   'cheque_status': cheque_status,
                                   'add_extension': payment_line.add_extension,
                                   'payment_method_id': payment_methods.id and payment_methods[0].id or False,
                                   'property_ids': rec.unit_ids.ids
                                   }

                    payments.append((0, 0, payment_arr))
            rec.payment_strg_ids = payments

    @api.multi
    def button_confirm_receive_checks(self):
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        move_date = datetime.date.today()
        maintaince_move_date = datetime.date.today()
        maintaince = False
        for rec in self:
            if (float_compare(rec.discount, 0.0, 6) in [1]) and rec.discount_approval == False:
                raise ValidationError(_("Please Check Discount Approval"))
            if rec.payment_strg_ids.ids and rec.is_payment_strg == True and rec.payment_approval == False:
                raise ValidationError(_("Please Check Payment Approval"))
            if not rec.payment_attach_ids:
                raise ValidationError(_("You should attach Checks."))
            if rec.payment_attach_ids:
                if not any(attach.attach_type == 'checks' for attach in rec.payment_attach_ids):
                    raise ValidationError(_("You should attach a File of type checks."))
                for attach in rec.payment_attach_ids:
                    if attach.attach_type == 'checks' and attach.file_size == 0:
                        raise ValidationError(_("You should attach 'Checks' file that has size."))
            if rec.payment_strg_ids:
                if any(payment_strg.bank_name.id == False and payment_strg.type == 'bank' for payment_strg in
                       rec.payment_strg_ids):
                    raise ValidationError(_("Installment Bank Is Missing"))
                if any(payment_strg.cheque == False and payment_strg.type == 'bank' for payment_strg in
                       rec.payment_strg_ids):
                    raise ValidationError(_("Cheque Number Is Missing"))

            credit_amount = 0
            debit_amount = 0
            maintaince_credit_amount = 0
            reservation_journal_id = self.env['ir.values'].get_default('sky.height.settings', 'reservation_journal_id')
            if not reservation_journal_id:
                raise ValidationError(_("Please set reservation journal from configuration."))
            reservation_journal_obj = self.env['account.journal'].browse(reservation_journal_id)
            maintaince_journal_id = self.env['ir.values'].get_default('sky.height.settings', 'maintaince_journal_id')
            if not maintaince_journal_id:
                raise ValidationError(_("Please set maintaince journal from configuration."))
            maintaince_journal_obj = self.env['account.journal'].browse(maintaince_journal_id)

            reservation_move_obj = move_obj.create(
                {'date': datetime.date.today(), 'journal_id': reservation_journal_obj.id})

            for pay in rec.payment_strg_ids:
                line_journal = pay.journal_id
                line_name = '/'
                move_date = pay.payment_date
                if not pay.journal_id.default_credit_account_id or not pay.journal_id.default_debit_account_id:
                    raise ValidationError(
                        _('Please define default credit/debit accounts on the journal "%s".') % (pay.journal_id.name))
                if not pay.journal_id.default_credit_account_id or not pay.journal_id.default_debit_account_id:
                    raise ValidationError(
                        _('Please define default credit/debit accounts on the journal "%s".') % (rec.journal_id.name))

                if not pay.move_check and pay.journal_id and not pay.journal_id.show_checks:
                    pay.write({'cheque_status': 'collection', 'partner_id': rec.customer_id.id,
                               'property_ids': rec.unit_ids.ids})
                else:
                    pay.write({'cheque_status': 'received', 'partner_id': rec.customer_id.id,
                               'property_ids': rec.unit_ids.ids})

                if pay.move_check == False and pay.journal_id.type == 'bank':
                    if not pay.journal_id.default_credit_account_id or not pay.journal_id.default_debit_account_id:
                        raise ValidationError(_('Please define default credit/debit accounts on the journal "%s".') % (
                            pay.journal_id.name))
                    if float_compare(pay.maintainance_fees, 0.0, 6) in [1]:
                        maintaince = True
                        maintaince_credit_amount += pay.maintainance_fees
                        maintaince_move_date = pay.payment_date
                        line_journal = maintaince_journal_obj
                        line_name = 'maintaince'
                        move_line_obj.with_context(check_move_validity=False).create({
                            'move_id': reservation_move_obj.id,
                            'date': datetime.date.today(),
                            'date_maturity': pay.payment_date,
                            'journal_id': pay.journal_id.id,
                            'account_id': line_journal.default_credit_account_id.id,
                            'partner_id': rec.customer_id.id,
                            'project_id': pay.project_id.id,
                            'name': line_name,
                            'debit': pay.maintainance_fees,
                            'credit': 0.0,
                            'amount_currency': 0.0})
                        debit_amount = pay.amount - pay.maintainance_fees
                    else:
                        if pay.add_extension:
                            line_journal = maintaince_journal_obj
                            line_name = 'maintaince'
                        else:
                            line_journal = pay.journal_id
                            line_name = '/'
                        debit_amount = pay.amount
                    move_line_obj.with_context(check_move_validity=False).create({
                        'move_id': reservation_move_obj.id,
                        'date': datetime.date.today(),
                        'date_maturity': pay.payment_date,
                        'journal_id': pay.journal_id.id,
                        'account_id': line_journal.default_credit_account_id.id,
                        'partner_id': rec.customer_id.id,
                        'project_id': pay.project_id.id,
                        'name': '/',
                        'debit': debit_amount,
                        'credit': 0.0,
                        'amount_currency': 0.0})

                    # credit_amount += debit_amount
                    if not pay.add_extension:
                        credit_amount += debit_amount
                    else:
                        # maintaince line credit
                        move_line_obj.with_context(check_move_validity=False).create({
                            'move_id': reservation_move_obj.id,
                            'date': datetime.date.today(),
                            'date_maturity': pay.payment_date,
                            'journal_id': line_journal.id,
                            'account_id': rec.customer_id.extension_account_prereceivable.id,
                            'partner_id': rec.customer_id.id,
                            'name': 'maintaince',
                            'credit': pay.amount,
                            'debit': 0.0,
                            'amount_currency': 0.0})
            if maintaince:
                if not rec.customer_id.extension_account_prereceivable:
                    raise ValidationError(_('Sorry .. please set maintaince account in customer!'))
                move_line_obj.with_context(check_move_validity=False).create({
                    'move_id': reservation_move_obj.id,
                    'date': maintaince_move_date,
                    'date_maturity': datetime.date.today(),
                    'journal_id': maintaince_journal_obj.id,
                    'account_id': rec.customer_id.extension_account_prereceivable.id,
                    'partner_id': rec.customer_id.id,
                    'name': 'maintaince',
                    'credit': maintaince_credit_amount,
                    'debit': 0.0,
                    'amount_currency': 0.0})
            if not rec.customer_id.property_unearned_revenu_account_prereceivable:
                raise ValidationError(_("Sorry .. set unearned revenue account in customer!"))

            move_line_obj.with_context(check_move_validity=False).create({
                'move_id': reservation_move_obj.id,
                'date': datetime.date.today(),
                'date_maturity': move_date,
                'journal_id': reservation_journal_obj.id,
                'account_id': rec.customer_id.property_unearned_revenu_account_prereceivable.id,
                'partner_id': rec.customer_id.id,
                'name': 'customer payment',
                'credit': credit_amount,
                'debit': 0.0,
                'amount_currency': 0.0})
            reservation_move_obj.journal_id = reservation_journal_obj.id
            reservation_move_obj.post()
            if rec.state == 'in_progress':
                rec.write({'receive_checks': True, 'state': 'confirm'})
            if rec.state == 'initialize':
                rec.write({'receive_checks': True})
            return rec.write(
                {'receive_checks_journal_entry_id': reservation_move_obj.id, 'confirm_date': datetime.date.today(),
                 'confirm_user_id': self.env.user.id})

    @api.multi
    def create_sale_order(self):
        for val in self:

            sale_order_pool = self.env['sale.order']
            sale_order_line_pool = self.env['sale.order.line']

            if (float_compare(val.discount, 0.0, 6) in [1]) and val.discount_approval == False:
                raise ValidationError(_("Please Check Discount Approval"))
            if val.payment_strg_ids.ids and val.is_payment_strg == True and val.payment_approval == False:
                raise ValidationError(_("Please Check Payment Approval"))

            if not val.payment_attach_ids:
                raise ValidationError(_("You should attach signature ."))
            if val.payment_attach_ids:
                if not any(attach.attach_type == 'signature' for attach in val.payment_attach_ids):
                    raise ValidationError(_("You should attach a File of type signature."))
                for attach in val.payment_attach_ids:
                    if attach.attach_type == 'signature' and attach.file_size == 0:
                        raise ValidationError(_("You should attach 'Signature' file that has size."))

            # Create Sale Order
            vals = {}
            payments = []
            for payment_line in val.payment_strg_ids:
                payments.append((0, _, {'amount': payment_line.amount,
                                        'payment_date': payment_line.payment_date,
                                        'journal_id': payment_line.journal_id.id,
                                        'bank_name': payment_line.bank_name.id,
                                        'cheque': payment_line.cheque,
                                        'move_check': payment_line.move_check,
                                        'description': payment_line.description,
                                        'cus_bank': payment_line.cus_bank.id,
                                        'type': payment_line.type,
                                        'payment_id': payment_line.payment_id.id,

                                        }))

            vals.update({'partner_id': val.customer_id.id,
                         'conditions': val.conditions,
                         'payment_term_id': val.pay_strategy_id.id,
                         'state': 'draft',
                         'pricelist_id': val.customer_id.property_product_pricelist.id,
                         'partner_invoice_id': val.customer_id.id,
                         'partner_shipping_id': val.customer_id.id,
                         'date_order': datetime.date.today(),
                         'order_policy': 'manual',
                         'company_id': val.customer_id.company_id.id,
                         'reservation_id': val.id,
                         'origin': val.name,
                         'fiscal_position': '1',
                         'payment_strg_ids': payments,

                         })

            sale_id = sale_order_pool.create(vals)

            order_lines = {}
            for unit in val.unit_ids:
                order_lines.update(({'order_id': sale_id.id,
                                     'product_id': unit.id,
                                     'name': 'yttt',
                                     'product_uom_qty': '1',
                                     'price_unit': val.net_price,
                                     'state': 'draft',
                                     'company_id': '1',

                                     }))
                sale_order_line_pool.create(order_lines)
                val.lead_id.action_set_won()
                sale_id.action_done()
                unit.write({'status': 'contracted'})
            val.write({'state': 'create_so', 'sale_order_id': sale_id.id, 'contract_user_id': val.env.user.id})
            return True

    @api.multi
    def button_request_exception(self):
        for val in self:
            if (float_compare(val.discount, 0.0, 6) in [1]) and val.discount_approval == False:
                raise ValidationError(_("Please Check Discount Approval"))
            if val.payment_strg_ids.ids and val.is_payment_strg == True and val.payment_approval == False:
                raise ValidationError(_("Please Check Payment Approval"))
            if not val.request_exception:
                raise ValidationError(_('You Must Enter Exception Request'))
            return val.write({'state': 'request_exception', 'request_user_id': self.env.user.id})

    @api.multi
    def button_exception_approval(self):
        for val in self:
            if (float_compare(val.discount, 0.0, 6) in [1]) and val.discount_approval == False:
                raise ValidationError(_("Please Check Discount Approval"))
            if val.payment_strg_ids.ids and val.is_payment_strg == True and val.payment_approval == False:
                raise ValidationError(_("Please Check Payment Approval"))
            return val.write({'state': 'exception_approval', 'exception_approval_user_id': self.env.user.id})

    @api.multi
    def button_exception_rejection(self):
        for val in self:
            if (float_compare(val.discount, 0.0, 6) in [1]) and val.discount_approval == False:
                raise ValidationError(_("Please Check Discount Approval"))
            if val.payment_strg_ids.ids and val.is_payment_strg == True and val.payment_approval == False:
                raise ValidationError(_("Please Check Payment Approval"))

            return val.write({'state': 'draft', 'exception_rejection_user_id': self.env.user.id})

    @api.multi
    def button_initialize(self):
        for rec in self:
            if (float_compare(rec.discount, 0.0, 6) in [1]) and rec.discount_approval == False:
                raise ValidationError(_("Please Check Discount Approval"))
            if rec.payment_strg_ids.ids and rec.is_payment_strg == True and rec.payment_approval == False:
                raise ValidationError(_("Please Check Payment Approval"))
            if not rec.id_no:
                raise ValidationError(_('You Must Choose Id No.'))
            if not rec.id_type:
                raise ValidationError(_('You Must Choose ID Type'))
            if not rec.id_photo:
                raise ValidationError(_('You Must Choose Photo ID'))
            if not rec.attach_ids:
                raise ValidationError(_("You should attach legal papers."))
            if rec.attach_ids:
                if not any(attach.legal_type == 'legal1' for attach in rec.attach_ids):
                    raise ValidationError(_("You should Select Legal Attachment 1 Type."))
                for attach in rec.attach_ids:
                    if attach.legal_type == 'legal1' and attach.file_size == 0:
                        raise ValidationError(_("You should attach 'Legal 1' file that has size."))

            return rec.write({'state': 'initialize', 'initialize_user_id': self.env.user.id, 'initalized_check': True})

    @api.multi
    def under_collection_check(self):
        account_move_obj = self.env['account.move']
        account_move_line_obj = self.env['account.move.line']
        maintaince = False
        for rec in self:
            credit_amount = 0
            debit_amount = 0
            maintaince_credit_amount = 0
            under_collection_journal_id = self.env['ir.values'].get_default('sky.height.settings',
                                                                            'under_collection_journal_id')
            if (float_compare(rec.discount, 0.0, 6) in [1]) and rec.discount_approval == False:
                raise ValidationError(_("Please Check Discount Approval"))
            if rec.payment_strg_ids.ids and rec.is_payment_strg == True and rec.payment_approval == False:
                raise ValidationError(_("Please Check Payment Approval"))
            if not under_collection_journal_id:
                raise ValidationError(_("Please set under collection journal from skyheights configuration."))
            under_collection_journal_obj = self.env['account.journal'].browse(under_collection_journal_id)
            under_collection_move_obj = account_move_obj.create(
                {'date': datetime.date.today(), 'journal_id': under_collection_journal_obj.id})
            maintaince_journal_id = self.env['ir.values'].get_default('sky.height.settings', 'maintaince_journal_id')
            if not maintaince_journal_id:
                raise ValidationError(_("Please set maintaince journal from configuration."))
            maintaince_journal_obj = self.env['account.journal'].browse(maintaince_journal_id)
            if maintaince_journal_obj and not maintaince_journal_obj.under_collected_account_id:
                raise ValidationError(_("Please set undercollection account in maintaince journal from configuration."))
            for pay in rec.payment_strg_ids:
                if not pay.journal_id.default_credit_account_id or not pay.journal_id.default_debit_account_id:
                    raise ValidationError(
                        _('Please define default credit/debit accounts on the journal "%s".') % (rec.journal_id.name))
                if pay.deposite == False:
                    pay.write({'cheque_status': 'under_collection',
                               'under_collected_journal_entry_id': under_collection_move_obj.id})
                    if float_compare(pay.maintainance_fees, 0.0, 6) in [1]:
                        maintaince = True
                        maintaince_credit_amount += pay.maintainance_fees
                        account_move_line_obj.with_context(check_move_validity=False).create({
                            'move_id': under_collection_move_obj.id,
                            'date': datetime.date.today(),
                            'date_maturity': pay.payment_date,
                            'journal_id': pay.journal_id.id,
                            'account_id': maintaince_journal_obj.under_collected_account_id.id,
                            'partner_id': rec.customer_id.id,
                            'project_id': pay.project_id.id,
                            'name': 'under collection maintaince',
                            'debit': pay.maintainance_fees,
                            'credit': 0.0,
                            'amount_currency': 0.0})
                        debit_amount = pay.amount - pay.maintainance_fees
                    elif pay.add_extension:
                        maintaince = True
                        maintaince_credit_amount += pay.amount
                        account_move_line_obj.with_context(check_move_validity=False).create({
                            'move_id': under_collection_move_obj.id,
                            'date': datetime.date.today(),
                            'date_maturity': pay.payment_date,
                            'journal_id': pay.journal_id.id,
                            'account_id': maintaince_journal_obj.under_collected_account_id.id,
                            'partner_id': rec.customer_id.id,
                            'project_id': pay.project_id.id,
                            'name': 'under collection maintaince',
                            'debit': pay.amount,
                            'credit': 0.0,
                            'amount_currency': 0.0})
                        debit_amount = pay.amount - pay.amount
                    else:
                        debit_amount = pay.amount

                    credit_amount += debit_amount
                    if debit_amount != 0.0:
                        account_move_line_obj.with_context(check_move_validity=False).create({
                            'move_id': under_collection_move_obj.id,
                            'date': datetime.date.today(),
                            'date_maturity': pay.payment_date,
                            'journal_id': pay.journal_id.id,
                            'account_id': pay.journal_id.under_collected_account_id.id,
                            'partner_id': rec.customer_id.id,
                            'project_id': pay.project_id.id,
                            'name': pay.description,
                            'debit': debit_amount,
                            'credit': 0.0,
                            'amount_currency': 0.0
                        })

            if maintaince and maintaince_credit_amount != 0.0:
                account_move_line_obj.with_context(check_move_validity=False).create({
                    'move_id': under_collection_move_obj.id,
                    'date': datetime.date.today(),
                    'date_maturity': pay.payment_date,
                    'journal_id': pay.journal_id.id,
                    'account_id': maintaince_journal_obj.default_credit_account_id.id,
                    'partner_id': rec.customer_id.id,
                    'name': 'under collection maintaince',
                    'credit': maintaince_credit_amount,
                    'debit': 0.0,
                    'amount_currency': 0.0})
            account_move_line_obj.with_context(check_move_validity=False).create({
                'move_id': under_collection_move_obj.id,
                'date': datetime.date.today(),
                'date_maturity': pay.payment_date,
                'journal_id': pay.journal_id.id,
                'account_id': pay.journal_id.default_credit_account_id.id,
                'partner_id': rec.customer_id.id,
                'name': 'Under Collection ',
                'credit': credit_amount,
                'debit': 0.0,
                'amount_currency': 0.0,

            })
            under_collection_move_obj.journal_id = under_collection_journal_obj.id
            under_collection_move_obj.post()
            rec.write({'state': 'under_collection', 'undercollection_check': True,
                       'under_collection__journal_entry_id': under_collection_move_obj.id})

    @api.multi
    def button_review(self):
        for rec in self:
            if (float_compare(rec.discount, 0.0, 6) in [1]) and rec.discount_approval == False:
                raise ValidationError(_("Please Check Discount Approval"))
            if rec.payment_strg_ids.ids and rec.is_payment_strg == True and rec.payment_approval == False:
                raise ValidationError(_("Please Check Payment Approval"))
            if not any(attach.legal_type == 'legal2' for attach in rec.attach_ids):
                raise ValidationError(_("You should Select Legal Attachment 2 Type."))
            for attach in rec.attach_ids:
                if attach.legal_type == 'legal2' and attach.file_size == 0:
                    raise ValidationError(_("You should attach 'Legal 2' file that has size."))
            return rec.write({'state': 'review', 'review_user_id': self.env.user.id, 'reviewed_check': True})

    @api.multi
    def button_in_progress(self):
        for rec in self:
            user = self.env['res.users'].browse(self.env.uid)

            # Check if properties in reservation request are still available or not
            if (any(True for each_unit in rec.unit_ids if each_unit.status != 'available')):
                raise ValidationError(_("One or more of selected properties are not available"))

            if rec.discount and rec.discount_approval == False:
                raise ValidationError(_("Please Check Discount Approval"))
            if rec.payment_strg_ids.ids and rec.is_payment_strg == True and rec.payment_approval == False:
                raise ValidationError(_("Please Check Payment Approval"))
            if not rec.customer_id:
                raise ValidationError(_('You Must Choose Customer'))
            if not rec.pay_strategy_id:
                raise ValidationError(_('You Must Choose Payment Strategy'))

            if rec.payment_strg_ids:
                for pay in rec.payment_strg_ids:
                    if pay.deposite == True:
                        if not pay.move_id:
                            raise ValidationError(_('All Deposits Amount Must Be Paid'))

            if not rec.payment_attach_ids:
                raise ValidationError(_("You should attach Deposit Papers."))
            if rec.payment_attach_ids:
                if not any(attach.attach_type == 'deposit' for attach in rec.payment_attach_ids):
                    raise ValidationError(_("You should attach a File of type deposit."))
                if not any(attach.attach_type == 'signature' for attach in rec.payment_attach_ids):
                    raise ValidationError(_("You should attach a File of type signature."))
                for attach in rec.payment_attach_ids:
                    if attach.attach_type == 'deposit' and attach.file_size == 0:
                        raise ValidationError(_("You should attach 'Deposit' file that has size."))

            for unit in rec.unit_ids:
                unit.write({'status': 'reserved'})
            rec.sudo().write({'state': 'in_progress',
                              'reservation_date': datetime.date.today(),
                              'in_progress_user_id': self.env.user.id})
            if user.has_group('isky_access_rights.group_ar'):
                return {
                    'view_type': 'form',
                    'view_mode': 'tree',
                    'res_model': 'rs.reservation',
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'res_id': rec.id,
                }

    @api.multi
    def cancel(self):
        for rec in self:
            if not rec.approve_cancellation:
                raise ValidationError(_('Manager Must Approve Cancellation'))
            if not rec.payment_attach_ids:
                raise ValidationError(_("You should attach Cancellation papers."))
            if rec.payment_attach_ids:
                if not any(attach.attach_type == 'cancel' for attach in rec.payment_attach_ids):
                    raise ValidationError(_("You should attach a File of type cancel."))
                for attach in rec.payment_attach_ids:
                    if attach.attach_type == 'cancel' and attach.file_size == 0:
                        raise ValidationError(_("You should attach 'Cancel' file that has size."))

            if not rec.customer_id:
                raise ValidationError(_('You Must Choose Customer'))

            for unit in rec.unit_ids:
                unit.write({'status': 'available'})
            rec.write({'state': 'cancel', 'cancelled': True, 'cancel_user_id': rec.env.user.id})
            for inv in rec.account_invoice_ids:
                if inv.state not in ('draft', 'cancel'):
                    raise ValidationError(
                        _('Cannot cancel this sales order!'),
                        _('First cancel all invoices attached to this sales order.'))
                inv.signal_workflow('invoice_cancel')

            rec.sale_order_id.write({'state': 'cancel'})

    @api.constrains('created_date', 'expire_date')
    def _check_created_date(self):
        for obj in self:
            if obj.expire_date and obj.created_date and obj.expire_date <= obj.created_date:
                raise ValidationError(_('Expire Date Must be greater Than Creation Date'))

    @api.multi
    @api.onchange('project_id')
    def on_change_project(self):
        for rec in self:
            # rec.unit_ids = False
            all_phases = []
            if rec.phase_id.project_id.id != rec.project_id.id:
                rec.phase_id = False
            phases = self.env['project.phase'].search(
                [('project_id', '=', rec.project_id.id), ('available', '=', True)])
            for phase in phases:
                all_phases.append(phase.id)
            return {'domain': {'phase_id': [('id', 'in', all_phases)]}}

    @api.multi
    @api.onchange('phase_id')
    def on_change_phase(self):
        for rec in self:

            all_properties = []
            properties = self.env['product.product'].search([('project_id', '=', rec.project_id.id),
                                                             ('phase_id', '=', rec.phase_id.id),
                                                             ('type', '=', 'property'),
                                                             ('status', 'in', ['available'])])

            not_avail_prop = self.env['product.product'].search([('project_id', '=', rec.project_id.id),
                                                                 ('phase_id', '=', rec.phase_id.id),
                                                                 ('type', '=', 'property'),
                                                                 ('resp_user_id', '=', self.env.uid),
                                                                 ('status', 'in', ['not_available'])]).ids

            for property in properties:
                all_properties.append(property.id)

            if not_avail_prop:
                all_properties += not_avail_prop
            rec.unit_ids = rec.unit_ids if rec.unit_ids and len(rec.unit_ids) == 1 and rec.unit_ids.ids[
                0] in all_properties else False
            return {'domain': {'unit_ids': [('id', 'in', all_properties)]}}

    @api.multi
    def action_paid_broker_amount(self):
        for rec in self:
            if not rec.broker_ids:
                raise ValidationError(_('There is no Brokers'))
            if rec.state == 'draft':
                raise ValidationError(_('You Can not create invoice , Reservation state is draft'))
            if rec.state == 'cancel':
                raise ValidationError(_('You Can not create invoice , Reservation state is cancelled'))
            if rec.state not in ['draft', 'cancel']:
                account_invoice_obj = rec.env['account.invoice']
                for broker in rec.broker_ids:
                    if not broker.broker_commission_amount:
                        raise ValidationError(
                            _('You Must Enter Commission percentage for this broker "%s" ') % (broker.name))
                    if not broker.broker_commission_account:
                        raise ValidationError(
                            _('You Must Enter Commission account for this broker "%s" ') % (broker.name))

                    if broker.broker_commission_account:
                        account_invoice_obj.create({'partner_id': broker.id,
                                                    'company_id': self.env.user.company_id.id,
                                                    'property_account_payable_id': broker.broker_commission_account.id or False,
                                                    'reserve_id': rec.id,
                                                    'type': 'in_invoice',
                                                    'invoice_line_ids': [(0, 0, {
                                                        'name': 'Broker Commission',
                                                        'account_id': broker.broker_commission_account.id,
                                                        'price_unit': (rec.net_price * broker.broker_commission_amount)
                                                                      / 100.0,
                                                    })]
                                                    })
                    else:
                        raise ValidationError(_("You Must Enter Commission Account."))
                rec.write({'button_broker_paid': True})
        return True

    @api.multi
    def print_payment_report(self):
        data = {}
        data['form'] = \
            self.read(['name', 'reservation_code', 'project_id', 'phase_id', 'unit_ids', 'pay_strategy_id'])[0]
        data['ids'] = self.id
        return self.env['report'].get_action(self, 'sky_height.reservation_payment_report_template', data=data)

    @api.constrains('payment_strg_ids')
    def _check_payment_strg_ids(self):
        self._check_total_payment_amount()

    @api.multi
    @api.depends('net_price', 'payment_strg_ids', 'pay_strategy_id')
    def _check_total_payment_amount(self):
        for rec in self:
            total_amount = 0.0
            maintaince_amount = 0.0
            for payment_obj in rec.payment_strg_ids:
                if float_compare(payment_obj.maintainance_fees, 0.0, 6) in [1]:
                    if float_compare(payment_obj.maintainance_fees, payment_obj.amount, 6) in [1]:
                        raise ValidationError(_("Maintenance fees can not be greater than cheque amount!!"))
                    if payment_obj.old_value == 0.0:
                        payment_obj.old_value = payment_obj.amount
                        payment_obj.amount += payment_obj.maintainance_fees
                    total_amount += payment_obj.old_value

                elif payment_obj.add_extension:
                    maintaince_amount += payment_obj.amount
                else:
                    total_amount += round(payment_obj.amount, 6)
            if float_compare(round(total_amount), round(rec.net_price), 6) in [1, -1]:
                raise ValidationError(_('Total Amount of Payments Must Be Equal Net Price "%s". ') % rec.net_price)


class PDCStatus(models.Model):
    _name = 'pds.status'

    name = fields.Char("Name", required=True)


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    reserve_id = fields.Many2one('rs.reservation', string='Reservation')
    cancel_reserve_id = fields.Many2one('rs.reservation', string='Cancel Reservation')
    cancel_sale_reserve_id = fields.Many2one('sale.order', string='Cancel Reservation')
    legal_type = fields.Selection([('legal1', 'Legal Attachment 1'), ('legal2', 'Legal Attachment 2')], string='Type')

    attach_type = fields.Selection([('deposit', _("Deposit")),
                                    ('checks', _("Checks")),
                                    ('signature', _("Signature")),
                                    ('cancel', _("Cancellation")), ], _('Type'))
