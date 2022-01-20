# -*- coding: utf-8 -*-
# from odoo import http


# class PabsHr(http.Controller):
#     @http.route('/pabs_hr/pabs_hr/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_hr/pabs_hr/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_hr.listing', {
#             'root': '/pabs_hr/pabs_hr',
#             'objects': http.request.env['pabs_hr.pabs_hr'].search([]),
#         })

#     @http.route('/pabs_hr/pabs_hr/objects/<model("pabs_hr.pabs_hr"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_hr.object', {
#             'object': obj
#         })
