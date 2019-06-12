# -*- coding: utf-8 -*-

from openerp import models, fields, api,_
from openerp.exceptions import UserError, RedirectWarning, ValidationError

class AccountMove(models.Model):
    _inherit ='account.move'

    project_id = fields.Many2one('project.project', string='Project',compute='get_project_product',store=True)
    product_id = fields.Many2one('product.product', string='Product',compute='get_project_product',store=True)
    reserve_id = fields.Many2one('rs.reservation', string='Reservation')
    
    @api.multi
    @api.depends('line_ids')
    def get_project_product(self):
        for rec in self:
            for line in rec.line_ids:
                rec.product_id = line.product_id.id if line.product_id else False
                rec.project_id = line.project_id.id if line.project_id else False

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    project_id = fields.Many2one('project.project', string='Project',related='product_id.project_id')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    product_ids = fields.One2many('product.product','payment_id', string='Products',)


    @api.multi
    @api.onchange('invoice_ids')
    def take_products_to_journal(self):
        for record in self:
            products = []
            if record.invoice_ids:
                for invoice in record.invoice_ids:
                    for line in invoice.invoice_line_ids:
                        products.append(line.product_id.id)
            record.product_ids = products

    @api.multi
    def post(self):
        for rec in self:
            if rec.product_ids:
                if rec.state != 'draft':
                    raise UserError(
                        _("Only a draft payment can be posted. Trying to post a payment in state %s.") % rec.state)

                if any(inv.state != 'open' for inv in rec.invoice_ids):
                    raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(
                    sequence_code)

                # Create the journal entry
                amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
                move = rec._create_payment_entry(amount)

                # In case of a transfer, the first journal entry created debited the source liquidity account and credited
                # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
                if rec.payment_type == 'transfer':
                    transfer_credit_aml = move.line_ids.filtered(
                        lambda r: r.account_id == rec.company_id.transfer_account_id)
                    transfer_debit_aml = rec._create_transfer_entry(amount)
                    (transfer_credit_aml + transfer_debit_aml).reconcile()

                # take product confirm payment
                all_products = []
                i = 0
                if rec.product_ids:
                    for product in rec.product_ids:
                        all_products.append(product.id)
                if move:
                    if move.line_ids and not rec.invoice_ids:
                        for line in move.line_ids:
                            if i < len(all_products):
                                line.product_id = all_products[i]
                                i = i + 1

                rec.state = 'posted'
            else:
                super(AccountPayment,self).post()




