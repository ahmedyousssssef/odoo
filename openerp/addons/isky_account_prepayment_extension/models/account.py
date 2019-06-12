# -*- coding: utf-8 -*-
from openerp import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_account_prereceivable = fields.Many2one('account.account',string="Account Receivable (Prep.)", company_dependent=True,
            domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
            help="This account will be used instead of the default one as the prepayment receivable account for the current partner")
    extension_account_prereceivable = fields.Many2one('account.account',string="Maintenance AR (Prep.)", company_dependent=True,
            domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
            help="This account will be used instead of the default one as the prepayment receivable account for the current partner")
    property_unearned_revenu_account_prereceivable = fields.Many2one('account.account',string="Unearned Revenu AR (Prep.)", company_dependent=True,
            domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
            help="This account will be used instead of the default one as the prepayment receivable account for the current partner")
