# -*- coding: utf-8 -*-
{
    'name': "pabs_base",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly

    'depends': ['base', 'pabs_product', 'account', 'stock', 'purchase'],


    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/logistics_groups.xml',
        'security/accounting_groups.xml',
        'security/purchase_groups.xml',
        'security/service_groups.xml',
        'security/marketing_groups.xml',
        'security/sales_groups.xml',
        'security/warehouse_groups.xml',

        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
