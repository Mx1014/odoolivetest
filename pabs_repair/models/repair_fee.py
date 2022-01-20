from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class RepairLine(models.Model):
    _inherit = 'repair.fee'

    x_discount_amount = fields.Float(string="Discount", digits=(14, 5))
    discount = fields.Float('Discount (%)', digits='Discount', default=0.0)
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_x_compute_currency_id')

    @api.depends('product_id')
    def _x_compute_currency_id(self):
        for rec in self:
            company_id = self.env.user.company_id
            rec.currency_id = company_id.currency_id

    @api.onchange('discount', 'price_unit', 'product_uom_qty', 'tax_id')
    @api.depends('product_uom_qty', 'price_unit', 'discount', 'tax_id')
    def amount_disc_get(self):
        for line in self:
            line.x_discount_amount = ((line.price_unit * line.product_uom_qty) / 100) * line.discount
            # line.price_subtotal = line.product_uom_qty * line.price_unit - (
            #         line.discount * (line.product_uom_qty * line.price_unit) / 100)

    @api.onchange('x_discount_amount', 'price_unit', 'product_uom_qty', 'tax_id')
    def perc_disc_from_amount(self):
        for line in self:
            if ((line.price_unit * line.product_uom_qty) / 100):
                line.discount = line.x_discount_amount / ((line.price_unit * line.product_uom_qty) / 100)

    @api.depends('price_unit', 'repair_id', 'product_uom_qty', 'product_id', 'tax_id', 'x_discount_amount')
    def _compute_price_subtotal(self):
        for fee in self:
            total = fee.price_unit * fee.product_uom_qty - fee.x_discount_amount
            taxes = total / (1 + ((fee.tax_id.amount if fee.tax_id else 0) / 100))
            fee.price_subtotal = taxes







