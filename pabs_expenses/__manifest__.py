# -*- coding: utf-8 -*-
{
    'name': "pabs_expenses",

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr_expense', 'account', 'hr_payroll'],

    # always loaded
    'data': [
          'security/ir.model.access.csv',
          'views/views.xml',
        # 'views/user_view.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
