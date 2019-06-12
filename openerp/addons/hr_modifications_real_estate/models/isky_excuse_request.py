# -*-	coding:	utf-8	-*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from datetime import datetime


class isky_excuse_request(models.Model):
    _name = 'isky.excuse.request'

    name = fields.Char(string='Reason', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    department = fields.Char(string='Department', related='employee_id.department_id.name')
    position = fields.Char(string='Position', related='employee_id.job_id.name')
    type_request = fields.Selection((('excuse', 'Excuse'), ('late', 'Late Arrival')), string='Request Type',
                                    required=True)
    date_from = fields.Datetime(required=True,string='Start Date')
    date_to = fields.Datetime(required=True,string='End Date')
    no_hours = fields.Float(string='Hours')

    @api.multi
    @api.onchange('date_from', 'date_to')
    @api.constrains('date_from', 'date_to')
    def _calc_hours(self):
        for record in self:
            if record.date_from and record.date_to:
                if record.date_from > record.date_to:
                    raise ValidationError('Start Date must be greater than End Date')
                else:
                    d_frm = datetime.strptime(record.date_from, '%Y-%m-%d %H:%M:%S')
                    d_to = datetime.strptime(record.date_to, '%Y-%m-%d %H:%M:%S')
                    difference = d_to - d_frm
                    record.no_hours = difference.seconds / 3600
