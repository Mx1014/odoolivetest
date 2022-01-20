# -*- coding: utf-8 -*-
{
    'name': "pabs_tags",

    'summary': "print offer template",

    'description': """
       customization to print for the offers templates
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        # 'views/pabs_tags_js.xml',
        'views/product_attribute_category.xml',
        'wizard/make_printable.xml',
        'views/product_template_inherit.xml',
        'data/report_paperformat.xml',
        'views/report_offer_large.xml',
        'views/report_tag_price_meduim.xml',
        'views/report_price_tag_small.xml',
        'views/report_tag_price_large.xml',
        'reports/report_tag_price_meduim_template.xml',
        'reports/report_offer_large_template.xml',
        'reports/report_tag_price_large_template.xml',
        'reports/report_price_tag_small_template.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
