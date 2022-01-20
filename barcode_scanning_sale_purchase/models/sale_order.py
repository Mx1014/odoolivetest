from odoo import api, models, fields, _
from odoo.exceptions import UserError
from playsound import playsound
from lxml import etree
from lxml.builder import E


# import simpleaudio as sa


class SaleOrderLines(models.Model):
    _inherit = 'sale.order.line'

    # barcode_scan = fields.Char(string='Product Barcode', help="Here you can provide the barcode for the product")
    #
    # @api.onchange('barcode_scan')
    # def _onchange_barcode_scan(self):
    #     product_rec = self.env['product.product']
    #     product_tmpl = self.env['product.template']
    #     if self.barcode_scan:
    #         product = product_rec.search(['|', ('barcode', '=', self.barcode_scan), ('barcode_ids.name', '=', self.barcode_scan), ('x_exist_in_pos', '!=', False)])
    #         self.product_id = product.id
    #         template = product_tmpl.search(['|', ('barcode', '=', self.barcode_scan), ('barcode_ids.name', '=', self.barcode_scan), ('x_exist_in_pos', '!=', False)])
    #         print(template)
    #         self.product_template_id = template.id
    #         if not product or not template:
    #             # filename = '/barcode_scanning_sale_purchase/static/description/warning.wav'
    #             # wave_obj = sa.WaveObject.from_wave_file(filename)
    #             # play_obj = wave_obj.play()
    #             # play_obj.wait_done()
    #             #playsound('/barcode_scanning_sale_purchase/static/description/warning.wav')
    #             raise UserError(_('Barcode does not match any product!'))

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


class Sales(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'barcodes.barcode_events_mixin']

    x_barcode_scan = fields.Char(string='Product Barcode', help="Here you can provide the barcode for the product")
    x_no_use = fields.Char(string='no use')

    #
    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(Sales, self).fields_view_get(view_id=view_id, view_type=view_type,
    #                                              toolbar=toolbar, submenu=submenu)
    #     type = self.env.context.get('default_type')
    #     if view_type == 'form':
    #         print(type, 'type')
    #         doc = etree.XML(res['arch'])
    #         node = doc.xpath("//field[@name='x_barcode_scan']")[0]
    #         parent = node.getparent()
    #         fields_attrs = {
    #             'placeholder': 'Barcode',
    #         }
    #         parent.append(
    #             E.field(
    #                 name="x_barcode_scan",
    #                 **fields_attrs,
    #             )
    #         )
    #         dd = doc.xpath("//field[@name='x_barcode_scan']")[1]
    #         dd.set('attrs', "{'invisible': [('sale_order_type', '!=', 'cash_memo')]}")
    #         res['arch'] = etree.tostring(doc)
    #     return res


    #@api.onchange('x_barcode_scan', 'x_no_use')
    def action_automatic_entry(self):
        product_rec = self.env['product.product']
        if self.x_barcode_scan:
            product = product_rec.search(
                ['|', ('barcode', '=', self.x_barcode_scan), ('barcode_ids.name', '=', self.x_barcode_scan),
                 ('x_exist_in_pos', '!=', False)])
            if not product:
                playsound('/home/odoo/custom/barcode_scanning_sale_purchase/static/description/WARNING.wav')
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
                elif product.id in self.order_line.mapped('product_id').ids:
                    exist_order = self.order_line.filtered(lambda prod: prod.product_id.id == product.id)
                    self.x_barcode_scan = ''
                    if exist_order:
                        for exist in exist_order:
                            exist.product_uom_qty += 1

    @api.onchange('sale_order_type')
    def onchnage_sale_order_type_unlink(self):
        for sale in self:
            if sale.sale_order_type == 'cash_memo' and sale.order_line:
                sale.order_line = [(5, 0, 0)]

    # def action_confirm(self):
    #     res = super(Sales, self).action_confirm()
    #     for sale in self:
    #         if sale.sale_order_type == 'cash_memo' and sale.picking_ids:
    #             if 'confirmed' in sale.picking_ids.mapped('state'):
    #                 raise UserError(_('No Stock Available'))
    #             elif 'assigned' in sale.picking_ids.mapped('state'):
    #                 sale.picking_ids.button_validate()
    #                 wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, sale.picking_ids.id)]})
    #                 wiz.process()
    #     return res