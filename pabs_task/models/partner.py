from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning
from random import choice
from string import digits


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_sub_engineer = fields.Boolean(string="Engineer", tracking="1")