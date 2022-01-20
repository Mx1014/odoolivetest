from odoo import models, fields, api, _
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime

class HrRule(models.Model):
    _inherit = 'hr.salary.rule'
    related_worked_days = fields.Many2many('hr.work.entry.type', string='Related Input')