from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, timedelta


class VacationPaymentLine(models.Model):
    _name = 'vacation.payment.lines'
    x_id = fields.Many2one('hr.settlement', string='Settlement', ondelete='cascade', index=True, store=True)
    x_leave_type = fields.Many2one('hr.leave.type', 'Leave Type', copy=False)
    x_current_balance = fields.Float(string='Current Balance', compute='leaves_balance', store=True, digits=(12, 3))
    x_requested_days = fields.Float(string='Requested Days', digits=(12, 3))
    x_remaining_balance = fields.Float(string='Remaining Balance', digits=(12, 3), compute='_compute_remaining_balance',
                                       store=True)
    total_amount = fields.Float(string='Total Amount', digits=(12, 3), compute='_compute_total_amount')
    x_date_from = fields.Date(string='Date From')
    x_date_to = fields.Date(string='Date To')
    # total_amount = fields.Float(string='Total Amount', digits=(12, 3), store=True, compute='_compute_total_amount')
    x_annual_id = fields.Many2one('hr.leave', 'Annual', readonly=True, copy=False)
    x_overtime_id = fields.Many2one('hr.leave', 'Overtime', readonly=True, copy=False)
    x_unpaid_days = fields.Float(string='Unpaid Days', digits=(12, 3))

    @api.depends('x_current_balance', 'x_requested_days')
    @api.onchange('x_date_from', 'x_date_to')
    def _compute_days(self):
        for rec in self:
            if rec.x_date_from and rec.x_date_to:
                d1 = datetime.strptime(str(self.x_date_from), '%Y-%m-%d')
                d2 = datetime.strptime(str(self.x_date_to), '%Y-%m-%d')
                d4 = timedelta(days=1)
                d3 = (d2 - d1) + d4
                print(d3, "333")
                rec.x_requested_days = str(d3.days)
                rec.x_unpaid_days = False
            if rec.x_requested_days > rec.x_current_balance:
                rec.x_unpaid_days = abs(rec.x_current_balance - rec.x_requested_days)
                rec.x_requested_days = rec.x_current_balance


    @api.depends('x_id.employee_name', 'x_leave_type')
    @api.onchange('x_leave_type')
    def leaves_balance(self):
        for employee in self:
            if employee.x_leave_type.code == 'ANL':
                annual_leave = self.env['hr.leave.report'].search([
                    ('employee_id.id', '=', employee.x_id.employee_name.id),
                    ('holiday_status_id.active', '=', True),
                    ('state', '=', 'validate'),
                    ('holiday_status_id.x_leave_types', '=', 'Annual Leave')
                ])
                employee.x_current_balance = sum(annual_leave.mapped('number_of_days'))
                print(employee.x_current_balance, "ll")
                print(sum(annual_leave.mapped('number_of_days')), "ll")
            if employee.x_leave_type.code == 'OVTL':
                overtime_leave = self.env['hr.leave.report'].search([
                    ('employee_id.id', '=', employee.x_id.employee_name.id),
                    ('holiday_status_id.active', '=', True),
                    ('state', '=', 'validate'),
                    ('holiday_status_id.x_leave_types', '=', 'Overtime Leave')
                ])
                employee.x_current_balance = sum(overtime_leave.mapped('number_of_days'))

    @api.depends('x_current_balance', 'x_requested_days')
    @api.onchange(' x_requested_days')
    def _compute_remaining_balance(self):
        for rec in self:
            rec.x_remaining_balance = rec.x_current_balance - rec.x_requested_days

    @api.depends('x_id.employee_name')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = ((rec.x_id.basic_salary * 12) / 365) * rec.x_requested_days
