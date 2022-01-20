# -*- coding: utf-8 -*-
# from odoo import http


# class PabsLogisticsExtra(http.Controller):
#     @http.route('/pabs_logistics_extra/pabs_logistics_extra/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_logistics_extra/pabs_logistics_extra/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_logistics_extra.listing', {
#             'root': '/pabs_logistics_extra/pabs_logistics_extra',
#             'objects': http.request.env['pabs_logistics_extra.pabs_logistics_extra'].search([]),
#         })

#     @http.route('/pabs_logistics_extra/pabs_logistics_extra/objects/<model("pabs_logistics_extra.pabs_logistics_extra"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_logistics_extra.object', {
#             'object': obj
#         })
