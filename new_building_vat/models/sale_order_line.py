# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    nb_price_unit = fields.Float('Unit Price (Stored to be recovered)', store=True, digits='Product Price', default=0.0)
