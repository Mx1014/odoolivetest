# -*- coding: utf-8 -*-
# from odoo import http


# class PabsProduct(http.Controller):
#     @http.route('/pabs_product/pabs_product/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_product/pabs_product/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_product.listing', {
#             'root': '/pabs_product/pabs_product',
#             'objects': http.request.env['pabs_product.pabs_product'].search([]),
#         })

#     @http.route('/pabs_product/pabs_product/objects/<model("pabs_product.pabs_product"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_product.object', {
#             'object': obj
#         })
