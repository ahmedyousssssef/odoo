# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
import calendar
from openerp.exceptions import UserError



class isky_payroll_structure_inherit(models.Model):
    _inherit = 'hr.payroll.structure'

    grade = fields.Many2one('employee.grade', string='Employee Grade')


class isky_hr_payslip_inherit(models.Model):
    _inherit = 'hr.payslip'

    grade = fields.Many2one('employee.grade', related='employee_id.grade',string='Employee Grade',readonly=1)
    insurance_per = fields.Float(compute="_get_days")

    @api.one
    def _get_days(self):
        insurance_from = fields.Date.from_string(self.contract_id.social_date_from)
        insurance_to = fields.Date.from_string(self.contract_id.social_date_to)
        date_to = fields.Date.from_string(self.date_to)
        date_from = fields.Date.from_string(self.date_from)
        per = 0.0
        days = 0.0

        if self.contract_id.social_date_from and self.contract_id.social_date_to:

            if date_from >= insurance_from and date_to <= insurance_to:
                days = (date_to - date_from).days + 1
            elif date_from < insurance_from and date_to <= insurance_to and date_to > insurance_from:
                days = (date_to - insurance_from).days
            elif date_from > insurance_from and date_to > insurance_to and date_from < insurance_to:
                days = (insurance_to-date_from).days + 1

            month_days = calendar.monthrange(date_from.year, date_from.month)[1]
            if days and month_days > 0:
                per = float(days) / float(month_days)
            self.insurance_per = per

            return per
        else:
            raise UserError(
                _('You must set values to ( Insurance Start Date and Insurance End Date)'))
