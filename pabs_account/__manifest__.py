# -*- coding: utf-8 -*-
{
    'name': "Pabs Account",

    'author': "Saleh Alqebaiti",
    'website': "http://www.proadvisory.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale', 'purchase', 'sale_management', 'account_analytic_default', 'pabs_sale_extra',
                'account_reports', 'account_followup', 'pabs_warranty', 'pabs_fleet'],

    # always loaded
    'data': [
        'data/report_paperformat.xml',
        'security/ir.model.access.csv',
        'views/temp_custom.xml',
        'views/vat_report_inherit.xml',
        'views/followup_report.xml',
        'views/report_invoice_doc_matrix.xml',
        'views/report_invoice_matrix.xml',
        'views/report_invoice_call_matrix.xml',
        'views/views.xml',
	'views/invoice_report.xml',
        'data/data.xml',
       # 'wizard/payment_specific_view.xml'
    ],

    # 'qweb': [
    #     'static/src/xml/account_payment.xml'
    # ],

}
