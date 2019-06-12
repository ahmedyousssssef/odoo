
from openerp import http
from openerp.http import request

class DashReport(http.Controller):

    @http.route('/isky_kpi_gui/get_all_emps', type='json', auth='user')
    def get_all_emps(self):
        all_tasks = request.env['project.task'].search([('project_id','!=',False)])
        emp_data = []
        emps = []
        for task in all_tasks:
            emp_obj = request.env['hr.employee'].search([('user_id','=',task.user_id.id)])
            if emp_obj.id not in emps:
                emp_data.append({'id':emp_obj.id,'display_name':emp_obj.display_name})
                emps.append(emp_obj.id)
        return {'employees': emp_data}

    @http.route('/isky_kpi_gui/get_all_tasks', type='json', auth='user')
    def get_all_tasks(self):
        all_tasks = request.env['project.task'].search([])
        task_data = []
        for task in all_tasks:
            task_data.append({'id':task.id,'name':task.name})
        return {'tasks': task_data}

    @http.route('/isky_kpi_gui/get_date_for_each_task', type='json')
    def get_date_for_each_task(self, task_name=False, task_id=False):
        tasks_arr = []
        technical_kpi_arr = []
        deadline_arr = []
        if not task_id and not task_name:
            tasks = request.env['project.task'].search([])
            for task in tasks:
                tasks_arr.append(task.name)
                technical_kpi_arr.append(round(task.weighted_score,2))
                deadline_arr.append(round(task.weighted_score_deadline,2))
        if task_id:
            task_obj = request.env['project.task'].browse(int(task_id))
            tasks_arr.append(task_obj.name)
            technical_kpi_arr.append(round(task_obj.weighted_score,2))
            deadline_arr.append(round(task_obj.weighted_score_deadline,2))

        return {
            'tasks_arr': tasks_arr,
            'technical_kpi_arr': technical_kpi_arr,
            'deadline_arr': deadline_arr,
        }

    @http.route('/isky_kpi_gui/get_tasks_for_each_employee', type='json')
    def get_tasks_for_each_employee(self, emp_name, emp_id):
        if emp_id:
            emp_obj = request.env['hr.employee'].browse(int(emp_id))
            tasks = request.env['project.task'].search([('user_id','=',emp_obj.user_id.id)])
            return {
                'no_tasks':len(tasks)
            }

    @http.route('/isky_kpi_gui/get_date_for_each_employee', type='json')
    def get_date_for_each_employee(self, emp_name, emp_id):
        competencies_appraisal = 0.0
        if emp_id:
            emp_obj = request.env['hr.employee'].browse(int(emp_id))
            tasks = request.env['project.task'].search([('user_id','=',emp_obj.user_id.id)])
            tasks_arr = []
            technical_kpi_arr = []
            deadline_arr = []
            for task in tasks:
                tasks_arr.append(task.name)
                technical_kpi_arr.append(round(task.weighted_score,2))
                deadline_arr.append(round(task.weighted_score_deadline,2))

            subordinates_text = ''
            employee_self_performance_appraisal = ''
            appraisal = request.env['hr.appraisal'].search([('employee_id','=',int(emp_id))],order='date_close desc',limit=1)
            if len(appraisal):
                competencies_appraisal = appraisal.final_res_competencies
                if appraisal.subordinates_text:
                    subordinates_text = appraisal.subordinates_text
                    employee_self_performance_appraisal = appraisal.employee_self_performance_appraisal
            else:
                competencies_appraisal = '<span><font style="font-size: 27px;color: red;">'+'This Employee Have no appraisal till Now!!'+'.</font></span>'
        return {
            'competencies_appraisal': competencies_appraisal,
            'subordinates_text': subordinates_text,
            'employee_self_performance_appraisal': employee_self_performance_appraisal,
            'tasks_arr': tasks_arr,
            'technical_kpi_arr': technical_kpi_arr,
            'deadline_arr': deadline_arr,
        }

    @http.route('/isky_kpi_gui/get_total', type='json', auth='user')
    def get_total(self,date_from,date_to):
        technical_share = request.env['ir.values'].get_default('hr.appraisal.settings', 'technical_share') or 0.0
        timeline_share = request.env['ir.values'].get_default('hr.appraisal.settings', 'timeline_share') or 0.0
        net_technical = request.env['ir.values'].get_default('hr.appraisal.settings', 'net_technical') or 0.0
        competencies_evaluation = request.env['ir.values'].get_default('hr.appraisal.settings',
                                                                           'competencies_evaluation') or 0.0
        objectives_arr = []
        data_arr = []
        total_technical = 0
        total_deadline = 0
        objectives_arr.append('Technical KPI')
        objectives_arr.append('Deadline')
        if date_from and date_to:
            appraisals = request.env['hr.appraisal'].search([('state','!=','new')])
            all_objectives = request.env['project.project'].search([('is_kpi','=',True),('from_date','>=',date_from),('to_date','<=',date_to)])
            for objective in all_objectives:
                total_deadline += objective.deadline_objective
                total_technical += objective.technical_objective
                if objective.technical_objective or objective.deadline_objective:
                    data_arr.append({
                        'type': 'column',
                        'name': objective.display_name,
                        'data': [objective.technical_objective, objective.deadline_objective],
                        'url': '/web#id=' + str(objective.id) + '&view_type=form&model=project.project&menu_id='
                    })

        return {
            'technical_share':technical_share,
            'timeline_share':timeline_share,
            'net_technical':net_technical,
            'competencies_evaluation':competencies_evaluation,
            'total_technical': round(total_technical,2),
            'total_deadline': round(total_deadline,2),
            'total_appraisal': len(appraisals),
            'objectives_arr':objectives_arr,
            'data_arr':data_arr

        }

