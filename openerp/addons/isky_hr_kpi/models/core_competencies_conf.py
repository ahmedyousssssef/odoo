# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError

class CoreCompetenciesResConf(models.Model):
    _name = 'core.competencies.res.conf'
    _rec_name = 'description'

    description = fields.Text(string='Description')
    percentage = fields.Integer(string='Weight')

    @api.constrains('percentage')
    def _check_percentage(self):
        for rec in self:
            if rec.percentage > 100:
                raise ValidationError(_("Percentage should less than or equal 100."))



class CoreCompetenciesConf(models.Model):
    _name = 'core.competencies.conf'
    _rec_name = 'title'

    title = fields.Char(string='Title',required=1)
    description = fields.Text(string='Description')
    percentage = fields.Float(string='Weight')
    appraisal_id = fields.Many2one('hr.appraisal',string='Appraisal')

    @api.constrains('percentage', 'title')
    def core_competencies_constrains(self):
        for val in self:
            if val.percentage > 100 or val.percentage < 0:
                raise ValidationError(_("Sorry .. Percentage must be between 0 and 100 %"))
            check_title = self.search(
                [('title', '=', val.title)])
            if len(check_title) > 1:
                raise ValidationError(_('Sorry .. this title is already exist !!'))
            all_objs = self.search([])
            total_percentages = sum(obj.percentage for obj in all_objs)
            if total_percentages > 100:
                raise ValidationError(_("Sorry .. Total percentages must be less than or equal 100%"))





class CoreCompetenciesConfLine(models.Model):
    _name = 'core.competencies.conf.line'
    _rec_name = 'title'

    title = fields.Char(string='Title')
    description = fields.Text(string='Description')
    percentage = fields.Float(string='Weight',default=0.0)
    rate = fields.Float(string='Rate(%)',default=0.0)
    score = fields.Float(string='Score',compute='set_employee_score',default=0.0)
    appraisal_id = fields.Many2one('hr.appraisal',string='Appraisal')

    @api.onchange('percentage','rate')
    def set_employee_score(self):
        for rec in self:
            rec.score = rec.percentage * (rec.rate/100.0)

