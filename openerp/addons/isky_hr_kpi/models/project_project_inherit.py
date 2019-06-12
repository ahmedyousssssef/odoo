# -*- coding: utf-8 -*-

from openerp import models, fields,api , _
from openerp.exceptions import UserError, ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    technical_objective = fields.Float(string='Technical Weight',compute='get_fields',default=0.0)
    deadline_objective = fields.Float(string='Deadline Weight',compute='get_fields',default=0.0)
    is_kpi = fields.Boolean(string='Is KPI')
    from_date = fields.Date(string='From')
    to_date = fields.Date(string='To')
    technical_weight = fields.Float(string='Technical Weight',default=0.0)
    deadline_weight = fields.Float(string='Deadline Weight',default=0.0)
    assigned_title = fields.Char(string='Assigned Title')

    @api.constrains('from_date','to_date')
    def _check_from_to_date(self):
        for rec in self:
            if rec.from_date > rec.to_date:
                raise ValidationError(_("From date must be less than or equal to date!!"))


    @api.constrains('technical_weight')
    def _check_technical_weight(self):
        for rec in self:
            if rec.technical_weight > 100.0:
                raise ValidationError(_("Project technical weight should be less than or equal 100%"))

    @api.multi
    def get_fields(self):
        for rec in self:
            tasks = self.env['project.task'].search([('project_id','=',rec.id)])
            if tasks:
                rec.technical_objective = sum(task.weighted_score for task in tasks)
                rec.deadline_objective = sum(task.weighted_score_deadline for task in tasks)