# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', domain="[('code', '=', 'outgoing')]", tracking=True)
    capacity_qty = fields.Float("Vehicle's Capacity Qty", tracking=True)
