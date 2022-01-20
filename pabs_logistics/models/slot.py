# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class SlotAllocationTime(models.Model):
    _name = "slot.allocation.time"
    _description = "Slot Allocation Time"

    name = fields.Char('Name', default=fields.Date.today())
    date = fields.Date('Delivery Date', default=fields.Date.today())
    time_zone = fields.Selection([('evening', 'Evening'), ('morning', 'Morning')], string="Time Zone")
    sale_order_line_ids = fields.One2many('sale.order.line', 'slot_allocation_time_id', string="Sale Order Line", domain=[('state', '!=', 'cancel')])
    reamining_qty = fields.Float('Remaining Capacity Qty', compute="_compute_remaining_capacity_qty", store=True)
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type')
    capacity_qty = fields.Float(related="picking_type_id.capacity_qty", store=True)
    stock_move_ids = fields.One2many('stock.move', 'slot_allocation_time_id', string="Pickings")

    @api.depends('capacity_qty', 'sale_order_line_ids', 'sale_order_line_ids.product_uom_qty')
    def _compute_remaining_capacity_qty(self):
        for rec in self:
            rec.reamining_qty = rec.capacity_qty - sum(rec.sale_order_line_ids.mapped('product_uom_qty'))

    @api.onchange('date', 'time_zone')
    def onchange_data_zone(self):
        if self.date and self.time_zone:
            self.name = str(self.date) + ' ' + str(self.time_zone)

    def name_get(self):
        res = []
        for slot in self:
            res.append((slot.id, ('%s: [%s / %s]') % (slot.name, slot.reamining_qty, slot.capacity_qty)))
        return res

    _sql_constraints = [
        (
            'unique_time_date_type', 'UNIQUE(time_zone, date, picking_type_id)',
            'can not create a same time zone , date and type because record already created')
    ]
