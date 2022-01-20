from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class RepairLine(models.Model):
    _inherit = 'repair.line'

    x_discount_amount = fields.Float(string="Discount", digits=(14, 3))
    discount = fields.Float('Discount (%)', digits='Discount', default=0.0)

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
        for line in self:
            total = line.price_unit * line.product_uom_qty - line.x_discount_amount
            taxes = total / (1 + ((line.tax_id.amount if line.tax_id else 0) / 100))
            line.price_subtotal = taxes

    @api.depends('product_id')
    def _x_compute_currency_id(self):
        for rec in self:
            company_id = self.env.user.company_id
            rec.currency_id = company_id.currency_id

    currency_id = fields.Many2one('res.currency', string='Currency', compute=_x_compute_currency_id)


@api.onchange('type', 'repair_id')
def onchange_operation_type(self):
    """ On change of operation type it sets source location, destination location
    and to invoice field.
    @param product: Changed operation type.
    @param guarantee_limit: Guarantee limit of current record.
    @return: Dictionary of values.
    """
    if not self.type:
        self.location_id = False
        self.location_dest_id = False
    elif self.type == 'add':
        self.onchange_product_id()
        warehouse = self.env['stock.location'].search([('x_is_spare_part', '=', True)], limit=1)
        if not warehouse:
            args = [('company_id', '=', self.repair_id.company_id.id)] or []
            warehouse = self.env['stock.warehouse'].search(args, limit=1).lot_stock_id
        self.location_id = warehouse
        self.location_dest_id = self.env['stock.location'].search([('usage', '=', 'production')], limit=1).id
    else:
        self.price_unit = 0.0
        self.tax_id = False
        self.location_id = self.env['stock.location'].search([('usage', '=', 'production')], limit=1).id
        self.location_dest_id = self.env['stock.location'].search([('scrap_location', '=', True)], limit=1).id
