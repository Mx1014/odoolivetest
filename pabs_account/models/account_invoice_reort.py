from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import datetime


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'
    x_partner_mobile = fields.Char(string='Mobile', related='partner_id.mobile')
    x_partner_phone = fields.Char(string='Phone', related='partner_id.phone')
    x_list_price = fields.Float(string='Unit Price', related='product_id.list_price')
    x_source_document = fields.Char(string='Source Document', related='move_id.invoice_origin')
    x_sales_person = fields.Char(string='Salesperson', related='move_id.invoice_user_id.name')
    x_related_order_line_id = fields.Many2one('sale.order.line', string='Related Product')
    x_price_unit = fields.Float(string='Unit Price', related='x_related_order_line_id.price_unit')
    x_invoice_price_unit = fields.Float(string='Unit Price', related='move_id.invoice_line_ids.price_unit')
    x_invoice_address = fields.Text(string='Address', related='move_id.x_shipping_address')

    # def _select(self):
    #     select_str = super()._select()
    #     select_str += """
    #           , order_line.related_order_line_id as x_related_order_line_id
    #           """
    #     return select_str

    def _select(self):
        select_str = super()._select()
        select_str += """
                 , line.x_related_order_line_id as x_related_order_line_id
                 """
        return select_str

    # @api.model
    # def _from(self):
    #     from_str = super()._from()
    #     from_str += "LEFT JOIN sale_order_line order_line ON order_line.id = line.x_so_line"
    #     return from_string

    # @api.model
    # def _from(self):
    #     from_str = super()._from()
    #     from_str += """
    #               LEFT JOIN  sale_order_line order_line on order_line.id = order_line.related_order_line_id
    #               """
    #     return from_str

    # @api.model
    # def _where(self):
    #     where_str = super()._where()
    #
    #
    # def _group_by(self):
    #     group_by_str = super()._group_by()
    #     group_by_str += ",  order_line.related_order_line_id"
    #     return group_by_str


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def get_sale_line_moves(self):
        print(self.sale_line_ids, 'ddddddddddddddd')
        return self.sale_line_ids

    sale_line_ids = fields.Many2many(
        'sale.order.line',
        'sale_order_line_invoice_rel',
        'invoice_line_id', 'order_line_id',
        string='Sales Order Lines', readonly=True, copy=False, store=True)

    x_related_order_line_id = fields.Many2one('sale.order.line', string='Related Product',
                                              related='sale_line_ids.related_order_line_id', store=True)

    x_sale_line_ids_related = fields.Many2many('sale.order.line', relation='sale_line_refs', store=True,
                                               default=get_sale_line_moves)
