# -*- coding: utf-8 -*-
# from odoo import http


# class PabsSaleExtra(http.Controller):
#     @http.route('/pabs_sale_extra/pabs_sale_extra/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_sale_extra/pabs_sale_extra/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_sale_extra.listing', {
#             'root': '/pabs_sale_extra/pabs_sale_extra',
#             'objects': http.request.env['pabs_sale_extra.pabs_sale_extra'].search([]),
#         })

#     @http.route('/pabs_sale_extra/pabs_sale_extra/objects/<model("pabs_sale_extra.pabs_sale_extra"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_sale_extra.object', {
#             'object': obj
#         })
