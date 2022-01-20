from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import date
from datetime import timedelta
from datetime import datetime
import dateutil


class IndemnityVacationPaymentlines(models.Model):
    _name = 'indemnity.vacation.payment.lines'

    indemnity_id = fields.Many2one('hr.settlement', 'Settlement')
    x_total_working_days = fields.Integer(string='Total Working Days', digits=(12, 3))
    x_unpaid_leave = fields.Float(string='Unpaid Leaves', digits=(12, 3))
    x_period = fields.Char(string='Periods')
    x_date_of_join = fields.Date(string='Date From')
    x_date_to = fields.Date(string='Date To')
    x_indemnity_balance = fields.Float(string='Indemnity Balance', digits=(12, 3))
    x_final_working_days = fields.Float(string='Final Working Days', digits=(12, 3))
    x_indemnity_amount = fields.Float(string='Indemnity Amount', digits=(12, 3))
