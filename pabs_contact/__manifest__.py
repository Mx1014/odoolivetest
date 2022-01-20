# -*- coding: utf-8 -*-
{
    'name': "pabs_contact",

    'author': "Pro Advisory",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Contact',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','base_address_city','base_address_extended','account','purchase','stock', 'account_reports'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/stock_picking_form_view.xml',
        'views/stock_picking_tree_view.xml',
        # 'data/contact_data.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'auto_install': True,
}
