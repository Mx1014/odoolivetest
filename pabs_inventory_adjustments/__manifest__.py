# -*- coding: utf-8 -*-
{
    'name': "pabs:Inventory Adjustments",

    'summary': "print inventory adjustments template",

    'description': """
       customization to print for the inventory adjustments templates
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        'data/mail_activity_data.xml',
        'reports/inventory_adjustments.xml',
        'views/view_inventory_form.xml',
    ],
    'qweb': [
        'static/src/xml/barcode_template.xml',
    ],
}
