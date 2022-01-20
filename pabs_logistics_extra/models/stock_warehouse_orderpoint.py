from collections import namedtuple
from datetime import datetime
from dateutil import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.osv import expression
from json import dumps

class Orderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    x_quantity_onhand = fields.Float(string='Onhand', compute='compute_x_quantity_onhand')
    x_quantity_reserved = fields.Float(string='Reserved', compute='compute_x_quantity_onhand')
    x_quantity_forecast = fields.Float(string='Forecast', compute='compute_x_quantity_onhand')
    x_quantity_free = fields.Float(string='Free to use', compute='compute_x_quantity_onhand')
    json_lead_days_popover = fields.Char(compute='_compute_json_popover')

    def _compute_json_popover(self):
        for orderpoint in self:
            if not orderpoint.product_id or not orderpoint.location_id:
                orderpoint.json_lead_days_popover = False
                continue
            orderpoint.json_lead_days_popover = dumps({
                'title': _('Replenishment'),
                'icon': 'fa-area-chart',
                'popoverTemplate': 'pabs_logistics_extra.leadDaysPopOver',
                'today': fields.Date.to_string(fields.Date.today()),
                'qty_forecast': orderpoint.x_quantity_forecast,
                'product_min_qty': orderpoint.product_min_qty,
                'product_max_qty': orderpoint.product_max_qty,
                'product_uom_name': orderpoint.product_uom_name,
            })

    @api.depends('product_id', 'warehouse_id', 'location_id')
    def compute_x_quantity_onhand(self):
        for rec in self:
            forecast = self.env['report.stock.quantity'].search([('product_id', '=', rec.product_id.id), ('warehouse_id', '=', rec.warehouse_id.id)]).mapped('product_qty')
            qty_hnd = 0.0
            qty_reserved = 0.0
            qty_forecast = 0.0
            qty_free = 0.0
            qty_onhand = self.env['stock.quant'].search([('product_id', '=', rec.product_id.id), ('location_id', '=', rec.location_id.id)])
            if qty_onhand:
                qty_hnd = qty_onhand.quantity
                qty_reserved = qty_onhand.reserved_quantity
                qty_free = qty_onhand.x_free_qty
            if rec.product_id and rec.location_id:
                moves_in = self.env['stock.move'].search([('product_id', '=', rec.product_id.id), ('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available')), ('location_dest_id', '=', rec.location_id.id)])
                moves_out = self.env['stock.move'].search([('product_id', '=', rec.product_id.id), ('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available')), ('location_id', '=', rec.location_id.id)])
                qty_forecast = qty_hnd + sum(moves_in.mapped('product_qty')) - sum(moves_out.mapped('product_qty'))
            else:
                qty_forecast = rec.product_id.virtual_available
            rec.x_quantity_onhand = qty_hnd
            rec.x_quantity_reserved = qty_reserved
            rec.x_quantity_forecast = qty_forecast
            rec.x_quantity_free = qty_free