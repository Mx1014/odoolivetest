# -*- coding: utf-8 -*-
# from odoo import http


# class BillOfEntry(http.Controller):
#     @http.route('/bill_of_entry/bill_of_entry/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bill_of_entry/bill_of_entry/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bill_of_entry.listing', {
#             'root': '/bill_of_entry/bill_of_entry',
#             'objects': http.request.env['bill_of_entry.bill_of_entry'].search([]),
#         })

#     @http.route('/bill_of_entry/bill_of_entry/objects/<model("bill_of_entry.bill_of_entry"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bill_of_entry.object', {
#             'object': obj
#         })
