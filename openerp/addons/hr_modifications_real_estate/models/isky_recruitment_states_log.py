# -*- coding: utf-8 -*-
from openerp import api, fields, models, _


class isky_recruitment_state_log(models.Model):
    _name = 'recruitment.state.log'

    name = fields.Char(string='Job Name', required=True)
    department_id = fields.Many2one('hr.department', string='Department')
    user_id = fields.Many2one('res.users', string='Recruitment Responsible')
    no_of_recruitment = fields.Integer(string='Expected New Employees')
    state = fields.Char(string='Stage', required=True)
    date = fields.Datetime(string='Date')