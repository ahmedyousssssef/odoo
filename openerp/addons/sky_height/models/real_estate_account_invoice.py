# -*- coding: utf-8 -*-

from openerp import models, fields, api, _


class AccountInvoice(models.Model):
    _inherit = ['account.invoice']

    partner_code = fields.Char(string='Partner Code', related='partner_id.partner_code')
    reserve_id = fields.Many2one('rs.reservation', string='Reservation')
