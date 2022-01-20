from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import date
from datetime import timedelta
from datetime import datetime
import dateutil
from odoo.exceptions import UserError


class GetExtendedWarranty(models.TransientModel):
    _name = 'get.extended.warranty'

    product_id = fields.Many2one('product.product', string="Extended Warranty")
    order_line = fields.Many2one('sale.order.line', string="Product")
    extended_quantity = fields.Integer(string='Extended Quantity', default=1)

    def action_save_extended_warranty(self):
        if self.extended_quantity < 1 or self.extended_quantity > self.order_line.product_uom_qty:
            raise UserError(_("Invalid Quantity"))
        dic = {
            'order_id': self.order_line.order_id,
            'product_id': self.product_id.id,
            'product_uom_qty': self.extended_quantity,
            'tax_id': self.order_line.tax_id,
            'price_unit': self.product_id.lst_price,
            'related_order_line_id': self.order_line.id,
        }
        self.order_line.order_id.order_line = [(0, 0, dic)]
