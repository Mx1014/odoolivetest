# -*- coding: utf-8 -*-
{
    'name': "Bahrain VAT Reports",

    'summary': """
        VAT Report Designer""",

    'author': "Saleh Alqebaiti",
    'website': "http://www.proadvisory.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','sale','sale_management'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/temp_custom.xml',
        'views/views.xml',
    ],

}
