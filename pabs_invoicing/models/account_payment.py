# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountPyament(models.Model):
    _inherit = 'account.payment'

    x_sale_id = fields.Many2one('sale.order', string="Sale Order")
