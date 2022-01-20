# -*- coding: utf-8 -*-
# from odoo import http


# class ProductBarcode(http.Controller):
#     @http.route('/product_barcode/product_barcode/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_barcode/product_barcode/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_barcode.listing', {
#             'root': '/product_barcode/product_barcode',
#             'objects': http.request.env['product_barcode.product_barcode'].search([]),
#         })

#     @http.route('/product_barcode/product_barcode/objects/<model("product_barcode.product_barcode"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_barcode.object', {
#             'object': obj
#         })
