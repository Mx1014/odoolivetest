# -*- coding: utf-8 -*-
# from odoo import http


# class PabsUppercase(http.Controller):
#     @http.route('/pabs_uppercase/pabs_uppercase/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_uppercase/pabs_uppercase/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_uppercase.listing', {
#             'root': '/pabs_uppercase/pabs_uppercase',
#             'objects': http.request.env['pabs_uppercase.pabs_uppercase'].search([]),
#         })

#     @http.route('/pabs_uppercase/pabs_uppercase/objects/<model("pabs_uppercase.pabs_uppercase"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_uppercase.object', {
#             'object': obj
#         })
