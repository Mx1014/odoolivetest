# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Pabs: Logistics',
    'summary': 'Pabs: Logistics',
    'sequence': 100,
    'license': 'OEEL-1',
    'website': 'https://www.odoo.com',
    'version': '1.0',
    'author': 'Tiny Erp Pvt.Ltd',
    'description': """
Pabs: Logistics
===============
    """,
    'category': 'Custom Development',
    'depends': ['sale_management', 'stock', 'sale_stock', 'stock_picking_batch', 'account_accountant', 'fleet', 'pabs_sale'],
    'data': [
        'security/ir.model.access.csv',

        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
        'views/slot_views.xml',
        'views/fleet_views.xml',
        'views/slot_vehicle_views.xml',
        'views/stock_picking_batch_views.xml',
        # wizard
        'wizard/vehicle_allocation.xml',
        'wizard/slot_create_allocation.xml',
        'wizard/stock_picking_to_batch_views.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
