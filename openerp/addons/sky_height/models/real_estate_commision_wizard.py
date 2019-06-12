# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError


class CommissionWizardLines(models.TransientModel):
    _name = 'commission.wizard.lines'

    partner_id = fields.Many2one('res.partner', string='Name')
    amount_percentage = fields.Float(string='Amount / Percentage', digits=(16, 4))
    pay_type = fields.Selection([('percentage', 'Percentage'), ('amount', 'Amount')], string='Pay Type', required=True)

    act_percentage = fields.Float(string='Act %', digits=(16, 4))
    amount = fields.Float(string='Amount')
    reservation_value = fields.Float(string='Reservation Value')
    wizard_id = fields.Many2one('commission.wizard', string='wizard')
    company_id = fields.Many2one('res.company', string='Company', )
    currency_id = fields.Many2one('res.currency', string='Company', )
    commission_type = fields.Selection([('sales_person', 'Sales Person'),
                                        ('sales_team_leader', 'Sales Team Leader'),
                                        ('sales_head', 'Sales Head'),
                                        ('sales_manager', 'Sales Manager'),
                                        ('legal_affairs', 'Legal Affairs'),
                                        ('client_accountant', 'Client Accountant'),
                                        ('development_head', 'Development Head'),
                                        ('operation_sr_manager', 'Operation Sr.Manager'),
                                        ('operation_manager', 'Operation Manager'),
                                        ('operation_senior_supervisor', 'Operation Senior Supervisor'),
                                        ('operation_supervisor', 'Operation Supervisor'),
                                        ('operation_sr_executive', 'Operation Sr.executive'),
                                        ('operation_executive', 'Operation Executive'),
                                        ('customer_ref_comm', 'Customer Referral'),
                                        ('employee_referral', 'Employee Referral'),
                                        ], string='Commission Type', required=True)

    commission_account_id = fields.Many2one('account.account', string="Account")

    @api.onchange('act_percentage')
    def get_act_total_amount(self):
        self.get_total_amount()

    @api.multi
    @api.onchange('amount_percentage')
    def get_total_amount(self):
        for val in self:
            sales_obj = self.env['commission.configuration'].search(
                [('sales_type', '=', val.wizard_id.sales_type), ('commission_type', '=', val.commission_type)], limit=1)

            if sales_obj.price_calculation == 'property_price':
                amount = val.wizard_id.reservation_tot_amount
                if val.pay_type == 'percentage':
                    val.amount = (((val.act_percentage * val.amount_percentage) / 100) * amount) / 100
                if val.pay_type == 'amount':
                    val.amount = val.amount_percentage

            if sales_obj.price_calculation == 'net_price':
                amount = val.wizard_id.reservation_id.net_price
                if val.pay_type == 'percentage':
                    val.amount = (((val.act_percentage * val.amount_percentage) / 100) * amount) / 100
                if val.pay_type == 'amount':
                    val.amount = val.amount_percentage

    @api.multi
    def create_vendor_bill(self, journal_id, reservation_id, account_id):
        for val in self:
            invoice_id = self.env['account.invoice']
            # TODO Create Invoice
            if not val.partner_id:
                raise ValidationError(_("Please Select Vendor !!"))
            invoice_id.create({'partner_id': val.partner_id.id,
                               'journal_id': journal_id.id,
                               'company_id': self.env.user.company_id.id,
                               'property_account_payable_id': val.partner_id.property_account_receivable_id.id,
                               'currency_id': self.env.user.company_id.currency_id.id,
                               'reserve_id': reservation_id.id,
                               'type': 'in_invoice',

                               'invoice_line_ids': [(0, 0, {
                                   'name': 'Property Commission',
                                   'account_id': account_id.id,
                                   'price_unit': val.amount,
                               })]
                               })


