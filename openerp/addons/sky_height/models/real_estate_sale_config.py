# -*- coding: utf-8 -*-

from openerp import api
from openerp import fields, models, api
from openerp.exceptions import ValidationError

class sale_configuration(models.TransientModel):
    _inherit = 'sale.config.settings'

    lead_period = fields.Float('Lead Expiration Period')

    @api.model
    def get_default_sale_config(self, fields):
        lead_period = self.env['ir.values'].get_default('sale.config.settings', 'lead_period')
        return {
            'lead_period': lead_period,
        }

    @api.multi
    def set_sale_defaults(self):
        self.ensure_one()
        if self.lead_period < 0:
            raise ValidationError("Sorry... Lead Expiration Period must be positive !!!")
        lead_period = self.lead_period
        res = self.env['ir.values'].sudo().set_default('sale.config.settings', 'lead_period', lead_period)
        return res