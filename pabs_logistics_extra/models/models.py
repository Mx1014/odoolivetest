# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class pabs_logistics_extra(models.Model):
#     _name = 'pabs_logistics_extra.pabs_logistics_extra'
#     _description = 'pabs_logistics_extra.pabs_logistics_extra'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
