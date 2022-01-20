# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class pabs_slots_creator(models.Model):
#     _name = 'pabs_slots_creator.pabs_slots_creator'
#     _description = 'pabs_slots_creator.pabs_slots_creator'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
