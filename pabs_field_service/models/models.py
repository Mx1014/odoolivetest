# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class pabs_field_service(models.Model):
#     _name = 'pabs_field_service.pabs_field_service'
#     _description = 'pabs_field_service.pabs_field_service'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
