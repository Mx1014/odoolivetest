# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string="Deliver on Vehicle", tracking=True)
    slot_allocation_time_id = fields.Many2one('slot.allocation.time', string="Slot Allocation Time")
    zone = fields.Char(related="partner_id.zone")
    city = fields.Char(related="partner_id.city")
    phone = fields.Char(related="partner_id.phone")
    street = fields.Char("Street", compute="_compute_street")

    @api.depends('partner_id', 'partner_id.street', 'partner_id.street2')
    def _compute_street(self):
        for rec in self:
            rec.street = (rec.partner_id.street or '') + (rec.partner_id.street2 or '')

    def action_done(self):
        res = super(StockPicking, self).action_done()
        slot_allocation_vehicle = []
        for pick in self.filtered(lambda p: p.fleet_vehicle_id and p.slot_allocation_time_id):
            slot_vehicle = {
                # 'slot_allocation_time_id': pick.slot_allocation_time_id and pick.slot_allocation_time_id.id,
                # 'fleet_vehicle_id': pick.fleet_vehicle_id and pick.fleet_vehicle_id.id,
                'picking_id': pick.id,
                # 'picking_type_id': pick.picking_type_id.id,
                'sale_order_id': pick.group_id.sale_id.id,
            }
            slot_allocation_vehicle.append(slot_vehicle)
        try:
            if slot_allocation_vehicle:
                self.env['slot.allocation.vehicle'].create(slot_allocation_vehicle)
        except Exception as e:
            print ('LOG---------------------', e)
        return res


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    fleet_vehicle_ids = fields.One2many('fleet.vehicle', 'picking_type_id', string="Deliver on Vehicle")
    capacity_qty = fields.Float(string='Capacity Qty', compute="_compute_capacity_qty", store=True)

    @api.depends('fleet_vehicle_ids', 'fleet_vehicle_ids.capacity_qty')
    def _compute_capacity_qty(self):
        for rec in self:
            rec.capacity_qty = sum(rec.fleet_vehicle_ids.mapped('capacity_qty'))
