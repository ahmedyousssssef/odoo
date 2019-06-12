# -*- coding: utf-8 -*-
{
    'name': "Yodlee",
    'summary': "Yodlee Finance",
    'category': 'Accounting',
    'version': '1.0',
    'depends': ['account_online_sync'],
    'description': '''
Sync your bank feeds with Yodlee
================================

Yodlee interface.
''',
    'data': [
        'views/yodlee_views.xml',
        'views/delete_ir_model_data.xml',
    ],
    'qweb': [
        'views/yodlee_templates.xml',
    ],
    'license': 'OEEL-1',
    'post_init_hook': '_load_csv',
}
