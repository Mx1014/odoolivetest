from odoo import models, fields, api


class PurchaseAgrement(models.Model):
    _inherit = 'purchase.requisition'

    @api.depends('line_ids.x_price_subtotal')
    def _amount_all(self):
        for order in self:
            amount_untaxed = 0.0
            tax_amount = 0.0
            val = 0.0
            for line in order.line_ids:
                amount_untaxed += line.x_price_subtotal
                tax_amount = line.x_price_subtotal
                tax_calculate = (tax_amount * (
                            1 + ((line.x_taxes_id.amount if line.x_taxes_id else 0) / 100))) - tax_amount
                val += tax_calculate
            order.x_untaxed_amount = amount_untaxed
            order.x_amount_tax = val
            order.x_amount_total = amount_untaxed + val

    x_untaxed_amount = fields.Monetary(string='Untaxed Amount', store=True, readonly=True,
                                       tracking=True, compute='_amount_all')
    x_amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    x_amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')


class PurchaseAgrementLine(models.Model):
    _inherit = 'purchase.requisition.line'
    x_taxes_id = fields.Many2many('account.tax', string='Taxes',
                                  domain=['|', ('active', '=', False), ('active', '=', True)])
    x_price_subtotal = fields.Float(string='Subtotal')

    @api.onchange('price_unit', 'product_qty')
    @api.depends('product_qty', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.x_price_subtotal = (line.price_unit * line.product_qty)

    @api.onchange('product_id')
    def onchange_for_taxes(self):
        self.x_taxes_id = self.product_id.supplier_taxes_id
