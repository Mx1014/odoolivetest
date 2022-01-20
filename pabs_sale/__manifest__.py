# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Pabs: sales',
    'category': 'Pabs',
    'summary': 'Sales Customization',
    'version': '1.0',
    'description': """Customization of Sales module as per requirement.""",
    'depends': [
        'sale_management',
        'sale_stock',
        'account_accountant',
        'sale_margin',
        'purchase'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/account_payment_term_views.xml',
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml',
        'views/payment_views.xml',
        'views/product_template_views.xml',
        'views/account_move_views.xml',
        'views/stock_picking_views.xml',
        'views/sale_terminal_views.xml',
        'views/account_user_statement_views.xml',
        'views/account_bank_statement_views.xml',
        'views/sale_order_mail_template.xml',
        'views/ir_sequence.xml',
        'views/pabs_sale_template.xml',
        'views/journal_views.xml',
        'views/statement_voucher.xml',
        'wizard/cheque_update_form.xml'
    ],
    # 'qweb': [
    #     'static/src/xml/kanban_button.xml',
    # ],
    'installable': True,
    'auto_install': True,
}
