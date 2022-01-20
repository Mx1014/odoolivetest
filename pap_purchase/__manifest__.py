{
    'name': "pabs_purchase",

    'author': "Pro Advisory",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    # 'category': 'purchase',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase', 'purchase_stock', 'stock'],

    # always loaded
    'data': [
        'data/report_paperformat.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/purchase_agrement.xml',
        'reports/purchase_order_report_template.xml',
        'reports/quotation_order_template.xml',
        'reports/purchase_report.xml',
        'reports/purchase_agrement_report.xml',
    ],

}
