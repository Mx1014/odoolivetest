# -*- coding: utf-8 -*-
{
    'name': "Down Payment",

    'author': "Pro Advisory",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sale',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale', 'pabs_sale'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/res_config_settings_views.xml',
        'wizard/sale_advance_payment_view.xml',


    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
