# -*- coding: utf-8 -*-

from openerp import api, fields, models,_
import datetime


class hr_applicant(models.Model):
    _inherit = 'hr.applicant'

    hiring_date = fields.Date(string="Hiring Date", )
    offer_expire_date = fields.Date(string="Offer Expiry Date", )
    benefits_offerd = fields.Text(string="Offered Benefits", )
    pro_date = fields.Date(string="Probation date",compute='calculate_pro_date' )
    certificate_ids = fields.One2many('hr.certification.and.degree','applicant_id',string='Certifications')
    emp_history_ids = fields.One2many('hr.employment.history','applicant_id',string='Employment History')
    course_ids = fields.One2many('hr.courses.and.qualification','applicant_id',string='Courses And Qualification')

    @api.one
    @api.depends('hiring_date')
    def calculate_pro_date(self):
        for record in self:
            if record.hiring_date:
                record.pro_date = (datetime.datetime.strptime(record.hiring_date,'%Y-%m-%d') +
                                   datetime.timedelta(3 * 365 / 12)).isoformat()



class hr_certification_and_degree(models.Model):
    _name = 'hr.certification.and.degree'
    _description = 'Certifications And Degrees'

    name = fields.Char(_('Certifications And Degrees'), size=512,required=True)
    college_name = fields.Char(_('Name of school & college'), size=512)
    date = fields.Date(_('Date'))
    inclusive_date = fields.Date(_('Inclusive Date'))
    country = fields.Many2one('res.country', _('Country'))
    applicant_id = fields.Many2one('hr.applicant', _('Applicant'))


class hr_employment_history(models.Model):
    _name = 'hr.employment.history'
    _description = 'Employment History'

    name = fields.Char(_('Employment History'), size=512,required=True)
    date_from = fields.Date(_('date from'), required=True)
    date_to = fields.Date(_('date to'), required=True)
    employer = fields.Char(_('Employer'), size=512)
    position = fields.Char(_('Position'), size=512)
    address = fields.Char(_('Address'), size=512)
    country = fields.Many2one('res.country', _('Country'))
    applicant_id = fields.Many2one('hr.applicant', _('Applicant'))

class hr_courses_and_qualification(models.Model):
    _name = 'hr.courses.and.qualification'
    _description = 'Additional Courses and Qualification'

    name = fields.Char(_('Courses and Qualification'), size=512,required=True)
    country = fields.Many2one('res.country', _('Country'))
    date = fields.Date(_('Date'))
    duration = fields.Integer(_('Duration in Months'))
    description = fields.Char(_('Description'), size=512)
    applicant_id = fields.Many2one('hr.applicant', _('Applicant'))


