# -*- coding: utf-8 -*-
# from odoo import http


# class PabsDeliveryReport(http.Controller):
#     @http.route('/pabs_delivery_report/pabs_delivery_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pabs_delivery_report/pabs_delivery_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pabs_delivery_report.listing', {
#             'root': '/pabs_delivery_report/pabs_delivery_report',
#             'objects': http.request.env['pabs_delivery_report.pabs_delivery_report'].search([]),
#         })

#     @http.route('/pabs_delivery_report/pabs_delivery_report/objects/<model("pabs_delivery_report.pabs_delivery_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pabs_delivery_report.object', {
#             'object': obj
#         })
