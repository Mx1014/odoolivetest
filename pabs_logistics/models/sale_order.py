# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    slot_allocation_time_id = fields.Many2one('slot.allocation.time', string="Slot Allocation Time", copy=False)
    capacity_qty = fields.Float('Capacity Quantity', realted="slot_allocation_time_id.capacity_qty")
    reamining_qty = fields.Float('Remaining Capacity Qty')

    @api.onchange('slot_allocation_time_id', 'product_uom_qty')
    def onchange_slot_allocation_time(self):
        if self.slot_allocation_time_id:
            self.reamining_qty = self.slot_allocation_time_id.reamining_qty

    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        self.ensure_one()
        values.update({'slot_allocation_time_id': self.slot_allocation_time_id and self.slot_allocation_time_id.id})
        return values

    @api.onchange('product_id', 'product_uom_qty', 'route_id')
    def onchange_product_id_to_slot_allocation(self):
        values = {}
        if not self.product_id:
            return values
        slot_allocation_time_ids = self.env['slot.allocation.time']
        domain = [('date', '>=', fields.Date.today()), ('reamining_qty', '>=',  self.product_uom_qty)]
        route_id = self.route_id or self.product_id.categ_id.route_ids
        if route_id:
            route_id = route_id and route_id[0]
            picking_type_id = route_id.rule_ids and route_id.rule_ids[0].picking_type_id
            if picking_type_id:
                domain += [('picking_type_id', '=', picking_type_id.id)]
        slot_allocation_time_ids = slot_allocation_time_ids.search(domain)
        if not slot_allocation_time_ids:
            values.update({'warning': {
                        'title': _("Warning"),
                        'message': _('Slot not exist for future delivery and current QTY, You have to create new one for that')
                        }
                    })
        values.update({'domain': {'slot_allocation_time_id': [('id', 'in', slot_allocation_time_ids.ids)]}})
        return values
