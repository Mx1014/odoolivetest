# -*- coding: utf-8 -*-
{
    'name': "pabs_task",

    'author': "Pro Advisory",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    # 'category': 'Contact',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase_stock', 'sale_timesheet', 'account', 'purchase', 'sale', 'web_gantt', 'pabs_logistics_extra', 'project', 'pabs_invoicing'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/security.xml',
        'views/views.xml',
        # 'views/report_purchase_order.xml',
        # 'views/report_progress_order.xml',
        # 'views/report_invoice.xml',
        'views/done_dn_view.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
