# -*- coding: utf-8 -*-
{
    'name': "pabs_invoicing",
    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'pabs_sale', 'pabs_downpayment', 'pabs_logistics_extra', 'pabs_repair', 'account_followup'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/web_assets.xml',
        # 'views/sale_order_views.xml',
        # 'views/payment_views.xml',
        # 'views/stock_picking_views.xml',
        #'views/picking_batch_views.xml',
        'views/templates.xml',
        'views/followup_report.xml',
        'views/partner_statement.xml',
        'wizard/payment_specific_view.xml',

    ],
    "qweb": [
        'static/src/xml/widget_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
