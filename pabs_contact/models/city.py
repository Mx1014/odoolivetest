from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError



class ResPartner(models.Model):
    _inherit = 'res.city'
    x_block = fields.Char(string="Block No.")