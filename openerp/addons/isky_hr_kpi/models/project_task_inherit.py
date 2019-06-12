# -*- coding: utf-8 -*-

from openerp import models, fields,api, _
from openerp.exceptions import UserError, ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    weight = fields.Float(string='Weight', default=0.0)
    weight_deadline = fields.Float(string='Weight', default=0.0)
    expected = fields.Float(string='Expected',default=0.0)
    achieved = fields.Float(string='Achieved',default=0.0)
    ratio = fields.Float(string='Ratio',compute='get_fields',default=0.0)
    final = fields.Float(string='Final',compute='get_fields',default=0.0)
    evaluation = fields.Float(string='Evalution',default=0.0)
    evaluation_on_score = fields.Float(string='Evalution On Score %',compute='get_fields',default=0.0)
    final_score = fields.Float(string='Final Score %',compute='get_fields',default=0.0)
    weighted_score = fields.Float(string='Weighted Score',compute='get_fields',default=0.0)
    diff = fields.Float(string='Diff (check point)',compute='get_fields',default=0.0)
    working_days = fields.Float(string='Working Days',default=0.0)
    achieved_days = fields.Float(string='Achieved Days',default=0.0)
    weighted_score_deadline = fields.Float(string='Weighted Score',compute='get_fields', default=0.0)
    diff_deadline = fields.Float(string='Diff', compute='get_fields', default=0.0)
    assigned_title = fields.Char(string='Assigned Title',related='project_id.assigned_title')
    from_date = fields.Date(string='From ',related='project_id.from_date')
    to_date = fields.Date(string='To ',related='project_id.to_date')
    is_kpi = fields.Boolean(string='Is KPI',related='project_id.is_kpi')

    @api.constrains('date_deadline')
    def _check_date_deadline(self):
        for rec in self:
            if rec.to_date and rec.date_deadline and rec.date_deadline > rec.to_date:
                raise ValidationError(_("Deadline date must not be greater than to date!!"))

    @api.constrains('weight','weight_deadline')
    def _check_technical_weight_and_deadline_weight(self):
        for rec in self:
            if rec.weight > 100.0 or rec.weight_deadline > 100.0:
                raise ValidationError(_("weight should not be greater thaan 100!!"))

            if rec.project_id:
                tasks = self.search([('project_id','=',rec.project_id.id)])
                project_obj = self.env['project.project'].browse(rec.project_id.id)
                # calc total weight for all tasks (Technical kpi)in project
                technical_project_weight = sum(task.weight for task in tasks)
                if technical_project_weight > project_obj.technical_weight:
                    raise ValidationError(_("Tasks technical weight should be less than or equal project weight"))
                # calc total weight for all tasks (Deadline)in project
                deadline_project_weight = sum(task.weight_deadline for task in tasks)
                if deadline_project_weight > project_obj.deadline_weight:
                    raise ValidationError(_("Tasks deadline weight should be less than or equal project weight"))

    @api.multi
    @api.depends('weight','expected','achieved','evaluation')
    def get_fields(self):
        for rec in self:
            if rec.expected and rec.achieved:
                rec.ratio = (rec.achieved / rec.expected) *100
                achievement_share = self.env['ir.values'].get_default('project.config.settings', 'achievement_share')
                if achievement_share:
                    rec.final = (rec.achieved / rec.expected)  * achievement_share
                quality_share = (self.env['ir.values'].get_default('project.config.settings', 'quality_share'))
                if quality_share:
                    quality_share /=100
                    rec.evaluation_on_score = (rec.evaluation / 100 * quality_share) * 100
                if rec.final and rec.evaluation_on_score:
                    rec.final_score = rec.final + rec.evaluation_on_score
                    rec.weighted_score = (rec.final_score * float(rec.weight)) / 100
                    rec.diff = float(rec.weight) - rec.weighted_score
            if rec.achieved_days:
                h_field = rec.working_days / rec.achieved_days
                i_field = h_field * rec.weight_deadline
                if i_field <= rec.weight_deadline:
                    rec.weighted_score_deadline = i_field
                if i_field > rec.weight_deadline:
                    rec.weighted_score_deadline = rec.weight_deadline
                rec.diff_deadline = rec.weight_deadline - rec.weighted_score_deadline

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        res = super(ProjectTask, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                            context=context, orderby=orderby)
        if 'project_id' in groupby:
            for line in res:
                tasks_in_project = self.search(domain)
                total_weight = sum(task.weight for task in tasks_in_project)
                total_weight_deadline = sum(task.weight_deadline for task in tasks_in_project)
                total_weight_score = sum(task.weighted_score for task in tasks_in_project)
                total_weight_score_deadline = sum(task.weighted_score_deadline for task in tasks_in_project)
                total_diff = sum(task.diff for task in tasks_in_project)
                total_diff_deadline = sum(task.diff_deadline for task in tasks_in_project)

                line.update({
                    'weight': total_weight,
                    'weight_deadline': total_weight_deadline,
                    'weighted_score': total_weight_score,
                    'weighted_score_deadline': total_weight_score_deadline,
                    'diff': total_diff,
                    'diff_deadline': total_diff_deadline
                })
        return res




