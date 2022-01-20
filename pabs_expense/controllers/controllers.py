# -*- coding: utf-8 -*-
from odoo import http

# class Locations(http.Controller):
#     @http.route('/locations/locations/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/locations/locations/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('locations.listing', {
#             'root': '/locations/locations',
#             'objects': http.request.env['locations.locations'].search([]),
#         })

#     @http.route('/locations/locations/objects/<model("locations.locations"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('locations.object', {
#             'object': obj
#         })