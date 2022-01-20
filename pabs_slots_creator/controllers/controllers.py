# -*- coding: utf-8 -*-
# from odoo import http


# class PabsSlotsCreator(http.Controller):
#     @http.route('/pabs_slots_creator/pabs_slots_creator/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_slots_creator/pabs_slots_creator/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_slots_creator.listing', {
#             'root': '/pabs_slots_creator/pabs_slots_creator',
#             'objects': http.request.env['pabs_slots_creator.pabs_slots_creator'].search([]),
#         })

#     @http.route('/pabs_slots_creator/pabs_slots_creator/objects/<model("pabs_slots_creator.pabs_slots_creator"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_slots_creator.object', {
#             'object': obj
#         })
