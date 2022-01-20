# -*- coding: utf-8 -*-
# from odoo import http


# class PabsBase(http.Controller):
#     @http.route('/pabs_base/pabs_base/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_base/pabs_base/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_base.listing', {
#             'root': '/pabs_base/pabs_base',
#             'objects': http.request.env['pabs_base.pabs_base'].search([]),
#         })

#     @http.route('/pabs_base/pabs_base/objects/<model("pabs_base.pabs_base"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_base.object', {
#             'object': obj
#         })
