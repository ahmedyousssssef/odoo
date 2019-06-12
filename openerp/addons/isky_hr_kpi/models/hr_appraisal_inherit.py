# -*- coding: utf-8 -*-

from openerp import models, fields,api,_
from openerp.exceptions import UserError, ValidationError


class HrAppraisal(models.Model):
    _inherit = 'hr.appraisal'

    core_competencies_ids = fields.One2many('core.competencies.conf.line','appraisal_id',string='Competencies')
    show = fields.Boolean(string='Show?')
    final_res_competencies = fields.Html(string='Competencies Appraisal',compute='get_competencies_res')
    self_share = fields.Float(string='Self',default=0.0)
    team_share = fields.Float(string='Team',default=0.0)
    no_subordinates = fields.Integer(string='No.subordinates',compute='get_no_subordinates')
    subordinates_score = fields.Float(string='Subordinates Scores',default=0.0)
    technical_share_score = fields.Float(string='Item Score',compute='get_fields',default=0.0)
    technical_share_net_score = fields.Float(string='Net Score',compute='get_fields',default=0.0)
    timeline_share_score = fields.Float(string='Item Score',compute='get_fields',default=0.0)
    timeline_share_net_score = fields.Float(string='Net Score',compute='get_fields',default=0.0)
    net_technical_net_score = fields.Float(string='Net Score ',compute='get_fields',default=0.0)
    competencies_evaluation_net_score = fields.Float(string='Net Score ',compute='get_fields',default=0.0)
    employee_self_performance_appraisal_score = fields.Float(string='employee self performance appraisal',compute='get_fields',default=0.0)
    employee_self_performance_appraisal = fields.Html(string='',compute='get_fields')
    subordinates_text = fields.Html(string='')
    show_res = fields.Boolean('')
    final_res = fields.Html(string='',compute='calc_final_res')
    from_date = fields.Date(string='From')
    to_date = fields.Date(string='To')

    @api.constrains('date_close')
    def _check_date_close(self):
        for rec in self:
            if rec.to_date and rec.date_close and rec.date_close > rec.to_date:
                raise ValidationError(_("Appraisal date must be less than or equal To date!!"))
    @api.multi
    def get_no_subordinates(self):
        for rec in self:
            no_subordinates = self.env['hr.employee'].search([('parent_id','=',rec.employee_id.id)])
            if no_subordinates:
                rec.no_subordinates = len(no_subordinates)
            else:
                rec.no_subordinates= 0


    @api.multi
    @api.onchange('self_share','team_share')
    def calc_final_res(self):
        for rec in self:
            avg_value_subordinate = 1
            if rec.no_subordinates > 0:
                avg_value_subordinate = rec.subordinates_score / rec.no_subordinates
            rec.final_res = "<table style = 'height: 152px; width: 100%;' class='table table-bordered'>" \
                                    "<tbody>" \
                                    "<tr><td style = 'width: 195.75px; text-align: center;' bgcolor='#000000'><span style='color:#ffffff'><strong> Item </strong></span></td>" \
                                    "<td style = 'width: 76.25px; text-align: center;' bgcolor='#000000'><span style='color:#ffffff'> <strong>Net Score </strong></span></td>" \
                                    "</tr><tr>" \
                                    "<td style = 'width: 195.75px;'><span style='color:#000000'><strong> Employee performance apprasial share result</strong></span> </td>" \
                                    "<td style = 'width: 76.25px;'><center><strong>" + str(rec.employee_self_performance_appraisal_score * rec.self_share / 100.0) + "</strong></center></td>" \
                                       "</tr><tr>" \
                                       "<td style = 'width: 195.75px;'><span style='color:#000000'><strong> Net Team share result</strong></span> </td>" \
                                       "<td style = 'width: 76.25px;'><center>" + str(avg_value_subordinate * rec.team_share / 100.0) + "</strong></center></td>" \
                                          "</tr><tr>" \
                                          "<td style = 'width: 195.75px;' bgcolor='#000000'><span style='color:#ffffff'><strong>Performance Apprasial total</strong></span> </td>" \
                                          "<td style = 'width: 76.25px;' bgcolor='#000000'><center><strong>" + str((avg_value_subordinate * rec.team_share / 100.0) +(rec.employee_self_performance_appraisal_score * rec.self_share / 100.0)) + "</strong></center></td></tr></tbody></table>"

    @api.multi
    def get_subordinateds_text(self):
        for rec in self:
            rec.show_res = True
            rec.subordinates_text =""
            if rec.no_subordinates > 0:
                rec.subordinates_text = "<table style = 'height: 152px; width: 100%;' class='table table-bordered'>" \
                                        "<tbody>" \
                                        "<tr><td style = 'width: 195.75px; text-align: center;' bgcolor='#000000'><span style='color:#ffffff'><strong> Item </strong></span></td>" \
                                        "<td style = 'width: 76.25px; text-align: center;' bgcolor='#000000'><span style='color:#ffffff'> <strong>Net Score </strong></span></td>" \
                                        "</tr><tr>" \
                                        "<td style = 'width: 195.75px;'><span style='color:#000000'><strong>Number of subordinates</strong></span> </td>" \
                                        "<td style = 'width: 76.25px;'><center><strong>" + str(rec.no_subordinates) + "</strong></center></td>" \
                                        "</tr><tr>" \
                                        "<td style = 'width: 195.75px;'><span style='color:#000000'><strong> Sum of appraised score of the subordinates</strong></span> </td>" \
                                        "<td style = 'width: 76.25px;'><center>" + str(rec.subordinates_score) + "</strong></center></td>" \
                                        "</tr><tr>" \
                                        "<td style = 'width: 195.75px;' bgcolor='#000000'><span style='color:#ffffff'><strong> Average value of the team appraisal</strong></span> </td>" \
                                        "<td style = 'width: 76.25px;' bgcolor='#000000'><center><strong style='color: white;'>"+str(round((rec.subordinates_score / rec.no_subordinates),2)) + "%</strong></center></td></tr></tbody></table>"



    @api.multi
    def get_fields(self):
        technical_share_score = 0
        timeline_share_score = 0
        task_obj = self.env['project.task']
        technical_share_weight = self.env['ir.values'].get_default('hr.appraisal.settings', 'technical_share') or 0.0
        timeline_share_weight = self.env['ir.values'].get_default('hr.appraisal.settings', 'timeline_share') or 0.0
        net_technical_weight = self.env['ir.values'].get_default('hr.appraisal.settings', 'net_technical') or 0.0
        competencies_evaluation_weight = self.env['ir.values'].get_default('hr.appraisal.settings', 'competencies_evaluation') or 0.0

        for rec in self:
            all_projects = self.env['project.project'].search([('is_kpi','=',True),('from_date','<=',rec.from_date),('to_date','>=',rec.to_date)])
            for project in all_projects:
                project_tasks = task_obj.search([('project_id','=',project.id)])
                technical_share_score += sum(task.weighted_score for task in project_tasks)
                timeline_share_score += sum(task.weighted_score_deadline for task in project_tasks)


            rec.technical_share_score = technical_share_score
            rec.technical_share_net_score = (rec.technical_share_score * technical_share_weight)/100.0
            rec.timeline_share_score = timeline_share_score
            rec.timeline_share_net_score = (rec.timeline_share_score * timeline_share_weight)/100.0
            rec.net_technical_net_score = (rec.technical_share_net_score + rec.timeline_share_net_score) *(net_technical_weight/100)
            competencies_evaluation_score = sum(core.score for core in rec.core_competencies_ids)
            rec.competencies_evaluation_net_score = (competencies_evaluation_weight / 100.0) *(competencies_evaluation_score)
            rec.employee_self_performance_appraisal_score = rec.competencies_evaluation_net_score + rec.net_technical_net_score
            rec.employee_self_performance_appraisal = "<table style = 'height: 152px; width: 100%;' class='table table-bordered'>" \
                                                      "<tbody>" \
                                                      "<tr><td style = 'width: 195.75px; text-align: center;' bgcolor='#000000'><span style='color:#ffffff'><strong> Item </strong></span></td>" \
                                                      "<td style = 'width: 76.25px; text-align: center;' bgcolor='#000000'><span style='color:#ffffff'> <strong>Weight </strong></span></td>" \
                                                      "<td style = 'width: 136px; text-align: center;' bgcolor='#000000'><span style='color:#ffffff'> <strong>Item score </strong></span></td>" \
                                                      "<td style = 'width: 136px; text-align: center;' bgcolor='#000000'><span style='color:#ffffff'><strong> Net score </strong></span></td>\
                                                      </tr><tr>" \
                                                      "<td style = 'width: 195.75px;'><span style='color:#000000'><strong>Technical Share </strong></span> </td>" \
                                                      "<td style = 'width: 76.25px;'><center><strong>"+str(technical_share_weight)+"%</strong></center></td>" \
                                                      "<td style = 'width: 136px;'><center><strong>"+str(round(rec.technical_share_score,2))+"</strong></center> </td>" \
                                                      "<td style = 'width: 136px;'><center><strong>"+str(round(rec.technical_share_net_score,2))+"%</strong></center></td>" \
                                                      "</tr><tr>" \
                                                      "<td style = 'width: 195.75px;'><span style='color:#000000'><strong> Timeline share</strong></span> </td>" \
                                                      "<td style = 'width: 76.25px;'><center>"+str(timeline_share_weight)+"%</strong></center></td>" \
                                                      "<td style = 'width: 136px;'><center>"+str(round(rec.timeline_share_score,2))+"</strong></center> </td>" \
                                                      "<td style = 'width: 136px;'><center>"+str(round(rec.timeline_share_net_score,2))+"%</strong></center></td>" \
                                                      "</tr><tr>" \
                                                      "<td style = 'width: 195.75px;'> <span style='color:#000000'><strong>Net Technical </td></strong></span>" \
                                                      "<td style = 'width: 76.25px;'><center><strong>"+str(net_technical_weight)+"</strong></center></td>" \
                                                      "<td style = 'width: 136px;'><center></center> </td>" \
                                                      "<td style = 'width: 136px;'><center><strong>"+str(round(rec.net_technical_net_score,2))+"%</strong></center></td>" \
                                                      "</tr><tr>" \
                                                          "<td style = 'width: 195.75px;'> <span style='color:#000000'><strong>Competencies Evaluation </strong></span></td>" \
                                                      "<td style = 'width: 76.25px;'><center><strong>"+str(competencies_evaluation_weight)+"%</strong></center></td>" \
                                                      "<td style = 'width: 136px;'><center><strong>"+str(round(competencies_evaluation_score,2))+"</strong></center> </td>" \
                                                      "<td style = 'width: 136px;'><center><strong>"+str(round(rec.competencies_evaluation_net_score,2))+"%</strong></center></td>" \
                                                      "</tr></tbody></table>" \
                                                      "<table style='height: 26px; width: 100%;' class='table table-bordered' ><tbody><tr>" \
                                                      "<td style='width: 835.45px; text-align: center;' bgcolor='#000000'><span style='color:#ffffff'>Value of employee pefromance apprasial</span></td>" \
                                                      "<td style='width: 291.55px; text-align: center;' bgcolor='#000000'><center><span style='color:#ffffff'>"+str(round(rec.employee_self_performance_appraisal_score,2))+"</span></center></td></tr>" \
                                                      "</tbody></table>"




    @api.constrains('self_share','team_share')
    def _check_supervisory_level_share(self):
        for rec in self:
            if rec.self_share and rec.team_share:
                if rec.self_share + rec.team_share != 100.0:
                    raise ValidationError(_("Sorry .. Total of supervisory level shares must equal 100%"))

    @api.multi
    @api.onchange('employee_id')
    def show_competencies(self):
        for rec in self:
            if rec.employee_id:
                rec.show = True

    @api.multi
    @api.depends('core_competencies_ids')
    def get_competencies_res(self):
        for rec in self:
            if rec.core_competencies_ids:
                total_score = sum(core_obj.score for core_obj in rec.core_competencies_ids)
                res = self.env['core.competencies.res.conf'].search([('percentage','<=',total_score)],order='percentage desc',limit=1)
                if res:
                    rec.final_res_competencies = '<span>' \
                                                 '<font style="font-size: 27px;color: red;">'+res.description+'</font><br/><font style="font-size: 39px;">'+str(total_score)+'%</font></span>'

    @api.multi
    @api.onchange('show')
    def get_core_competencies_ids(self):
        for rec in self:
            objs = self.env['core.competencies.conf'].search([])
            core_arr = []
            for obj in objs:
                core_arr.append((0,0,{'title':obj.title,
                                      'description':obj.description,
                                      'percentage':obj.percentage}))

            rec.core_competencies_ids = core_arr
