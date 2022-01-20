# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Inventory Forecast',
    'version': '1.1',
    'summary': 'Forecast',
    'description': "",
    'depends': ['product', 'sale', 'sale_stock', 'purchase_stock', 'mrp', 'stock_account'],
    'category': 'Inventory/Inventory',
    'sequence': 25,
    'data': [
        'views/stock_template.xml',
        'report/report_stock_forecasted.xml',
        'views/stock_picking_views.xml',
        'wizard/product_replenish_views.xml',
        'wizard/stock_orderpoint_snooze_views.xml',
        'views/stock_orderpoint_views.xml',
        'report/report_stock_forecasted_stock_account.xml',
        'report/report_stock_forecasted_sale_stock.xml',
        'report/report_stock_forecasted_purchase_stock.xml',
        'report/report_stock_forecasted_mrp.xml',

    ],
    'qweb': [
        'static/src/xml/popover_widget.xml',
        'static/src/xml/forecast_widget.xml',
        'static/src/xml/report_stock_forecasted.xml',
        'static/src/xml/stock_orderpoint.xml',
        'static/src/xml/qty_at_date.xml',
    ],

}
