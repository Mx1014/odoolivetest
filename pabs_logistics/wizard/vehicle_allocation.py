# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import Warning


class VehicleAllocationWizard(models.TransientModel):
    _name = 'vehicle.allocation.wizard'
    _description = "Vehicle Allocation Wizard"

    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    picking_ids = fields.Many2many('stock.picking', string="Delivery Lines")
    picking_type_id = fields.Many2one('stock.picking.type', string="Picking Type")
    slot_allocation_time_id = fields.Many2one('slot.allocation.time', string="Slot Allocation Time")
    delivery_qty = fields.Float('Delivery Qty')
    remaining_qty = fields.Float('Remaining Qty')

    @api.onchange('fleet_vehicle_id', 'slot_allocation_time_id', 'picking_type_id')
    def onchange_fleet_vehicle_id(self):
        if not self.fleet_vehicle_id:
            return {}
        # slot_allocation_vehicle = self.env['slot.allocation.vehicle'].search([('slot_allocation_time_id', '=', self.slot_allocation_time_id.id), ('fleet_vehicle_id', '=', self.fleet_vehicle_id.id), ('picking_type_id', '=', self.picking_type_id.id)])
        stock_picking = self.env['stock.picking'].search([('slot_allocation_time_id', '=', self.slot_allocation_time_id.id), ('fleet_vehicle_id', '=', self.fleet_vehicle_id.id), ('picking_type_id', '=', self.picking_type_id.id)])
        remaining_qty = self.fleet_vehicle_id.capacity_qty - sum(stock_picking.mapped('move_ids_without_package.product_uom_qty'))
        if self.fleet_vehicle_id and self.delivery_qty > remaining_qty or remaining_qty < 1:
            raise Warning(_("""
                        you can not deliver qty on this vehicle your vehicle is full:
                        \n Your Vehicle Capacity Qty: \t %s
                        \n Remaining Qty: \t %s
                        \n You want to Deliver Qty: \t %s""" % (self.fleet_vehicle_id.capacity_qty, remaining_qty, self.delivery_qty)))
        self.remaining_qty = remaining_qty

    @api.onchange('picking_ids')
    def onchange_picking_ids(self):
        self.delivery_qty = sum(self.picking_ids.mapped('move_ids_without_package.product_uom_qty'))

    def action_assing_vehicle_allocation(self):
        self.ensure_one()
        if self.fleet_vehicle_id:
            self.picking_ids.write({'fleet_vehicle_id': self.fleet_vehicle_id.id})
