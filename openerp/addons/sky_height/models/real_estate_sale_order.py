# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
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


class SaleOrder(models.Model):
    _inherit = "sale.order"

    payment_strg_ids = fields.One2many('payment.strg', 'sale_order_id', _('Payment'))
    reservation_id = fields.Many2one('rs.reservation', _('Reservation'), readonly=True)
    discount = fields.Float(string="Discount Percentage", related='reservation_id.discount', readonly=True)
    net_property_price = fields.Float(string="Net Price", related='reservation_id.net_price')
    approve_cancellation = fields.Boolean(string="Approve Cancellation")
    cancel_attach_ids = fields.One2many('ir.attachment', 'cancel_sale_reserve_id', string='Cancellation Papers')
    conditions = fields.Text(string="Conditions", related='reservation_id.conditions')
    delivery_journal_id = fields.Many2one('account.journal', _('Delivery Journal'))
    expense_journal_id = fields.Many2one('account.journal', _('Expense Journal'))
    delivery_debit_account_id = fields.Many2one('account.account', _('Delivery Debit Account'))
    delivery_credit_account_id = fields.Many2one('account.account', _('Delivery Credit Account'))
    expense_debit_account_id = fields.Many2one('account.account', _('Expense Debit Account'))
    expense_credit_account_id = fields.Many2one('account.account', _('Expense Credit Account'))
    delivery_journal_entry_id = fields.Many2one('account.move', _('Delivery Journal Entry'))
    expense_journal_entry_id = fields.Many2one('account.move', _('Expense Journal Entry'))
    hide_delivery_button = fields.Boolean('Hide Delivery_button')
    hide_expense_button = fields.Boolean('Hide Expense Button')
    user_ids = fields.Many2many('res.users', string='Sales Persons')

    @api.multi
    def cancel_quo_so(self):
        for rec in self:
            if not rec.approve_cancellation:
                raise ValidationError(_('Manager Must Approve Cancellation'))
            if not rec.cancel_attach_ids:
                raise ValidationError(_("You should attach Cancellation papers."))
            if rec.cancel_attach_ids:
                for attach in rec.cancel_attach_ids:
                    if attach.file_size == 0:
                        raise ValidationError(_("You should attach File that has size."))

            if not rec.partner_id:
                raise ValidationError(_('You Must Choose Customer'))
            res = self.env['ir.model.data'].get_object_reference('sky_height', 'form_cancel_process_view')
            view_id = res and res[1] or False

            ctx = {
                'default_property_price': rec.net_property_price,
                'default_customer_id': rec.partner_id.id,
                'default_reserve_id': rec.reservation_id.id,
                'default_order_id': rec.id,

            }

            return {
                'name': _("Cancel"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'cancel.process',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'domain': '[]',
                'context': ctx,
            }

    @api.multi
    def action_button_confirm(self):
        for rec in self:
            for line in rec.order_line:
                line.product_id.write({'status': 'deliverd'})
            return super(SaleOrder, self).action_button_confirm()

    @api.one
    def generate_delivery_entries(self):
        account_move_pool = self.env['account.move']
        journal_vals = {}
        line_vals = {}
        line_vals2 = {}
        for rec in self:
            if not rec.delivery_journal_id:
                raise ValidationError(_('Please Choose Delivery journal'))
            if not rec.delivery_debit_account_id:
                raise ValidationError(_('Please Choose Delivery Debit Account'))
            if not rec.delivery_credit_account_id:
                raise ValidationError(_('Please Choose Delivery Credit Account'))

            line_vals['name'] = rec.name
            line_vals['credit'] = 0.0
            line_vals['currency_id'] = rec.delivery_journal_id.currency_id.id
            for line in rec.order_line:
                line_vals['product_id'] = line.product_id.id
                line_vals['project_id'] = line.product_id.project_id.id
                if rec.net_property_price != 0:
                    if not rec.delivery_journal_id.currency_id:
                        line_vals['debit'] = rec.net_property_price
                        line_vals['amount_currency'] = 0.0
                    else:
                        line_vals['debit'] = rec.net_property_price / rec.delivery_journal_id.currency_id.rate
                        line_vals['amount_currency'] = rec.net_property_price
                line_vals['account_id'] = rec.delivery_debit_account_id.id
                line_vals['partner_id'] = rec.partner_id.id
                line_vals2['name'] = rec.name
                line_vals2['product_id'] = line.product_id.id
                line_vals2['project_id'] = line.product_id.project_id.id
                line_vals2['currency_id'] = rec.delivery_journal_id.currency_id.id
                line_vals2['partner_id'] = rec.partner_id.id
                line_vals2['debit'] = 0.0
                if not rec.delivery_journal_id.currency_id:

                    line_vals2['credit'] = rec.net_property_price
                    line_vals2['amount_currency'] = 0.0
                else:
                    line_vals2['credit'] = rec.net_property_price / rec.delivery_journal_id.currency_id.rate
                    line_vals2['amount_currency'] = -rec.net_property_price
                line_vals2['account_id'] = rec.delivery_credit_account_id.id
                journal_vals.update({
                    'journal_id': rec.delivery_journal_id.id,
                    'ref': line.product_id.name,
                    'date': datetime.date.today(),
                    'line_ids': [(0, 0, line_vals), (0, 0, line_vals2)]
                })
                move = account_move_pool.create(journal_vals)
                move.post()

            rec.write({'hide_delivery_button': True, 'delivery_journal_entry_id': move.id})

    @api.multi
    def generate_expense_entries(self):
        account_move_pool = self.env['account.move']
        journal_vals = {}
        line_vals = {}
        line_vals2 = {}
        for rec in self:
            if not rec.expense_journal_id:
                raise ValidationError(_('Please Choose Expense journal'))
            if not rec.expense_debit_account_id:
                raise ValidationError(_('Please Choose Expense Debit Account'))
            if not rec.expense_credit_account_id:
                raise ValidationError(_('Please Choose Expense Credit Account'))

            line_vals['name'] = rec.name
            line_vals['credit'] = 0.0
            line_vals['currency_id'] = rec.expense_journal_id.currency_id.id
            for line in rec.order_line:
                line_vals['product_id'] = line.product_id.id
                line_vals['project_id'] = line.product_id.project_id.id
                if rec.net_property_price != 0:
                    if not rec.expense_journal_id.currency_id:
                        line_vals['debit'] = self.net_property_price
                        line_vals['amount_currency'] = 0.0
                    else:
                        line_vals['debit'] = rec.net_property_price / rec.expense_journal_id.currency_id.rate
                        line_vals['amount_currency'] = rec.net_property_price
                line_vals['account_id'] = rec.expense_debit_account_id.id
                line_vals['partner_id'] = rec.partner_id.id

                line_vals2['name'] = rec.name
                line_vals2['product_id'] = line.product_id.id
                line_vals2['project_id'] = line.product_id.project_id.id
                line_vals2['currency_id'] = rec.expense_journal_id.currency_id.id
                line_vals2['partner_id'] = rec.partner_id.id
                line_vals2['debit'] = 0.0
                if not rec.expense_journal_id.currency_id:

                    line_vals2['credit'] = rec.net_property_price
                    line_vals2['amount_currency'] = 0.0
                else:
                    line_vals2['credit'] = rec.net_property_price / rec.expense_journal_id.currency_id.rate
                    line_vals2['amount_currency'] = -rec.net_property_price
                line_vals2['account_id'] = rec.expense_credit_account_id.id
                journal_vals.update({
                    'journal_id': rec.expense_journal_id.id,
                    'ref': line.product_id.name,
                    'date': datetime.date.today(),
                    'line_ids': [(0, 0, line_vals), (0, 0, line_vals2)]
                })
                move = account_move_pool.create(journal_vals)
                move.post()

            rec.write({'hide_expense_button': True, 'expense_journal_entry_id': move.id})


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    analytic_account_id = fields.Many2one('account.analytic.account', _('Analytic Account'),
                                          compute='_compute_analytic_account_id')

    @api.multi
    @api.depends('order_id')
    def _compute_analytic_account_id(self):
        for rec in self:
            if rec.order_id.project_id:
                rec.analytic_account_id = rec.order_id.project_id.id

    @api.multi
    def _prepare_order_line_invoice_line(self, account_id=False):
        res = super(SaleOrderLine, self)._prepare_order_line_invoice_line(account_id)
        for rec in self:
            res.update({'account_analytic_id': rec.analytic_account_id.id})
            return res


class RealStateCrmTeam(models.Model):
    _inherit = 'crm.team'

    sales_manager_id = fields.Many2one('res.users', string='Sales Manager')

    @api.onchange('user_id')
    def get_manger_sales(self):
        for val in self:
            if val.user_id:
                team_leader_emp = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
                team_mngr = team_leader_emp.parent_id.user_id.id
                val.sales_manager_id = team_mngr
            else:
                val.sales_manager_id = False
