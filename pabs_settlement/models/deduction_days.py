from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class EmployeeLeaves(models.Model):
    _name = 'deduction.days'
    x_id = fields.Many2one('hr.settlement', string='Settlement', ondelete='cascade', index=True)
    difference_days = fields.Integer(string='Difference Days')
    deduction_amount = fields.Float(string='Deduction Amount', digits=(12, 3))
