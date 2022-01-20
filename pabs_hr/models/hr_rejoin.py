from odoo import models, fields, api, _
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class RejoinLineDate(models.Model):
    _name = 'hr.rejoin.line'
    rejoin_id = fields.Many2one('hr.leave', readonly=True)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    employee_rejoin_date = fields.Date(string='Rejoin Date', store=True)
    x_unpaid_days = fields.Integer(string='Unpaid Days', readonly=True, compute='calculate_date')
    x_holiday_status = fields.Many2one("hr.leave.type", string="Time Off Type")

    def calculate_date(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.employee_rejoin_date:
                d1 = datetime.strptime(str(self.end_date), '%Y-%m-%d')
                d2 = datetime.strptime(str(self.employee_rejoin_date), '%Y-%m-%d')
                d3 = d2 - d1
                rec.x_unpaid_days = str(d3.days)
            else:
                rec.x_unpaid_days = 0
