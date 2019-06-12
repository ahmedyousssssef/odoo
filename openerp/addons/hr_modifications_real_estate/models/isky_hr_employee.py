# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
import datetime
from datetime import date

class isky_hr_employee_inherit(models.Model):
    _inherit = 'hr.employee'

    career_level = fields.Many2one('career.level', string='Career Level')
    extension_phone = fields.Char(string='Ext. Number')
    employee_id = fields.Char(string='Employee ID')
    graduation = fields.Selection(
        [('graduate', 'Graduate'), ('under_graduate', 'Under Graduate')],
        string="Graduation", default='graduate')

    military_status = fields.Selection(
        [('not_applicable', "Not Applicable"), ('postponed', "Postponed"), ('completed', "Completed"),
         ('exempted', "Exempted")],
        string='Military Status')

    address = fields.Char(string='Address')
    city = fields.Char(string='City')
    personal_mobile = fields.Char(string='Personal Mobile')
    institute = fields.Char(string='Institute')
    major = fields.Char(string='Major')
    employment = fields.Date(string='Employment Date')
    year = fields.Selection([(num, str(num)) for num in range(1960, (datetime.datetime.now().year) + 1)],
                            string='Graduation Year')

    medical_condition = fields.Text(string="Medical Condition")
    grade = fields.Many2one('employee.grade', string='Employee Grade')
    job_family = fields.Many2one('employee.job.family', string='Job Family')
    section = fields.Many2one('employee.section', string='Section')
    unit = fields.Many2one('employee.unit', string='Unit')


class career_level(models.Model):
    _name = 'career.level'

    name = fields.Char(string='Career Level', required=True)

class employee_grade(models.Model):
    _name = 'employee.grade'

    name = fields.Char(string='Grade', required=True)

class employee_job_family(models.Model):
    _name = 'employee.job.family'
    _rec_name = 'codes'

    codes = fields.Text(string='Codes', required=True)


class employee_section(models.Model):
    _name = 'employee.section'
    _rec_name = 'codes'

    codes = fields.Text(string='Codes', required=True)

class employee_unit(models.Model):
    _name = 'employee.unit'
    _rec_name = 'codes'

    codes = fields.Text(string='codes', required=True)
