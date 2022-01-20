# -*- coding: utf-8 -*-
# from odoo import http


# class PabsRepair(http.Controller):
#     @http.route('/pabs_repair/pabs_repair/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_repair/pabs_repair/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_repair.listing', {
#             'root': '/pabs_repair/pabs_repair',
#             'objects': http.request.env['pabs_repair.pabs_repair'].search([]),
#         })

#     @http.route('/pabs_repair/pabs_repair/objects/<model("pabs_repair.pabs_repair"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_repair.object', {
#             'object': obj
#         })
