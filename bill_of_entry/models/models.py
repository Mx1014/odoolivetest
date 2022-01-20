# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class bill_of_entry(models.Model):
#     _name = 'bill_of_entry.bill_of_entry'
#     _description = 'bill_of_entry.bill_of_entry'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
