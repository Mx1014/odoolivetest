# -*- coding: utf-8 -*-
# from odoo import http


# class PabsSaleQuotation(http.Controller):
#     @http.route('/pabs_sale_quotation/pabs_sale_quotation/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_sale_quotation/pabs_sale_quotation/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_sale_quotation.listing', {
#             'root': '/pabs_sale_quotation/pabs_sale_quotation',
#             'objects': http.request.env['pabs_sale_quotation.pabs_sale_quotation'].search([]),
#         })

#     @http.route('/pabs_sale_quotation/pabs_sale_quotation/objects/<model("pabs_sale_quotation.pabs_sale_quotation"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_sale_quotation.object', {
#             'object': obj
#         })
