from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning
from random import choice
from string import digits
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_products_supplied = fields.One2many('product.supplierinfo', 'name', string="Products Supplied")
