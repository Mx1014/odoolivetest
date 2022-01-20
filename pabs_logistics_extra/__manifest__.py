# -*- coding: utf-8 -*-
{
    'name': "pabs_logistics_extra",


    'author': "ProAdvisory Business Solution",
    'website': "http://www.proadvisory.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_management', 'stock', 'sale_stock', 'stock_picking_batch', 'account_accountant',
                'fleet', 'pabs_sale', 'pabs_sale_extra', 'hr', 'mrp', 'purchase', 'contacts',
                'account', 'pabs_contact', 'pabs_base'],
    # 'planning',
    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/stock_picking_type_view.xml',
        'views/stock_immediate_transfer_views.xml',
        'wizards/delivery_reminder.xml',
        'wizards/shift_plan_calendar_inventory.xml',
        'wizards/shift_plan_calendar.xml',
        'wizards/plan_calendar.xml',
        'views/views.xml',
        'views/sequence.xml',
        'views/logistics_team_views.xml',
        'views/team_contract_view.xml',
        'views/remove_add_to_batch_action_menu_item.xml',
        'wizards/plan_calendar_transfer.xml',
        'wizards/shift_plan_calendar_transfer.xml',
        'views/sale_order_views.xml',
        'views/stock_picking.xml',
        'views/stock_picking_batch_form.xml',
        'views/res_partner_inherit.xml',
        'views/view_employee_form_inherit.xml',
        'views/stock_picking_tree_view.xml',
        'views/res_users_view.xml',
        'views/menu_items.xml',
        'views/product.xml',
        'views/purchase_order.xml',
        'views/purchase_order_tree.xml',
        'views/slot_creator_automation.xml',
        'views/warehouse_orderpoint_views.xml',
        'views/purchase_confirm_automation.xml',
        'views/account_move.xml',
        'views/stock_location_view.xml',
        'wizards/stock_picking_batch_confirm_done.xml',
        'wizards/stock_backorder_confirmation_views_inherit.xml',
        'wizards/stock_picking_return_view.xml',
        'static/src/xml/assets.xml',

        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': ['demo/demo.xml'],
    'qweb': ['static/src/xml/popover_widget.xml',
             'static/src/xml/stock_orderpoint.xml',
             'static/src/xml/add_to_batch_button.xml'],
    'auto_install': True,
}
# 'static/src/xml/add_to_batch_button.xml'