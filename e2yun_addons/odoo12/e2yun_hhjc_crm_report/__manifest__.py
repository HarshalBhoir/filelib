# -*- coding: utf-8 -*-
{
    'name': 'E2yun HHJC CRM Report',
    'version': '12.0.0.1',
    'sequence': '10',
    'category': 'base',
    'depends': ['base','web','crm','e2yun_crm_warehouse'],
    'author': 'liqiang',
    'website': 'http://e2yun.cn',
    'summary': 'E2yun HHJC CRM Report',
    'description': """E2yun HHJC CRM Report""",
    'data': [
        'views/customer_loss_view.xml',
        'views/stock_query.xml',
        'views/credit_query_view.xml'
    ],
    'qweb': [
        'static/src/xml/customer_loss_template.xml',
        'static/src/xml/tree_button_template.xml',
             ],
    'installable': True,
    'auto_install': False,
}
