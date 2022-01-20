# -*- coding: utf-8 -*-
{
    'name': "Online Booking",

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_stock', 'sale', 'pabs_logistics_extra', 'portal', 'web', 'web_editor', 'pabs_sale_quotation'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/portal_template.xml',
        'views/assets.xml',
        'views/calendar_portal.xml',
        'reports/sale_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

}
