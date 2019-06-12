# -*- coding: utf-8 -*-

from openerp import models, fields, api

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    user_id = fields.Many2one('res.users', string='Salesperson',
                    help='The internal user that is in charge of communicating with this contact if any.', default=lambda self: self.env.user.id)
