# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    """
    def _assign_picking_post_process(self, new=False):
        super(StockMove, self)._assign_picking_post_process(new=new)
        if new:
            picking_id = self.mapped('picking_id')
            # automatically validate delivery if sale order type is Cash Memo and if it has no tracking
            if picking_id and picking_id.sale_id.sale_order_type == 'cash_memo' and not picking_id.has_tracking:
                picking_id.action_assign()
                for move in picking_id.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                    for move_line in move.move_line_ids:
                        move_line.qty_done = move_line.product_uom_qty
                    if not move.move_line_ids:
                        move.quantity_done = move.product_uom_qty
                picking_id.action_done()
                                   """

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        vals['sale_order_type'] = self.sale_line_id.order_id.sale_order_type
        return vals
