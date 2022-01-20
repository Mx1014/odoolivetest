import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MakePrintable(models.TransientModel):
    _name = "product.make.printable"
    _description = "make a product description printable in tags"