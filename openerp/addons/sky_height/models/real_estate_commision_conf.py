# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError


class CommissionConfiguration(models.Model):
    _name = 'commission.configuration'

    sales_type = fields.Selection([('direct', _("Direct")),
                                   ('indirect', _("Indirect")),
                                   ('individual_broker', _("Individual Broker")),
                                   ('client_referral', _("Client Referral")),
                                   ('employee_referral', _("Employee Referral")),
                                   ('resale', _("Resale")),
                                   ('upgrade', _("Upgrade")),
                                   ('supplier_through_sales', _("Supplier Through Sales")),
                                   ('supplier_through_company', _("Supplier Through Company")), ], string='Sales Type',
                                  required=True)

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
                                        ('operation_sr_executive', 'Operation Sr.Executive'),
                                        ('operation_executive', 'Operation Executive'),
                                        ('customer_ref_comm', 'Customer Referral'),
                                        ('employee_referral', 'Employee Referral'),
                                        ], string='Commission Type',
                                       required=True)
    amount_percentage = fields.Float(string='Amount / Percentage', digits=(16, 4))
    pay_type = fields.Selection([('percentage', 'Percentage'), ('amount', 'Amount')], string='Pay Type', required=True,
                                default='percentage')
    price_calculation = fields.Selection([('net_price', 'Net Price'), ('property_price', 'Property Price')],
                                         string='Price Calc.', required=True, default='property_price')
    commission_account_id = fields.Many2one('account.account', string="Account", required=True)

    @api.constrains('amount_percentage', 'pay_type', 'sales_type', 'commission_type')
    def commission_constrains(self):
        for val in self:
            if (val.amount_percentage > 100 or val.amount_percentage < 0) and val.pay_type == 'percentage':
                raise ValidationError(_("Sorry .. Percentage must be between 0 and 100 %"))

            check_type = self.search(
                [('sales_type', '=', val.sales_type), ('commission_type', '=', val.commission_type)])
            if len(check_type) > 1:
                raise ValidationError(_('Sorry .. this type is already exist !!'))
