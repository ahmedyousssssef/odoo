# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
from datetime import datetime
from dateutil import relativedelta
from openerp.exceptions import ValidationError


class isky_hr_contract_inherit(models.Model):
    _inherit = 'hr.contract'


    contract_expired = fields.Boolean(string="contract expired before three months")
    social_insurance_fixed = fields.Float(string='Fixed Social Insurance')
    social_insurance_variable = fields.Float(string='Variable Social Insurance')
    social_date_from = fields.Date(string='Insurance Start Date')
    social_date_to = fields.Date(string='Insurance End Date')
    transportation_allowance = fields.Float(string="Transportation Allowance Basic")
    mobile_allowance = fields.Float(string="Mobile Allowance Basic")


    @api.constrains('social_date_from', 'social_date_to')
    def _check_date(self):
        for record in self:
            if record.social_date_from > record.social_date_to:
                raise ValidationError(_('Insurance end date cannot be less than Insurance start date.'))

    @api.model
    def get_tree_color(self):
        for rec in self.env['hr.contract'].search([]):
            now = fields.Date.from_string(fields.Date.today())
            contract_end = fields.Date.from_string(rec.date_end)
            diff = relativedelta.relativedelta(contract_end, now).months
            if diff <= 3 :
                rec.contract_expired = True
            else:
                rec.contract_expired = False