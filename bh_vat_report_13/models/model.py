from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import re
from datetime import datetime
from odoo.tools.misc import formatLang
from functools import partial


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_before_disc_price = fields.Float(string='Price Exc. Disc', compute="compute_price_before_discount",
                                       digits=(14, 3))
    x_price_tax = fields.Float(string='Tax Amount', compute="compute_price_before_discount", digits=(14, 3))
    x_discount_amount = fields.Float(string="Discount", digits=(14, 3), compute="amount_disc_get")

    @api.onchange('discount', 'price_unit', 'quantity')
    @api.depends('quantity', 'price_unit', 'discount')
    def amount_disc_get(self):
        for line in self:
            line.x_discount_amount = ((line.price_unit * line.quantity) / 100) * line.discount

    @api.onchange('x_discount_amount', 'price_unit', 'quantity')
    def perc_disc_from_amount(self):
        for line in self:
            if ((line.price_unit * line.quantity) / 100):
                line.discount = line.x_discount_amount / ((line.price_unit * line.quantity) / 100)

    @api.onchange('quantity', 'price_unit')
    @api.depends('quantity', 'price_unit')
    def compute_price_before_discount(self):
        for line in self:
            line.x_before_disc_price = line.price_unit * line.quantity
            line.x_price_tax = line.price_total - line.price_subtotal


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_before_disc_price = fields.Float(string='Price Exc. Disc', compute="compute_price_before_discount",
                                       digits=(14, 3))
    x_discount_amount = fields.Float(string="Discount", digits=(14, 3), compute="amount_disc_get")

    @api.onchange('discount', 'price_unit', 'product_uom_qty')
    @api.depends('product_uom_qty', 'price_unit', 'discount')
    def amount_disc_get(self):
        for line in self:
            line.x_discount_amount = ((line.price_unit * line.product_uom_qty) / 100) * line.discount

    @api.onchange('x_discount_amount', 'price_unit', 'product_uom_qty')
    def perc_disc_from_amount(self):
        for line in self:
            if ((line.price_unit * line.product_uom_qty) / 100):
                line.discount = line.x_discount_amount / ((line.price_unit * line.product_uom_qty) / 100)

    @api.onchange('product_uom_qty', 'price_unit')
    @api.depends('product_uom_qty', 'price_unit')
    def compute_price_before_discount(self):
        for line in self:
            line.x_before_disc_price = line.price_unit * line.product_uom_qty

    def _prepare_invoice_line(self):
        values = super(SaleOrderLine, self)._prepare_invoice_line()
        values['x_discount_amount'] = self.x_discount_amount
        # values['x_price_tax'] = self.price_tax
        return values


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sign_template_id = fields.Many2one('sign.template', string="Signature")
    sign_url = fields.Char(string="URL")

    @api.onchange('sign_template_id')
    def get_url_share(self):
        for temp in self:
            if temp.sign_template_id.responsible_count > 1:
                temp.sign_url = False
            else:
                # if not temp.sign_template_id.share_link:
                #     temp.sign_template_id.share_link = str(uuid.uuid4())
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                temp.sign_url = "%s/sign/%s" % (base_url, temp.sign_template_id.share_link)


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_show_tax = fields.Boolean(default=False, copy=False, compute="show_tax_qweb_line")

    @api.depends('invoice_line_ids')
    def show_tax_qweb_line(self):
        for invoice in self:
            invoice.x_show_tax = False
            for line in invoice.invoice_line_ids:
                if line.tax_ids:
                    invoice.x_show_tax = True

    def grouping(self):
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(formatLang, self.with_context(lang=order.partner_id.lang).env, currency_obj=currency)
            res = {}
            for line in order.invoice_line_ids:
                # for tax in line.tax_ids:
                group = line.tax_ids.name
                res.setdefault(group, {'amount': 0.0, 'base': 0.0, 'desc': ''})
                # for t in taxes:
                #     print(taxes)
                # print(res)
                # if res[0] == tax.name:
                res[group]['amount'] += order.currency_id._convert(line['x_price_tax'], order.company_id.currency_id,
                                                                   order.company_id, order.date)
                res[group]['base'] += order.currency_id._convert(line['price_subtotal'], order.company_id.currency_id,
                                                                 order.company_id, order.date)
                res[group]['desc'] = line.tax_ids.description
            # res = sorted(res.items(), key=lambda l: l[0].sequence)
            return res

# class ResPartner(models.Model):
#     _inherit = 'res.partner'
#
#     # x_is_vendor = fields.Boolean(string="Vendor", force_save=True)
#     # x_is_customer = fields.Boolean(string="Customer", force_save=True)
#     x_is_vendor = fields.Boolean(string="Vendor", compute="is_vendor", force_save=True, readonly=False)
#     x_is_customer = fields.Boolean(string="Customer", compute="is_customer", force_save=True, readonly=False)
#
#     @api.depends('supplier_rank')
#     def is_vendor(self):
#         for all in self:
#             if all.supplier_rank != 0:
#                all.x_is_vendor = True
#             else:
#                 all.x_is_vendor = False
#
#     @api.depends('customer_rank')
#     def is_customer(self):
#         for all in self:
#             if all.customer_rank != 0:
#                 all.x_is_customer = True
#             else:
#                 all.x_is_customer = False
#
#     @api.onchange('x_is_customer','x_is_vendor')
#     def onchange_rank(self):
#         for test in self:
#             if test.x_is_customer == False and test.customer_rank == 1:
#                 test.customer_rank = 0
#             elif test.x_is_customer == True and test.customer_rank == 0:
#                 test.customer_rank = 1
#             if test.x_is_vendor == False and test.supplier_rank == 1:
#                 test.supplier_rank = 0
#             elif test.x_is_vendor == True and test.supplier_rank == 0:
#                 test.supplier_rank = 1
