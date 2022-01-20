# -*- coding: utf-8 -*-
{
    'name': "Pabs: Sale Extra",

    'author': "Pro Advisory",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'sales_team', 'sale_stock', 'account', 'pabs_sale', 'account_batch_payment'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/report_paperformat.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/product_view.xml',
        'views/sales_team_views.xml',
        'views/view_batch_payment.xml',
        'views/terminal.xml',
        'views/statement_payment_method_views.xml',
        'views/account.xml',
        'views/client_action.xml',
        'views/statement_deposit.xml',
        'reports/report_closing.xml',
        'reports/report_closing_template.xml',
        'reports/sales_ticket_report.xml',
        'reports/sales_ticket_template.xml',
        'reports/report_deposit_voucher.xml',
        'reports/report_cash_deposit.xml',
        'reports/report_deposit_voucher_template.xml',
        'reports/report_cash_deposit_template.xml',
        'reports/report_cashier_invoices.xml',
        'reports/report_cashier_invoices_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
