# -*- coding: utf-8 -*-
import datetime
from dateutil.relativedelta import relativedelta

from openerp import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _name = "sale.order"

    def create_contract(self):
        """ Create a contract based on the order's quote template's contract template """
        self.ensure_one()
        if self.require_payment:
            payment_method = self.payment_tx_id.payment_method_id  # FORWARD-PORT: payment_method_id renamed to payment_token_id in 10.0
        if self.template_id and self.template_id.contract_template and not self.subscription_id \
                and any(self.order_line.mapped('product_id').mapped('recurring_invoice')):
            values = self._prepare_contract_data(payment_method_id=payment_method.id if self.require_payment else False)
            subscription = self.env['sale.subscription'].sudo().create(values)
            subscription.name = self.partner_id.name + ' - ' + subscription.code

            invoice_line_ids = []
            for line in self.order_line:
                if line.product_id.recurring_invoice:
                    invoice_line_ids.append((0, 0, {
                        'product_id': line.product_id.id,
                        'analytic_account_id': subscription.id,
                        'name': line.name,
                        'sold_quantity': line.product_uom_qty,
                        'discount': line.discount,
                        'uom_id': line.product_uom.id,
                        'price_unit': line.price_unit,
                    }))
            if invoice_line_ids:
                sub_values = {'recurring_invoice_line_ids': invoice_line_ids}
                subscription.write(sub_values)

            self.project_id = subscription.analytic_account_id
            # send new contract email to partner
            _, template_id = self.env['ir.model.data'].get_object_reference('website_contract', 'email_contract_open')
            mail_template = self.env['mail.template'].browse(template_id)
            mail_template.sudo().send_mail(subscription.id, force_send=True)
            return subscription
        return False

    def _prepare_contract_data(self, payment_method_id=False):
        contract_tmp = self.template_id.contract_template
        values = {
            'name': contract_tmp.name,
            'state': 'open',
            'type': 'contract',
            'template_id': contract_tmp.id,
            'partner_id': self.partner_id.id,
            'manager_id': self.user_id.id,
            'date_start': fields.Date.today(),
            'description': self.note,
            'payment_method_id': payment_method_id,
            'pricelist_id': self.pricelist_id.id,
            'recurring_rule_type': contract_tmp.recurring_rule_type,
            'recurring_interval': contract_tmp.recurring_interval,
            'company_id': self.company_id.id,
        }
        # if there already is an AA, use it in the subscription's inherits
        if self.project_id:
            values.pop('name')
            values.pop('partner_id')
            values.pop('company_id')
            values['analytic_account_id'] = self.project_id.id
        # compute the next date
        today = datetime.date.today()
        periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
        invoicing_period = relativedelta(**{periods[values['recurring_rule_type']]: values['recurring_interval']})
        recurring_next_date = today + invoicing_period
        values['recurring_next_date'] = fields.Date.to_string(recurring_next_date)
        if 'asset_category_id' in contract_tmp._fields:
            values.update({'asset_category_id': contract_tmp.asset_category_id and contract_tmp.asset_category_id.id})            
        return values

    @api.one
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.subscription_id and any(self.order_line.mapped('product_id').mapped('recurring_invoice')):
            lines = self.order_line.filtered(lambda s: s.product_id.recurring_invoice)
            msg_body = self.env.ref('website_contract.chatter_add_paid_option').render(values={'lines': lines})
            # done as sudo since salesman may not have write rights on subscriptions
            self.subscription_id.sudo().message_post(body=msg_body, author_id=self.env.user.partner_id.id)
        self.create_contract()
        return res

    # DBO: the following is there to amend the behaviour of website_sale:
    # - do not update price on sale_order_line where force_price = True
    #   (some options may have prices that are different from the product price)
    # - prevent having a cart with options for different contracts (project_id)
    # If we ever decide to move the payment code out of website_sale, we should scrap all this
    def set_project_id(self, account_id):
        """ Set the specified account_id sale.subscription as the sale_order project_id
        and remove all the recurring products from the sale order if the field was already defined"""
        account = self.env['sale.subscription'].browse(account_id)
        if self.project_id != account:
            self.reset_project_id()
        self.write({'project_id': account.analytic_account_id.id, 'user_id': account.manager_id.id if account.manager_id else False})

    def reset_project_id(self):
        """ Remove the project_id of the sale order and remove all sale.order.line whose
        product is recurring"""
        data = []
        for line in self.order_line:
            if line.product_id.product_tmpl_id.recurring_invoice:
                data.append((2, line.id))
        self.write({'order_line': data, 'project_id': False})

    def _get_payment_type(self):
        if any(line.product_id.recurring_invoice for line in self.sudo().order_line):
            return 'form_save'
        return super(SaleOrder, self)._get_payment_type()


class sale_order_line(models.Model):
    _inherit = "sale.order.line"
    _name = "sale.order.line"

    force_price = fields.Boolean('Force price', help='Force a specific price, regardless of any coupons or pricelist change', default=False)

    @api.model
    def _prepare_order_line_invoice_line(self, line, account_id=False):
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(line, account_id=account_id)
        if 'asset_category_id' in self.env['sale.subscription']._fields:
            if line.order_id.template_id and line.order_id.template_id.contract_template:
                if line.order_id.template_id.contract_template.asset_category_id and line.product_id.recurring_invoice:
                    res.update({'asset_category_id': line.order_id.template_id.contract_template.asset_category_id.id})
        return res
