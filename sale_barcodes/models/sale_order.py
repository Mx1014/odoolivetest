# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
import odoo.addons.decimal_precision as dp



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_barcode = fields.Char(related='product_id.barcode')


    @api.onchange('product_id')
    def _onchange_product_product_id(self):
        res = {}
        if self.order_id.sale_order_type == 'cash_memo':
            res['domain'] = {'product_id': [('x_exist_in_pos', '!=', False)]}
            return res

    @api.onchange('product_template_id', 'product_id')
    def _onchange_product_product_template_id(self):
        res = {}
        if self.order_id.sale_order_type == 'cash_memo':
            res['domain'] = {'product_template_id': [('x_exist_in_pos', '!=', False)]}
            return res

    def reduce_uom_quantity(self):
        for line in self:
            if line.product_uom_qty > 1:
                line.product_uom_qty -= 1


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'barcodes.barcode_events_mixin']

    x_barcode_scan = fields.Char(string='Product Barcode', help="Here you can provide the barcode for the product")

    @api.onchange('x_barcode_scan')
    def method_add_product_call(self):
            product_rec = self.env['product.product']
            if self.x_barcode_scan:
                product = product_rec.search(
                    ['|', ('barcode', '=', self.x_barcode_scan), ('barcode_ids.name', '=', self.x_barcode_scan),
                     ('x_exist_in_pos', '!=', False)])
                if not product:
                    self.x_barcode_scan = ''
                    raise UserError(_('Barcode does not match any product!'))
                if product:
                    if product.id not in self.order_line.mapped('product_id').ids:
                        vals = product.product_tmpl_id._get_combination_info()
                        self.order_line = [(0, 0, {
                            'product_template_id': vals['product_template_id'],
                            'product_id': vals['product_id'],
                        })]
                        self.x_barcode_scan = ''
                        for order in self.order_line[-1]:
                            order.product_id_change()
                            order.product_uom_change()
                            order._onchange_discount()
                    elif product.id in self.order_line.mapped('product_id').ids:
                        exist_order = self.order_line.filtered(lambda prod: prod.product_id.id == product.id)
                        self.x_barcode_scan = ''
                        if exist_order:
                            for exist in exist_order:
                                exist.product_uom_qty += 1

    def _add_product(self, product, qty=1.0):
        order_line = self.order_line.filtered(lambda r: r.product_id.id == product.id)
        if order_line:
            order_line.product_qty = qty
        else:
            product_lang = product.with_context({
                'lang': self.partner_id.lang,
                'partner_id': self.partner_id.id,
            })
            name = product_lang.display_name
            if product_lang.description_purchase:
                name += '\n' + product_lang.description_purchase

            vals = {
                'product_id': product.id,
                'name': name,
                'product_uom': product.uom_id.id,
                'product_uom_qty': 1,
                'price_unit': product.lst_price,
                'state': 'draft',
            }
            new_order_line = self.order_line.new(vals)
            self.order_line += new_order_line
            new_order_line.product_id_change()
            new_order_line.product_uom_change()
            new_order_line._onchange_discount()

    def on_barcode_scanned(self, barcode):
        if self.sale_order_type == 'cash_memo':
            product = self.env['product.product'].search(['|', ('barcode', '=', barcode), ('barcode_ids.name', '=', barcode), ('x_exist_in_pos', '!=', False)])
            if product:
                self._add_product(product)
            else:
                raise UserError(_('Barcode does not match any product!'))

    @api.onchange('sale_order_type')
    def onchnage_sale_order_type_unlink(self):
        for sale in self:
            if sale.sale_order_type == 'cash_memo' and sale.order_line:
                sale.order_line = [(5, 0, 0)]


    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        invoice = 0
        for sale in self:
            print(sale.picking_ids.mapped('state'))
            if sale.sale_order_type == 'cash_memo' and sale.picking_ids:
                # if 'assigned' in sale.picking_ids.mapped('state'):
                #     sale.picking_ids.button_validate()
                #     wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, sale.picking_ids.id)]})
                #     wiz.process()
                if 'confirmed' or 'waiting' in sale.picking_ids.mapped('state'):
                    for move in sale.picking_ids.move_ids_without_package.filtered(lambda x: x.reserved_availability == 0.0):
                        sale.picking_ids.move_line_ids_without_package = [(0, 0, {
                            'product_id': move.product_id.id,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            #'product_uom_qty': move.product_uom_qty,
                            'origin': move.origin,
                            'picking_id': sale.picking_ids.id,
                            'reference':  sale.picking_ids.name,
                            'company_id': sale.picking_ids.company_id.id,
                            'product_uom_id': move.product_uom.id,
                            'qty_done': move.product_uom_qty,
                        })]
                        #sale.picking_ids.move_line_ids_without_package[-1].product_uom_qty = move.product_uom_qty
                sale.picking_ids.button_validate()
                wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, sale.picking_ids.id)]})
                wiz.process()
        return res


    def action_approval(self):
        res = super(SaleOrder, self).action_approval()
        if self.sale_order_type == 'cash_memo' and self.picking_ids:
            invoice = self._create_invoices()
            invoice.action_post()
            invoice.action_register_payment_custom()
            return invoice.action_register_payment_custom()
        return res
