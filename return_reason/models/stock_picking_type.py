# -*- coding: utf-8 -*-
# Part of Odoo. See ICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    is_reason_required = fields.Boolean(
        string="Is Reason Required?",
        help="Makes the system asks the users to add a reason of the returned orders in DN.",
        default=False,
    )
