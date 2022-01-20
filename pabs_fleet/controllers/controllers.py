# -*- coding: utf-8 -*-
# from odoo import http


# class PabsFleet(http.Controller):
#     @http.route('/pabs_fleet/pabs_fleet/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_fleet/pabs_fleet/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_fleet.listing', {
#             'root': '/pabs_fleet/pabs_fleet',
#             'objects': http.request.env['pabs_fleet.pabs_fleet'].search([]),
#         })

#     @http.route('/pabs_fleet/pabs_fleet/objects/<model("pabs_fleet.pabs_fleet"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_fleet.object', {
#             'object': obj
#         })
