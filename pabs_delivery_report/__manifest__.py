# -*- coding: utf-8 -*-
{
    'name': "Delivery Report",

    'summary': """
        This module created a new delivery report in transfers""",

    'description': """
        This module created a new delivery report in transfers
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'pabs_base', 'pabs_logistics_extra', 'stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/picking_client_action.xml',
        # 'views/templates.xml',
        'data/report_paperformat.xml',
        'reports/stock_picking_view.xml',
        'reports/report_delivery_note.xml',
        'views/stock_picking_batch_form.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
