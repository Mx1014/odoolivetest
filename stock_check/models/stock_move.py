# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from collections import defaultdict
from datetime import datetime
from itertools import groupby
from operator import itemgetter
from re import findall as regex_findall
from re import split as regex_split

from dateutil import relativedelta

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_is_zero, float_repr, float_round
from odoo.tools.misc import format_date, OrderedSet

PROCUREMENT_PRIORITIES = [('0', 'Normal'), ('1', 'Urgent')]


class StockMove(models.Model):
    _inherit = "stock.move"

    forecast_availability = fields.Float('Forecast Availability', compute='_compute_forecast_information',
                                         digits='Product Unit of Measure', compute_sudo=True)
    forecast_expected_date = fields.Datetime('Forecasted Expected date', compute='_compute_forecast_information',
                                             compute_sudo=True)

    @api.depends('product_id', 'picking_type_id', 'picking_id', 'reserved_availability', 'priority', 'state',
                 'product_uom_qty', 'location_id')
    def _compute_forecast_information(self):
        """ Compute forecasted information of the related product by warehouse."""
        self.forecast_availability = False
        self.forecast_expected_date = False

        not_product_moves = self.filtered(lambda move: move.product_id.type != 'product')
        for move in not_product_moves:
            move.forecast_availability = move.product_qty

        product_moves = (self - not_product_moves)
        warehouse_by_location = {loc: loc.get_warehouse() for loc in product_moves.location_id}

        outgoing_unreserved_moves_per_warehouse = defaultdict(lambda: self.env['stock.move'])
        for move in product_moves:
            picking_type = move.picking_type_id or move.picking_id.picking_type_id
            is_unreserved = move.state in ('waiting', 'confirmed', 'partially_available')
            if picking_type.code in self._consuming_picking_types() and is_unreserved:
                outgoing_unreserved_moves_per_warehouse[warehouse_by_location[move.location_id]] |= move
            elif picking_type.code in self._consuming_picking_types():
                move.forecast_availability = move.product_uom._compute_quantity(
                    move.reserved_availability, move.product_id.uom_id, rounding_method='HALF-UP')

        for warehouse, moves in outgoing_unreserved_moves_per_warehouse.items():
            if not warehouse:  # No prediction possible if no warehouse.
                continue
            product_variant_ids = moves.product_id.ids
            wh_location_ids = [loc['id'] for loc in self.env['stock.location'].search_read(
                [('id', 'child_of', warehouse.view_location_id.id)],
                ['id'],
            )]
            ForecastedReport = self.env['report.stock_check.report_product_product_replenishment']
            forecast_lines = ForecastedReport.with_context(warehouse=warehouse.id)._get_report_lines(None,
                                                                                                     product_variant_ids,
                                                                                                     wh_location_ids)
            for move in moves:
                lines = [l for l in forecast_lines if
                         l["move_out"] == move._origin and l["replenishment_filled"] is True]
                if lines:
                    move.forecast_availability = sum(m['quantity'] for m in lines)
                    move_ins_lines = list(filter(lambda report_line: report_line['move_in'], lines))
                    if move_ins_lines:
                        expected_date = max(m['move_in'].date for m in move_ins_lines)
                        move.forecast_expected_date = expected_date


    def action_product_forecast_report(self):
        self.ensure_one()
        action = self.product_id.action_product_forecast_report()
        warehouse = self.location_id.get_warehouse()
        action['context'] = {'warehouse': warehouse.id, } if warehouse else {}
        return action

    # def _do_unreserve(self):
    #     moves_to_unreserve = OrderedSet()
    #     for move in self:
    #         if move.state == 'cancel' or (move.state == 'done' and move.scrapped):
    #             # We may have cancelled move in an open picking in a "propagate_cancel" scenario.
    #             # We may have done move in an open picking in a scrap scenario.
    #             continue
    #         elif move.state == 'done':
    #             raise UserError(_("You cannot unreserve a stock move that has been set to 'Done'."))
    #         moves_to_unreserve.add(move.id)
    #     moves_to_unreserve = self.env['stock.move'].browse(moves_to_unreserve)
    #
    #     ml_to_update, ml_to_unlink = OrderedSet(), OrderedSet()
    #     moves_not_to_recompute = OrderedSet()
    #     for ml in moves_to_unreserve.move_line_ids:
    #         if ml.qty_done:
    #             ml_to_update.add(ml.id)
    #         else:
    #             ml_to_unlink.add(ml.id)
    #             moves_not_to_recompute.add(ml.move_id.id)
    #     ml_to_update, ml_to_unlink = self.env['stock.move.line'].browse(ml_to_update), self.env['stock.move.line'].browse(ml_to_unlink)
    #     moves_not_to_recompute = self.env['stock.move'].browse(moves_not_to_recompute)
    #
    #     ml_to_update.write({'product_uom_qty': 0})
    #     ml_to_unlink.unlink()
    #     # `write` on `stock.move.line` doesn't call `_recompute_state` (unlike to `unlink`),
    #     # so it must be called for each move where no move line has been deleted.
    #     (moves_to_unreserve - moves_not_to_recompute)._recompute_state()
    #     return True

    def _get_source_document(self):
        """ Return the move's document, used by `report.stock.report_product_product_replenishment`
        and must be overrided to add more document type in the report.
        """
        self.ensure_one()
        return self.picking_id or False

    @api.model
    def _consuming_picking_types(self):
        return ['outgoing']
