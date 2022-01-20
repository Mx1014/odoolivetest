# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


class Location(models.Model):
    _inherit = "stock.location"

    @api.returns('stock.warehouse', lambda value: value.id)
    def get_warehouse(self):
        """ Returns warehouse id of warehouse that contains location """
        domain = [('view_location_id', 'parent_of', self.ids)]
        return self.env['stock.warehouse'].search(domain, limit=1)

    def should_bypass_reservation(self):
        self.ensure_one()
        return self.usage in ('supplier', 'customer', 'inventory', 'production') or self.scrap_location or (self.usage == 'transit' and not self.company_id)