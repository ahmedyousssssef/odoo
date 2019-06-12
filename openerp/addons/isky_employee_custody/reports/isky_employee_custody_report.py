# -*- coding: utf-8 -*-

import StringIO
import base64

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

class iSkyEmployeeCustodyReport(models.AbstractModel):
    _name = 'report.isky_employee_custody.all_custody_view_id'

    def _open_balance(self, employee_id, currency_id):
        open_balance_total = 0
        close_balance_total = 0
        total_transactions_sum = 0
        total_list = []
        custody_obj = self.env['employee.custody'].search([('employee_id', '=', employee_id), ('currency_id', '=', currency_id)])
        for each_custody in custody_obj:
            open_balance_total += each_custody.open_balance
            close_balance_total += each_custody.close_balance
            total_transactions_sum += each_custody.total_transactions
        total_list.append(open_balance_total)
        total_list.append(close_balance_total)
        total_list.append(total_transactions_sum)
        return total_list

    def _get_currency(self, employee_id):
        currency_ids = []
        return_values = []
        currency = self.env['employee.custody'].search([('employee_id', '=', employee_id)])
        for each_currency in currency:
            if each_currency.currency_id not in currency_ids:
                currency_ids.append(each_currency.currency_id)
        for each_cur in currency_ids:
            open_balance_total = 0
            close_balance_total = 0
            total_transactions_sum = 0
            each_line = []
            emp_name = ''
            for each_rec in self.env['employee.custody'].search([('employee_id', '=', employee_id), ('currency_id', '=', each_cur.id)]):
                open_balance_total += each_rec.open_balance
                close_balance_total += each_rec.close_balance
                total_transactions_sum += each_rec.total_transactions
                emp_name = each_rec.employee_id.display_name
            each_line.append(emp_name)
            each_line.append(open_balance_total)
            each_line.append(close_balance_total)
            each_line.append(total_transactions_sum)
            each_line.append(each_cur.display_name)
            return_values.append(each_line)
        return return_values

    @api.multi
    def render_html(self,docids, data=None):
        docs = self.env['employee.custody'].browse(data['ids'])
        employee_ids = []
        for doc in docs:
            if doc.employee_id.id not in employee_ids:
                employee_ids.append(doc.employee_id.id)
        docs = self.env['hr.employee'].browse(employee_ids)
        records = {
            'open_balance': self._open_balance,
            'doc_ids': data['ids'],
            'doc_model': 'employee.custody',
            'docs': docs,
            'currency': self._get_currency
        }
        return self.env['report'].render('isky_employee_custody.all_custody_view_id', records)

class isky_employee_custody(models.TransientModel):
    _name = "isky.employee.custody.report"

    employee_id= fields.Many2one('hr.employee', string='Sales Person')
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    loan_id = fields.Many2one('custody.category', 'Custody Category')

    @api.multi
    def display_data(self):
        domain = []
        view_id = self.env.ref('isky_employee_custody.view_employee_custody_tree_report').id
        ctx = dict(self._context, )
        for val in self:
            if val.from_date and val.to_date:
                if val.to_date <= val.from_date:
                    raise ValidationError("Date to must be greater than Date from !! ")
            domain = []
            if val.employee_id:
                domain += [('employee_id', '=', self.employee_id.id)]
            if val.from_date:
                domain += [('custody_date', '>=', self.from_date)]
            if val.to_date:
                domain += [('custody_date', '<=', self.to_date)]
            if val.loan_id:
                domain += [('loan_id', '=', self.loan_id.id)]

        return {
            'domain': domain,
            'name': _('Employees Custody Report'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'employee.custody',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'context': ctx,
        }

    @api.multi
    def print_data(self):
        for val in self:
            if val.from_date and val.to_date:
                if val.to_date <= val.from_date:
                    raise ValidationError("Date to must be greater than Date from !! ")
            domain = []
            if val.employee_id:
                domain += [('employee_id', '=', self.employee_id.id)]
            if val.from_date:
                domain += [('custody_date', '>=', self.from_date)]
            if val.to_date:
                domain += [('custody_date', '<=', self.to_date)]
            if val.loan_id:
                domain += [('loan_id', '=', self.loan_id.id)]
            data = {}
            data['ids'] = self.env['employee.custody'].search(domain).ids or False

            if data['ids']:
                if self.env.context.get('print'):
                    return self.env['report'].with_context({'loan_id': self.loan_id.id}).get_action(self, 'isky_employee_custody.all_custody_view_id', data=data)
            else:
                raise ValidationError("Sorry .. Can't Find Employee Custody!!")

            if self.env.context.get('export'):
                list_header = []
                list_header.append("Employee")
                list_header.append("Debit")
                list_header.append("Credit")
                list_header.append("Balance")
                list_header.append("Currency")
                output = StringIO.StringIO()
                value = ','.join(list_header)
                output.write(value)
                output.write("\n")
                if data['ids']:
                    employees = []
                    for each_custody in self.env['employee.custody'].search(domain):
                        if each_custody.employee_id not in employees:
                            employees.append(each_custody.employee_id)
                    for each_emp in employees:
                        currency_ids = []
                        return_values = []

                        currency = self.env['employee.custody'].search([('employee_id', '=', each_emp.id)])
                        for each_currency in currency:
                            if each_currency.currency_id not in currency_ids:
                                currency_ids.append(each_currency.currency_id)
                        for each_cur in currency_ids:
                            get_total = self.env['report.isky_employee_custody.all_custody_view_id']._open_balance(each_emp.id, each_cur.id)
                            custody_list = []
                            custody_list.append('"' + str(each_emp.name) + '"')
                            custody_list.append('"' + str(get_total[0]) + '"')
                            custody_list.append('"' + str(get_total[2]) + '"')
                            custody_list.append('"' + str(get_total[1]) + '"')
                            custody_list.append('"' + str(each_cur.display_name) + '"')
                            value_list = ','.join(custody_list)
                            output.write(value_list)
                            output.write("\n")
                    data = base64.encodestring(output.getvalue())
                    name = "%s.csv" % ("employee_custody_excel_report")

                    export_id = self.env['employee.custody.report'].create({'excel_file': data, 'file_name': name})
                    view_id = self.env.ref('isky_employee_custody.custody_export_excel_view').id
                    return {
                        'name': _('Export Excel'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'employee.custody.report',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'res_id': export_id.id,
                        'views': [(False, 'form')],
                        'target': 'new',
                        'view_id': view_id,
                    }

class EmployeeCustodyReportInherit(models.TransientModel):
    _name = 'employee.custody.report'

    file_name = fields.Char('File Name', readonly=True, size=256,
                            help="Write File Path you want to export system data in")
    excel_file = fields.Binary('Download report Excel', readonly=True)