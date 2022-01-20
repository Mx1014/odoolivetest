# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning


class StockPickingToBatch(models.TransientModel):
    _inherit = 'stock.picking.to.batch'

    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    picking_ids = fields.Many2many('stock.picking', string="Delivery Lines")
    picking_type_id = fields.Many2one('stock.picking.type', string="Picking Type")
    slot_allocation_time_id = fields.Many2one('slot.allocation.time', string="Slot Allocation Time")
    delivery_qty = fields.Float('Delivery Qty')
    remaining_qty = fields.Float('Remaining Qty')

    @api.model
    def default_get(self, fields):
        result = super(StockPickingToBatch, self).default_get(fields)
        result['picking_ids'] = self.env.context.get('active_ids')
        return result

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
        picking_ids = self.picking_ids
        if picking_ids and len(picking_ids.mapped('picking_type_id')) == 1 and len(picking_ids.mapped('slot_allocation_time_id')) == 1:
            self.picking_type_id = picking_ids.mapped('picking_type_id').id,
            self.slot_allocation_time_id = picking_ids.mapped('slot_allocation_time_id').id
            self.delivery_qty = sum(picking_ids.mapped('move_ids_without_package.product_uom_qty'))
        else:
            raise Warning(_('you can not deliver for multi picking type and multi slot time in single vehicle'))

    def assing_vehicle_allocation(self):
        self.ensure_one()
        if self.fleet_vehicle_id:
            self.picking_ids.write({'fleet_vehicle_id': self.fleet_vehicle_id.id})
        if self.batch_id:
            values = {'fleet_vehicle_id': self.fleet_vehicle_id.id, 'picking_type_id': self.picking_type_id.id, 'slot_allocation_time_id': self.slot_allocation_time_id.id}
            self.batch_id.write(values)

    def attach_pickings(self):
        # use active_ids to add picking line to the selected batch
        self.ensure_one()
        self.assing_vehicle_allocation()
        return super(StockPickingToBatch, self).attach_pickings()
