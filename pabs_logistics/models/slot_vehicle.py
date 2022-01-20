# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class SlotAllocationVehicle(models.Model):
    _name = "slot.allocation.vehicle"
    _description = "Slot Allocation Vehicle"

    picking_id = fields.Many2one('stock.picking', string='Picking')
    slot_allocation_time_id = fields.Many2one('slot.allocation.time', string="Slot Allocation Time", related="picking_id.slot_allocation_time_id")
    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string="Deliver on Vehicle", related="picking_id.fleet_vehicle_id")
    picking_type_id = fields.Many2one('stock.picking.type', string='Picking Type', related="picking_id.picking_type_id")
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    deliver_qty = fields.Float('Deliver Qty', compute='_compute_delivery_qty')

    def _compute_delivery_qty(self):
        for rec in self:
            rec.deliver_qty = sum(rec.picking_id.move_ids_without_package.mapped('product_uom_qty'))
