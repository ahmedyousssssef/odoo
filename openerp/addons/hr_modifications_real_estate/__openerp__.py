# -*- coding: utf-8 -*-
{
    'name': "HR Modifications",

    'summary': "HR Real Estate Modifications",

    'description': """This Module Adds Two Tabs In in Hr Job Screen (Education ,Employment History)
    And Customize The Workflow Of This Screen And Adds Fields In Hr Applicant Screen
    (hiring_date,offer_expire_date,benfids_offerd,pro_date) And Adds Reports In Hr Applicant Screen
     Like Hiring Checklist Report And Part and Full Time Report
    """,

    'author': 'iSky Development Team',

    'depends': ['hr','hr_contract','hr_recruitment', 'hr_holidays', 'hr_payroll'],

    "data": [
        #security
        # "security/ir.model.access.csv",

        #views
        "views/hr_inherit_job_positions_view.xml",
        "views/hr_applicant_hr_inherit_view.xml",
        "views/isky_hr_employee_view.xml",
        "views/isky_recruitment_state_log_view.xml",
        "views/isky_hr_holidays_view.xml",
        "views/isky_hr_excuse_request_view.xml",
        "views/hr_automated_actions_view.xml",
        'views/isky_hr_payroll_view.xml',
        'views/isky_hr_contract_view.xml',
        "views/menu_item_view.xml",

        #reports
        "report/excuse_report_view.xml",
        "report/blue_collar_contract_report_view.xml",
        "report/acceptance_job_report_view.xml",
        "report/full_time_report_view.xml",
        "report/filing_tracker_report_view.xml",
        "report/hiring_checklist_report_view.xml",
        "report/part_time_report_view.xml",
        "report/all_reports_view.xml",

        #data
        'data/social_insurance_salary_rule.xml',
        'data/contract_cron.xml',

    ],

    'installable': True
}
