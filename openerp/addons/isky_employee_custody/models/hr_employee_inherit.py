#	-*-	coding:	utf-8	-*-
from openerp import models, fields, api, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'


    employee_code = fields.Char(string='Employee Code', copy=False, readonly=True)