class CommissionWizard(models.TransientModel):
    _name = 'commission.wizard'

    @api.onchange('lines_ids')
    def onchange_lines_ids(self):
        for rec in self:
            rec.show_confirm_button = False

    @api.multi
    def update_commission(self):
        res = []
        self.ensure_one()
        percentage = 0.0
        sales_person_flag = False
        ctx = self._context
        team_leaders = []
        managers = []
        for line in self.lines_ids:
            if line.commission_type == 'sales_person':
                percentage += line.act_percentage
                sales_person_flag = True
                user = self.env['res.users'].search([('partner_id', '=', line.partner_id.id)])

                res.append({
                    'team_id': user.sale_team_id.id or self.env['crm.team'].search([('user_id', '=', user.id)],
                                                                                   limit=1).id,
                    'percentage': line.act_percentage
                })
            if line.commission_type == 'sales_team_leader' and line.partner_id.id not in team_leaders:
                team_leaders.append(line.partner_id.id)
            if line.commission_type == 'sales_manager' and line.partner_id.id not in managers:
                managers.append(line.partner_id.id)

        for line in self.lines_ids:
            user_obj = self.env['res.users'].search([('partner_id', '=', line.partner_id.id)])

            if len(team_leaders) > 0:
                if line.commission_type == 'sales_team_leader':
                    for recs in res:
                        team_obj = self.env['crm.team'].search([('user_id', '=', user_obj.id)])

                        if team_obj and (team_obj.id == recs['team_id']):
                            line.act_percentage = recs['percentage']

            if line.commission_type == 'sales_manager':
                for manager in self.reservation_id.sales_manager_ids:
                    manager_team_obj = self.env['crm.team'].search([('sales_manager_id', '=', manager.id)])

                    for val in res:
                        if val['team_id'] == manager_team_obj.id:
                            line_id = self.lines_ids.search([('wizard_id', '=', line.wizard_id.id),
                                                             ('partner_id', '=', manager.partner_id.id),
                                                             ('id', '=', line.id),
                                                             ('commission_type', '=', 'sales_manager')])
                            if line_id:
                                line_id.act_percentage = val['percentage']

            line.get_total_amount()
        self.show_confirm_button = False
        if percentage == 100.0:
            self.show_confirm_button = True
        else:
            if sales_person_flag == True:
                raise ValidationError(_("Sales person percentage must be equal 100%"))
            else:
                self.show_confirm_button = True
        return {
            "type": "ir.actions.do_nothing",
        }

    @api.model
    def get_default_journal_id(self):
        journal_id = self.env['ir.values'].get_default('sky.height.settings', 'commission_journal_id')
        if journal_id:
            return journal_id

    reservation_id = fields.Many2one('rs.reservation', string='Reservation', required=True)
    reservation_tot_amount = fields.Float(string='Reservation Total Amount', related='reservation_id.property_price')
    lines_ids = fields.One2many('commission.wizard.lines', 'wizard_id', string='Lines Commission')
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, default=get_default_journal_id)
    sales_type = fields.Selection([('resale', 'Resale'), ('direct', 'Direct'), ('indirect', 'Indirect'),
                                   ('client_referral', 'Client Referral'), ('upgrade', 'Upgrade')],
                                  string='Sales Type', related='reservation_id.sales_type', readonly=1)
    show_confirm_button = fields.Boolean(default=False)

    @api.multi
    def create_inv_vendor(self):
        for val in self:
            sp_percent = 0.0
            sales_person_flag = False
            for line in val.lines_ids:
                if line.commission_type == 'sales_person' and line.act_percentage:
                    sp_percent += round(line.act_percentage, 2)
                    sales_person_flag = True

            if sp_percent != 100 and sales_person_flag:
                raise ValidationError(_("Sales persons commissions must be 100%!!"))

            if val.lines_ids:
                for recs in val.lines_ids:
                    journal_id = val.journal_id
                    reservation_id = val.reservation_id
                    account_id = recs.commission_account_id
                    recs.create_vendor_bill(journal_id, reservation_id, account_id)
            else:
                raise ValidationError(_("Please Check Lines"))
            val.reservation_id.write({'is_commission_created': True})

    @api.multi
    @api.onchange('sales_type')
    def commission_lines(self):
        for record in self:
            record.lines_ids = []
            client_accountant_user = False
            users = self.env['res.users'].search([])
            line_objs = []
            comm_objects = self.env['commission.configuration'].search([('sales_type', '=', record.sales_type)])
            if comm_objects:
                # TODO Sales Manager Commission
                if record.reservation_id.sales_team_ids:
                    user_ids = []

                    for team in record.reservation_id.sales_team_ids:
                        if team.sales_manager_id and (team.sales_manager_id not in user_ids):
                            user_ids.append(team.sales_manager_id)

                    if user_ids:
                        for user in user_ids:
                            if user != 1:
                                sales_obj = self.env['commission.configuration'].search(
                                    [('sales_type', '=', record.sales_type),
                                     ('commission_type', '=', 'sales_manager')], limit=1)
                                sales_manager_percentage = sales_obj.amount_percentage
                                if sales_manager_percentage:
                                    line_objs.append(
                                        (0, 0, {'partner_id': user.partner_id.id,
                                                'sales_type': record.sales_type,
                                                'commission_type': 'sales_manager',
                                                'act_percentage': 100,
                                                'amount_percentage': sales_manager_percentage,
                                                'commission_account_id': sales_obj.commission_account_id.id,
                                                'pay_type': sales_obj.pay_type,
                                                'amount': sales_obj.amount_percentage
                                                }))

                # TODO Sales Team Leader Commission
                team_leader_ids = []
                for team in record.reservation_id.sales_team_ids:
                    if team.user_id.id != 1:
                        if team.user_id.partner_id:
                            if team.user_id.id not in record.reservation_id.user_ids.ids:
                                team_leader_ids.append(team.user_id.partner_id.id)

                for teamleader in team_leader_ids:
                    team_lead_comm_obj = self.env['commission.configuration'].search(
                        [('sales_type', '=', record.sales_type),
                         ('commission_type', '=', 'sales_team_leader')], limit=1)
                    sales_team_leader_percentage = team_lead_comm_obj.amount_percentage
                    if sales_team_leader_percentage:
                        line_objs.append(
                            (0, 0, {'partner_id': teamleader,
                                    'sales_type': record.sales_type,
                                    'commission_type': 'sales_team_leader',
                                    'act_percentage': 100,
                                    'pay_type': team_lead_comm_obj.pay_type,
                                    'amount_percentage': sales_team_leader_percentage,
                                    'commission_account_id': team_lead_comm_obj.commission_account_id.id
                                    }))

                # TODO Legal Affairs Commission
                legal_affairs_user = record.reservation_id.initialize_user_id.partner_id.id
                if legal_affairs_user and record.reservation_id.initialize_user_id.id != 1:
                    legal_comm_obj = self.env['commission.configuration'].search(
                        [('sales_type', '=', record.sales_type),
                         ('commission_type', '=', 'legal_affairs')], limit=1)
                    legal_affairs_percentage = legal_comm_obj.amount_percentage
                    if legal_affairs_percentage:
                        line_objs.append(
                            (0, 0, {'partner_id': legal_affairs_user,
                                    'sales_type': record.sales_type,
                                    'act_percentage': 100,
                                    'commission_type': 'legal_affairs',
                                    'pay_type': legal_comm_obj.pay_type,
                                    'amount_percentage': legal_affairs_percentage,
                                    'commission_account_id': legal_comm_obj.commission_account_id.id
                                    }))

                # TODO Sales Head Commission
                sales_head_users = []
                for user in users:
                    if user.has_group('sky_height.sales_head_user') and user.id != 1:
                        sales_head_users.append(user.id)

                if sales_head_users:
                    sales_head_comm_obj = self.env['commission.configuration'].search(
                        [('sales_type', '=', record.sales_type),
                         ('commission_type', '=', 'sales_head')], limit=1)
                    sales_head_percentage = sales_head_comm_obj.amount_percentage
                    if sales_head_percentage:
                        for user in sales_head_users:
                            user_obj = self.env['res.users'].browse(user)
                            line_objs.append(
                                (0, 0, {'partner_id': user_obj.partner_id.id,
                                        'sales_type': record.sales_type,
                                        'commission_type': 'sales_head',
                                        'act_percentage': 100,
                                        'amount_percentage': sales_head_percentage,
                                        'pay_type': sales_head_comm_obj.pay_type,
                                        'commission_account_id': sales_head_comm_obj.commission_account_id.id
                                        }))

                # TODO Development Head Commission
                development_head_users = []
                for user in users:
                    if user.has_group('sky_height.development_head_user') and user.id != 1:
                        development_head_users.append(user.id)

                if development_head_users:
                    dev_head_obj = self.env['commission.configuration'].search(
                        [('sales_type', '=', record.sales_type),
                         ('commission_type', '=', 'development_head')], limit=1)
                    development_head_percentage = dev_head_obj.amount_percentage
                    if development_head_percentage:
                        for user in development_head_users:
                            user_obj = self.env['res.users'].browse(user)
                            line_objs.append(
                                (0, 0, {'partner_id': user_obj.partner_id.id,
                                        'sales_type': record.sales_type,
                                        'act_percentage': 100,
                                        'commission_type': 'development_head',
                                        'amount_percentage': development_head_percentage,
                                        'pay_type': dev_head_obj.pay_type,
                                        'commission_account_id': dev_head_obj.commission_account_id.id
                                        }))

                # TODO Operation sr.manager Commission
                operation_sr_managers = []
                for user in users:
                    if user.has_group('sky_height.operation_sr_manager_user') and user.id != 1:
                        operation_sr_managers.append(user.id)

                if operation_sr_managers:
                    operation_mngr_obj = self.env['commission.configuration'].search(
                        [('sales_type', '=', record.sales_type),
                         ('commission_type', '=', 'operation_sr_manager')], limit=1)
                    operation_sr_manager_percentage = operation_mngr_obj.amount_percentage
                    if operation_sr_manager_percentage:
                        for user in operation_sr_managers:
                            user_obj = self.env['res.users'].browse(user)
                            line_objs.append(
                                (0, 0, {'partner_id': user_obj.partner_id.id,
                                        'sales_type': record.sales_type,
                                        'commission_type': 'operation_sr_manager',
                                        'act_percentage': 100,
                                        'pay_type': operation_mngr_obj.pay_type,
                                        'amount_percentage': operation_sr_manager_percentage,
                                        'commission_account_id': operation_mngr_obj.commission_account_id.id
                                        }))

                # TODO Operation senior supervisor Commission
                operation_senior_supervisors = []
                for user in users:
                    if user.has_group('sky_height.operation_senior_supervisor_user') and user.id != 1:
                        operation_senior_supervisors.append(user.id)

                if operation_senior_supervisors:
                    senior_super_obj = self.env['commission.configuration'].search(
                        [('sales_type', '=', record.sales_type),
                         ('commission_type', '=', 'operation_senior_supervisor')], limit=1)
                    operation_senior_supervisor_percentage = senior_super_obj.amount_percentage
                    if operation_senior_supervisor_percentage:
                        for user in operation_senior_supervisors:
                            user_obj = self.env['res.users'].browse(user)
                            line_objs.append(
                                (0, 0, {'partner_id': user_obj.partner_id.id,
                                        'act_percentage': 100,
                                        'sales_type': record.sales_type,
                                        'pay_type': senior_super_obj.pay_type,
                                        'commission_type': 'operation_senior_supervisor',
                                        'amount_percentage': operation_senior_supervisor_percentage,
                                        'commission_account_id': senior_super_obj.commission_account_id.id
                                        }))

                # TODO Operation supervisor Commission
                operation_supervisors = []
                for user in users:
                    if user.has_group('sky_height.operation_supervisor_user') and user.id != 1:
                        operation_supervisors.append(user.id)

                if operation_supervisors:
                    operation_super_obj = self.env['commission.configuration'].search(
                        [('sales_type', '=', record.sales_type),
                         ('commission_type', '=', 'operation_supervisor')], limit=1)
                    operation_supervisor_percentage = operation_super_obj.amount_percentage
                    if operation_supervisor_percentage:
                        for user in operation_supervisors:
                            user_obj = self.env['res.users'].browse(user)
                            line_objs.append(
                                (0, 0, {'partner_id': user_obj.partner_id.id,
                                        'act_percentage': 100,
                                        'sales_type': record.sales_type,
                                        'pay_type': operation_super_obj.pay_type,
                                        'commission_type': 'operation_supervisor',
                                        'amount_percentage': operation_supervisor_percentage,
                                        'commission_account_id': operation_super_obj.commission_account_id.id
                                        }))

                # TODO Operation sr.executive Commission
                operation_sr_executive_users = []
                for user in users:
                    if user.has_group('sky_height.operation_sr_executive_user') and user.id != 1:
                        operation_sr_executive_users.append(user.id)

                if operation_sr_executive_users:
                    sr_ex_obj = self.env['commission.configuration'].search(
                        [('sales_type', '=', record.sales_type),
                         ('commission_type', '=', 'operation_sr_executive')], limit=1)
                    operation_sr_executive_percentage = sr_ex_obj.amount_percentage
                    if operation_sr_executive_percentage:
                        for user in operation_sr_executive_users:
                            user_obj = self.env['res.users'].browse(user)
                            line_objs.append(
                                (0, 0, {'partner_id': user_obj.partner_id.id,
                                        'sales_type': record.sales_type,
                                        'act_percentage': 100,
                                        'pay_type': sr_ex_obj.pay_type,
                                        'commission_type': 'operation_sr_executive',
                                        'amount_percentage': operation_sr_executive_percentage,
                                        'commission_account_id': sr_ex_obj.commission_account_id.id
                                        }))

                # TODO Operation executive Commission
                operation_executive_users = []
                for user in users:
                    if user.has_group('sky_height.operation_executive_user') and user.id != 1:
                        operation_executive_users.append(user.id)

                if operation_executive_users:
                    operation_ex_obj = self.env['commission.configuration'].search(
                        [('sales_type', '=', record.sales_type),
                         ('commission_type', '=', 'operation_executive')], limit=1)
                    operation_executive_percentage = operation_ex_obj.amount_percentage
                    if operation_executive_percentage:
                        for user in operation_executive_users:
                            user_obj = self.env['res.users'].browse(user)
                            line_objs.append(
                                (0, 0, {'partner_id': user_obj.partner_id.id,
                                        'act_percentage': 100,
                                        'sales_type': record.sales_type,
                                        'pay_type': operation_ex_obj.pay_type,
                                        'commission_type': 'operation_executive',
                                        'amount_percentage': operation_executive_percentage,
                                        'commission_account_id': operation_ex_obj.commission_account_id.id
                                        }))

                # TODO client accountant Commission
                if record.reservation_id.client_accountant_id:
                    client_accountant_user = record.reservation_id.client_accountant_id

                if client_accountant_user and client_accountant_user.id != 1:
                    client_acc_obj = self.env['commission.configuration'].search(
                        [('sales_type', '=', record.sales_type),
                         ('commission_type', '=', 'client_accountant')], limit=1)
                    client_accountant_percentage = client_acc_obj.amount_percentage
                    if client_accountant_percentage:
                        line_objs.append(
                            (0, 0, {'partner_id': client_accountant_user.partner_id.id,
                                    'act_percentage': 100,
                                    'sales_type': record.sales_type,
                                    'pay_type': client_acc_obj.pay_type,
                                    'commission_type': 'client_accountant',
                                    'amount_percentage': client_accountant_percentage,
                                    'commission_account_id': client_acc_obj.commission_account_id.id
                                    }))

                # TODO Operation manager Commission
                operation_managers = []
                for user in users:
                    if user.has_group('sky_height.operation_manager_user') and user.id != 1:
                        operation_managers.append(user.id)
                #
                if operation_managers:
                    operation_managers_obj = self.env['commission.configuration'].search(
                        [('sales_type', '=', record.sales_type),
                         ('commission_type', '=', 'operation_manager')], limit=1)
                    operation_manager_percentage = operation_managers_obj.amount_percentage
                    if operation_manager_percentage:
                        for user in operation_managers:
                            user_obj = self.env['res.users'].browse(user)
                            line_objs.append(
                                (0, 0, {'partner_id': user_obj.partner_id.id,
                                        'sales_type': record.sales_type,
                                        'act_percentage': 100,
                                        'pay_type': operation_managers_obj.pay_type,
                                        'commission_type': 'operation_manager',
                                        'amount_percentage': operation_manager_percentage,
                                        'commission_account_id': operation_managers_obj.commission_account_id.id
                                        }))

                # TODO Sales Person Commission
                sales_persons_ids = []
                for sp in record.reservation_id.user_ids:
                    if sp.id != 1:
                        sales_persons_ids.append(sp.partner_id.id)
                sales_person_obj = self.env['commission.configuration'].search([('sales_type', '=', record.sales_type),
                                                                                ('commission_type', '=',
                                                                                 'sales_person')],
                                                                               limit=1)
                sales_persons_percentage = sales_person_obj.amount_percentage
                if sales_persons_ids and sales_persons_percentage:
                    for recs in sales_persons_ids:
                        line_objs.append(
                            (0, 0, {'partner_id': recs,
                                    'sales_type': record.sales_type,
                                    'act_percentage': 100.00 / len(sales_persons_ids),
                                    'commission_type': 'sales_person',
                                    'pay_type': sales_person_obj.pay_type,
                                    'amount_percentage': sales_persons_percentage,
                                    'commission_account_id': sales_person_obj.commission_account_id.id
                                    }))

                # # TODO Sales client referral Commission
                if record.sales_type == 'client_referral':
                    customer_ref_comm_obj = self.env['commission.configuration'].search(
                        [('sales_type', '=', record.sales_type), ('commission_type', '=', 'customer_ref_comm')],
                        limit=1)
                    if customer_ref_comm_obj:
                        line_objs.append(
                            (0, 0, {'partner_id': record.reservation_id.sales_customer_id.id,
                                    'sales_type': record.sales_type,
                                    'act_percentage': 100.00,
                                    'commission_type': 'customer_ref_comm',
                                    'pay_type': customer_ref_comm_obj.pay_type,
                                    'amount_percentage': customer_ref_comm_obj.amount_percentage,
                                    'commission_account_id': customer_ref_comm_obj.commission_account_id.id
                                    }))

                # TODO Sales employee referral Commission
                if record.sales_type == 'employee_referral':
                    if record.reservation_id.sales_employee_id.address_home_id:
                        employee_referral_comm_obj = self.env['commission.configuration'].search(
                            [('sales_type', '=', record.sales_type), ('commission_type', '=', 'employee_referral')],
                            limit=1)
                        if employee_referral_comm_obj:
                            line_objs.append(
                                (0, 0, {'partner_id': record.reservation_id.sales_employee_id.address_home_id.id,
                                        'sales_type': record.sales_type,
                                        'act_percentage': 100.00,
                                        'pay_type': employee_referral_comm_obj.pay_type,
                                        'commission_type': 'employee_referral',
                                        'amount_percentage': employee_referral_comm_obj.amount_percentage,
                                        'commission_account_id': employee_referral_comm_obj.commission_account_id.id
                                        }))
            record.lines_ids = line_objs
            if record.lines_ids:
                for line in record.lines_ids:
                    line.get_total_amount()
            record.reservation_id.write({'button_salescommission_paid': True})
