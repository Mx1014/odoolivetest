# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    picking_type_id = fields.Many2one('stock.picking.type', string="LOB")
    slot_allocation_time_id = fields.Many2one('slot.allocation.time', string="Slot Allocation Time")
    delivery_qty = fields.Float('Delivery Qty', compute='_compute_delivery_qty')
    remaining_qty = fields.Float('Remaining Qty')
    trip_sheet_date = fields.Date(string="Trip Sheet Date", related="slot_allocation_time_id.date")
    delivery_slot = fields.Selection(string="Delivery Slot", related="slot_allocation_time_id.time_zone")
    vendor_name = fields.Many2one('res.partner')
    technician_name = fields.Many2one('res.partner')
    # fleet_vehicle_ids = fields.Many2many('fleet.vehicle', compute="_get_available_vehicle")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In progress'),
        ('loading', 'Loading'),
        ('out_for_delivery', 'Out for Delivery'),
        ('returned', 'To be Reviewed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], default='draft',
        copy=False, tracking=True, required=True, readonly=True)

    @api.model
    def create(self, vals):
        record = super(StockPickingBatch, self).create(vals)
        if record.fleet_vehicle_id:
            record.picking_ids.fleet_vehicle_id = record.fleet_vehicle_id.id
        return record

    def write(self, vals):
        if 'fleet_vehicle_id' in vals:
            self.picking_ids.fleet_vehicle_id = vals.get('fleet_vehicle_id')
        return super(StockPickingBatch, self).write(vals)

    # @api.depends('picking_ids.batch_id', 'slot_allocation_time_id', 'picking_type_id')
    # def _compute_available_vehicle(self):
    #     for rec in self:
    #         stock_picking = self.env['stock.move'].search([('slot_allocation_time_id', '=', rec.slot_allocation_time_id.id), ('picking_id.fleet_vehicle_id', '!=', False)])
    #         self.fleet_vehicle_id.capacity_qty - sum(stock_picking.mapped('move_ids_without_package.product_uom_qty'))
    #         rec.fleet_vehicle_ids = sum(rec.picking_ids.mapped('move_ids_without_package.product_uom_qty'))

    @api.depends('picking_ids.batch_id', 'slot_allocation_time_id', 'picking_type_id')
    def _compute_delivery_qty(self):
        for rec in self:
            rec.delivery_qty = sum(rec.picking_ids.mapped('move_ids_without_package.product_uom_qty'))

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

    @api.depends('picking_ids.batch_id')
    @api.onchange('picking_ids')
    def onchange_picking_ids(self):
        picking_ids = self.picking_ids
        if not picking_ids:
            return {}
        if picking_ids and len(picking_ids.mapped('picking_type_id')) == 1 and len(picking_ids.mapped('slot_allocation_time_id')) == 1:
            self.picking_type_id = picking_ids.mapped('picking_type_id').id,
            self.slot_allocation_time_id = picking_ids.mapped('slot_allocation_time_id').id
        else:
            raise Warning(_('you can not deliver for multi picking type and multi slot time on single vehicle'))

    @api.onchange('slot_allocation_time_id', 'picking_type_id')
    def onchange_slot_picking(self):
        if self.picking_ids:
            raise Warning(_('you can not change the slot allocation time or picking'))
        domain = []
        if self.slot_allocation_time_id:
            domain += [('slot_allocation_time_id', '=', self.slot_allocation_time_id.id)]
        if self.picking_type_id:
            domain += [('picking_type_id', '=', self.picking_type_id.id)]
        return {'domain': {'picking_ids': domain}}
