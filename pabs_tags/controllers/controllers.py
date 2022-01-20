# -*- coding: utf-8 -*-
# from odoo import http


# class PabsOffer(http.Controller):
#     @http.route('/pabs_offer/pabs_offer/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_offer/pabs_offer/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_offer.listing', {
#             'root': '/pabs_offer/pabs_offer',
#             'objects': http.request.env['pabs_offer.pabs_offer'].search([]),
#         })

#     @http.route('/pabs_offer/pabs_offer/objects/<model("pabs_offer.pabs_offer"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_offer.object', {
#             'object': obj
#         })
