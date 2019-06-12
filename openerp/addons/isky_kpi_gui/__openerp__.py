# -*- coding: utf-8 -*-
{
    'name': "iSky KPI GUI",
    'summary': "iSky KPI GUI",
    'author': "iSky Development Team",
    'description': """
iSky HR KPI GUI
====================================
    """,
    'website': "http://www.iskydev.com",
    'depends': [
        'base',
        'isky_highchart_libs',
        'isky_hr_kpi'
    ],
    'data': [
        'views/resources.xml',
        'views/isky_menu_items_view.xml',
    ],
    'demo': [

    ],

    'qweb': [
        'static/src/xml/isky_kpi_gui.xml',
        'static/src/xml/isky_emp_gui.xml',
    ],

    'installable': True,
}
