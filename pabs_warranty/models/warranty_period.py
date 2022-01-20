from odoo import models, fields, api, _
from odoo.exceptions import Warning


class WarrantyPeriod(models.Model):
    _name = 'warranty.period'
    _order = 'sequence ASC'
    name = fields.Char(string='Period')
    sequence = fields.Integer(default=10)
    period_countable = fields.Integer(string='Period Month')

    @api.onchange('period_countable')
    def set_warranty_period(self):
        # if self.period_countable:
        self.name = str(self.period_countable) + " Months"

