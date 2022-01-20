from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class AnualProvision(models.Model):
    _name = 'anual.provision'
    name = fields.Char(string='Name')
    x_rule = fields.Char(string='Rule', readonly=True)
    x_reference = fields.Char(string='Reference', readonly=True)
    employee_name = fields.Many2one('hr.employee', string='Employee', track_visibility='onchange')
    x_total = fields.Float(string='Total')
    x_date = fields.Datetime(string='Date')
