# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class StockMove(models.Model):
    _inherit = "stock.move"

    slot_allocation_time_id = fields.Many2one('slot.allocation.time', string="Slot Allocation Time", related="sale_line_id.slot_allocation_time_id", store=True)
    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string="Deliver on Vehicle", related="picking_id.fleet_vehicle_id", store=True)

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        vals.update({'slot_allocation_time_id': self.mapped('sale_line_id.slot_allocation_time_id') and self.mapped('sale_line_id.slot_allocation_time_id').id})
        return vals
