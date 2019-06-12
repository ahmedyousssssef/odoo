# -*- coding: utf-8 -*-
from openerp import api, fields, models, _


class hr_job(models.Model):
    _inherit = 'hr.job'

    sub_state = fields.Selection([('hiring_request', 'Hiring Request'), ('hr_review', 'HR Review')
                                     , ('ceo_approved', 'CEO Approved'), ('job_posted', 'Vacancies Posted')
                                     , ('receiving_cvs', 'Receiving CVs'), ('cv_categorization', 'CV Categorization')],
                                 string='Sub Status', readonly=True, required=True,
                                 track_visibility='always', copy=False,
                                 help="Set Status Of this job position.", default='hiring_request')
    duties = fields.Text(_('Duties'))
    salary_range = fields.Char(_('Salary Range'))
    compensations = fields.Char(_('Compensations'))

    # states Dates Fields
    recruitment_progress_date = fields.Datetime(string='Recruitment Progress Date', )
    hiring_request_date = fields.Datetime(string='Hiring Request Date', )
    hr_review_date = fields.Datetime(string='HR Review Date')
    ceo_approval_date = fields.Datetime(string='CEO Approval Date')
    job_posted_date = fields.Datetime(string='Vacancies Posted Date')
    receiving_cvs_date = fields.Datetime(string='Receiving CVs Date')
    cv_categorization_date = fields.Datetime(string='CV Categorization Date')
    recruitment_closing_date = fields.Datetime(string='Recruitment Closing Date')

    qualifications = fields.Text(string='Qualifications')
    cycle_closure_date = fields.Date(string='Cycle Closure Date(Expected)')
    post_media_ids = fields.Many2many('post.media', string='Post Media', )

    total_received_cvs = fields.Integer(string='Total No. Received CVs')
    total_accepted_cvs = fields.Integer(string='Total No. Accepted CVs')
    total_rejected_cvs = fields.Integer(string='Total No. Rejected CVs')
    total_fit_cvs = fields.Integer(string='Total No. Fit Another Position CVs')

    job_family = fields.Many2one('employee.job.family', string='Job Family')
    section = fields.Many2one('employee.section', string='Section')
    unit = fields.Many2one('employee.unit', string='Unit')

    @api.one
    def hr_review(self):
        self.write({'sub_state': 'hr_review', 'hr_review_date': fields.Datetime.now()})
        recruitment_state_log_obj = self.env['recruitment.state.log']
        recruitment_state_log_obj.create(
            {'name': self.name, 'department_id': self.department_id.id or False, 'user_id': self.user_id.id or False,
             'no_of_recruitment': self.no_of_recruitment, 'state': 'HR Review', 'date': fields.Datetime.now()})

    @api.one
    def ceo_approved(self):
        self.write({'sub_state': 'ceo_approved', 'ceo_approval_date': fields.Datetime.now()})
        recruitment_state_log_obj = self.env['recruitment.state.log']
        recruitment_state_log_obj.create(
            {'name': self.name, 'department_id': self.department_id.id or False, 'user_id': self.user_id.id or False,
             'no_of_recruitment': self.no_of_recruitment, 'state': 'CEO Approved', 'date': fields.Datetime.now()})

    @api.one
    def job_posted(self):
        self.write({'sub_state': 'job_posted', 'job_posted_date': fields.Datetime.now()})
        recruitment_state_log_obj = self.env['recruitment.state.log']
        recruitment_state_log_obj.create(
            {'name': self.name, 'department_id': self.department_id.id or False, 'user_id': self.user_id.id or False,
             'no_of_recruitment': self.no_of_recruitment, 'state': 'Vacancies Posted', 'date': fields.Datetime.now()})

    @api.one
    def receiving_cvs(self):
        self.write({'sub_state': 'receiving_cvs', 'receiving_cvs_date': fields.Datetime.now()})
        recruitment_state_log_obj = self.env['recruitment.state.log']
        recruitment_state_log_obj.create(
            {'name': self.name, 'department_id': self.department_id.id or False, 'user_id': self.user_id.id or False,
             'no_of_recruitment': self.no_of_recruitment, 'state': 'Receiving CVs', 'date': fields.Datetime.now()})

    @api.one
    def cv_categorization(self):
        self.write({'sub_state': 'cv_categorization', 'cv_categorization_date': fields.Datetime.now()})
        recruitment_state_log_obj = self.env['recruitment.state.log']
        recruitment_state_log_obj.create(
            {'name': self.name, 'department_id': self.department_id.id or False, 'user_id': self.user_id.id or False,
             'no_of_recruitment': self.no_of_recruitment, 'state': 'CV Categorization', 'date': fields.Datetime.now()})

    # set substate and initializing states dates
    @api.multi
    def set_recruit(self):
        for record in self:
            no_of_recruitment = record.no_of_recruitment == 0 and 1 or record.no_of_recruitment
            record.write(
                {'state': 'recruit', 'no_of_recruitment': no_of_recruitment, 'sub_state': 'hiring_request',
                 'recruitment_progress_date': fields.Datetime.now(),
                 'hiring_request_date': fields.Datetime.now(), 'hr_review_date': False,
                 'ceo_approval_date': False, 'job_posted_date': False, 'receiving_cvs_date': False,
                 'cv_categorization_date': False, 'recruitment_closing_date': False})
            recruitment_state_log_obj = self.env['recruitment.state.log']
            recruitment_state_log_obj.create(
                {'name': record.name, 'department_id': record.department_id.id or False, 'user_id': record.user_id.id or False,
                 'no_of_recruitment': record.no_of_recruitment, 'state': 'HR Review', 'date': fields.Datetime.now()})
            recruitment_state_log_obj.create(
                {'name': record.name, 'department_id': record.department_id.id or False, 'user_id': record.user_id.id or False,
                 'no_of_recruitment': record.no_of_recruitment, 'state': 'Recruitment in Progress',
                 'date': fields.Datetime.now()})

        return True

    @api.multi
    def set_open(self):
        for record in self:
            record.write({
                'state': 'open',
                'recruitment_closing_date': fields.Datetime.now(),
                'no_of_recruitment': 0,
                'no_of_hired_employee': 0
            })
            recruitment_state_log_obj = self.env['recruitment.state.log']
            recruitment_state_log_obj.create(
                {'name': record.name, 'department_id': record.department_id.id or False, 'user_id': record.user_id.id or False,
                 'no_of_recruitment': record.no_of_recruitment, 'state': 'Recruitment Closed', 'date': fields.Datetime.now()})
        return True

    @api.model
    def create(self, values):
        values.update({
            'recruitment_progress_date': fields.Datetime.now(),
            'hiring_request_date': fields.Datetime.now(),
        })
        recruitment_state_log_obj = self.env['recruitment.state.log']
        recruitment_state_log_obj.create(
            {'name': values.get('name'), 'department_id': values.get('department_id'), 'user_id': values.get('user_id'),
             'no_of_recruitment': values.get('no_of_recruitment'), 'state': 'Recruitment in Progress',
             'date': values.get('recruitment_progress_date')})
        recruitment_state_log_obj.create(
            {'name': values.get('name'), 'department_id': values.get('department_id'), 'user_id': values.get('user_id'),
             'no_of_recruitment': values.get('no_of_recruitment'), 'state': 'Hiring Request',
             'date': values.get('hiring_request_date')})

        return super(hr_job, self.with_context(mail_create_nosubscribe=True)).create(values)


class post_media(models.Model):
    _name = 'post.media'

    name = fields.Char(string='Name', required=True)
