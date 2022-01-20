from odoo import models, fields, api, _
from odoo.exceptions import Warning


class NoticePeriod(models.Model):
    _name = 'notice.period'
    name = fields.Char(string='Period')
    period_countable = fields.Integer(string='Period Days')

    @api.onchange('period_countable')
    def set_notice_period(self):
        # if self.period_countable:
        self.name = str(self.period_countable) + " Days"

