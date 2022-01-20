# -*- coding: utf-8 -*-
from odoo import http

# class CustomerAnalysis(http.Controller):
#     @http.route('/customer_analysis/customer_analysis/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customer_analysis/customer_analysis/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('customer_analysis.listing', {
#             'root': '/customer_analysis/customer_analysis',
#             'objects': http.request.env['customer_analysis.customer_analysis'].search([]),
#         })

#     @http.route('/customer_analysis/customer_analysis/objects/<model("customer_analysis.customer_analysis"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customer_analysis.object', {
#             'object': obj
#         })