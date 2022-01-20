# -*- coding: utf-8 -*-

{
    'name': 'Reason of Return - Transfer',
    'category': 'Operations/Inventory',
    'summary': 'Asks about the return reason of the orders.',
    'description': """Asks about the return reason of the orders.""",
    'version': '1.0',
    'depends': ['stock', 'mail', 'stock_picking_batch', 'pabs_logistics_extra', 'pabs_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
        'views/stock_return_reason_views.xml',
        'views/stock_return_picking_views.xml',
        'views/stock_picking_type_views.xml',
        'views/main_menus.xml',
    ],
    'installable': True,
}
