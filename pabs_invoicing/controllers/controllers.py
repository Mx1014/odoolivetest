# -*- coding: utf-8 -*-
# from odoo import http


# class PabsInvoicing(http.Controller):
#     @http.route('/pabs_invoicing/pabs_invoicing/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_invoicing/pabs_invoicing/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_invoicing.listing', {
#             'root': '/pabs_invoicing/pabs_invoicing',
#             'objects': http.request.env['pabs_invoicing.pabs_invoicing'].search([]),
#         })

#     @http.route('/pabs_invoicing/pabs_invoicing/objects/<model("pabs_invoicing.pabs_invoicing"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_invoicing.object', {
#             'object': obj
#         })
