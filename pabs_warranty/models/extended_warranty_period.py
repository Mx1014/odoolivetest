from odoo import models, fields, api, _
from odoo.exceptions import Warning


class WarrantyPeriod(models.Model):
    _name = 'extended.warranty.period'
    name = fields.Char(string='Period')
    period_countable = fields.Integer(string='Period Months')

    @api.onchange('period_countable')
    def set_extended_warranty_period(self):
        self.name = str(self.period_countable) + " Months"

