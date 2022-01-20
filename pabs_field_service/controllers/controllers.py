# -*- coding: utf-8 -*-
# from odoo import http


# class PabsFieldService(http.Controller):
#     @http.route('/pabs_field_service/pabs_field_service/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_field_service/pabs_field_service/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_field_service.listing', {
#             'root': '/pabs_field_service/pabs_field_service',
#             'objects': http.request.env['pabs_field_service.pabs_field_service'].search([]),
#         })

#     @http.route('/pabs_field_service/pabs_field_service/objects/<model("pabs_field_service.pabs_field_service"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_field_service.object', {
#             'object': obj
#         })
