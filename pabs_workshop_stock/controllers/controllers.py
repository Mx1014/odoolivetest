# -*- coding: utf-8 -*-
# from odoo import http


# class PabsWorkshopStock(http.Controller):
#     @http.route('/pabs_workshop_stock/pabs_workshop_stock/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_workshop_stock/pabs_workshop_stock/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_workshop_stock.listing', {
#             'root': '/pabs_workshop_stock/pabs_workshop_stock',
#             'objects': http.request.env['pabs_workshop_stock.pabs_workshop_stock'].search([]),
#         })

#     @http.route('/pabs_workshop_stock/pabs_workshop_stock/objects/<model("pabs_workshop_stock.pabs_workshop_stock"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_workshop_stock.object', {
#             'object': obj
#         })
