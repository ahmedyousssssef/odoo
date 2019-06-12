# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError


class WizardPaymentLines(models.TransientModel):
    _name = 'fill.payment.lines'
    _rec_name = 'reservation_id'
    reservation_id = fields.Many2one('rs.reservation')
    pay_strg_ids = fields.One2many('reservation.payment.strgs.lines', 'wizard_id', string="Lines")

    @api.onchange('reservation_id')
    def get_payment_lines(self):
        for val in self:
            lines = []
            for payment in val.reservation_id.payment_strg_ids:
                lines.append((0, 0, {
                    'payment_strg_id': payment.id,
                    'bank_id': payment.bank_name.id,
                    'cheque': payment.cheque,
                }))
            val.pay_strg_ids = lines

    @api.multi
    def update_reservation_payments(self):
        for val in self:
            for line in val.pay_strg_ids:
                line.change_bank_cheque_name()


class PaymentLines(models.TransientModel):
    _name = 'reservation.payment.strgs.lines'

    payment_strg_id = fields.Many2one('payment.strg', 'Payment Strategy')
    wizard_id = fields.Many2one('fill.payment.lines', 'Wizard')
    bank_id = fields.Many2one('payment.bank', string="Bank Name")
    cheque = fields.Char(string="Cheque Number")

    @api.multi
    def change_bank_cheque_name(self):
        for val in self:
            if val.payment_strg_id:
                val.payment_strg_id.bank_name = val.bank_id.id
                val.payment_strg_id.cheque = val.cheque
