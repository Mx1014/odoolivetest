# -*- coding: utf-8 -*-
# from odoo import http


# class PabsPromotion(http.Controller):
#     @http.route('/pabs_promotion/pabs_promotion/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_promotion/pabs_promotion/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_promotion.listing', {
#             'root': '/pabs_promotion/pabs_promotion',
#             'objects': http.request.env['pabs_promotion.pabs_promotion'].search([]),
#         })

#     @http.route('/pabs_promotion/pabs_promotion/objects/<model("pabs_promotion.pabs_promotion"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_promotion.object', {
#             'object': obj
#         })
