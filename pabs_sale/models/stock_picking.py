# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sale_order_type = fields.Selection(string='Sale Order Type', readonly=True,
                                       selection=[('cash_memo', 'Cash Memo'), ('credit_sale', 'Credit Sale'),
                                                  ('paid_on_delivery', 'Paid on Delivery'), ('advance_payment', 'Cash Invoice'), ('service', 'Service')])
    journal_id = fields.Many2one('account.journal', string='Account Journal')

    # def action_done(self):
    #     res = super(StockPicking, self).action_done()
    #
    #     for pick in self:
    #         if pick.sale_order_type != 'cash_memo':
    #             for stock_move in pick.move_lines:
    #                 journal_items = []
    #                 account_move = pick.env['account.move'].search([('stock_move_id', '=', stock_move.id)], limit=1)
    #                 # for line in stock_move.mapped('move_line_ids'):
    #                 price = 0
    #                 sale_line = stock_move.sale_line_id
    #                 product = stock_move.product_id
    #
    #                 if stock_move:
    #                     if stock_move.quantity_done != 0.0:
    #                         qty = stock_move.quantity_done
    #                     else:
    #                         qty = stock_move.reserved_availability
    #                 if sale_line:
    #                     price = sale_line.price_unit - ((sale_line.price_unit * sale_line.discount)/100)
    #
    #                 if product:
    #                     journal_items.append((0, 0, {
    #                         'account_id': product.income_account_id.id if product.income_account_id else False,
    #                         'product_id': product.id,
    #                         'credit': price * qty,
    #                         'partner_id': pick.partner_id.id if pick.partner_id else False,
    #                         'name': product.display_name,
    #                     }))
    #                     journal_items.append((0, 0, {
    #                         'account_id': product.property_account_income_id.id if product.property_account_income_id else False,
    #                         'product_id': product.id,
    #                         'debit': price * qty,
    #                         'partner_id': pick.partner_id.id if pick.partner_id else False,
    #                         'name': product.display_name,
    #                     }))
    #
    #                 account_move.write({
    #                     'line_ids': journal_items
    #                 })
    #
    #     return res

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for picking in self.move_ids_without_package:
            if picking.quantity_done > picking.product_uom_qty:
                raise UserError(_('You Cannot add quantity done more than demand quantity'))
        return res
