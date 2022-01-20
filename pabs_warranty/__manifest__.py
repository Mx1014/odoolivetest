{
    'name': "pabs_warranty",

    'author': "Pro Advisory",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    # 'category': 'purchase',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'product_brand', 'pabs_logistics_extra'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/extended_product.xml',
        'views/views.xml',
        'views/allow_product_warranty.xml',
        'views/allow_product_variant_warranty.xml',
        'views/extended_warranty.xml',
        'views/sale_order_line.xml',
        'views/extended_warranty_form.xml',
    ],

}
