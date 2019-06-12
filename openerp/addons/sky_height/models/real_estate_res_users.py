# -*- coding: utf-8 -*-
from openerp import models, fields, api, _


class ResUsers(models.Model):
    _inherit = "res.users"

    sales_commission_amount =fields.Float('Commission Percentage')