# -*- encoding: utf-8 -*-
{
    'name': 'Access Rights',
    'summary': 'Access Rights',
    'description': '''
           In this module add access rights for sky heights.
    ''',
    'author': 'iSky Development Team',
    'website': 'www.iskydev.com',
    'depends': ['sky_height',
                'sale', 'crm', 'sales_team', 'isky_employee_custody','account', 'isky_kpi_gui', 'product', 'base', 'analytic', 'mail', 'isky_kpi_gui', 'payment'],

    'data': [

        'security/access_rights_security_view.xml',
        'security/ir.model.access.csv',
        'views/inherited_views.xml',
        'views/menuitems.xml',
    ],

    'installable': True,
    'auto_install': False,
}
