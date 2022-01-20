# -*- coding: utf-8 -*-
{
    'name': "pabs_payroll",

    'author': "Pro Advisory",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Payroll',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_payroll', 'hr_payroll_account', 'hr_holidays', 'odoo_report_xlsx'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/payslip_register_payment_form.xml',
        'views/views.xml',
        # 'views/report_payslip.xml',
        'views/report_transfer_payment.xml',
        # 'views/report_bonus_payslip.xml',
        # 'views/report_settlement_payslip.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
