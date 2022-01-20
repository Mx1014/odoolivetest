from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class EmployeeLeaves(models.Model):
    _name = 'encashment.lines'
    x_id = fields.Many2one('hr.settlement', string='Settlement', ondelete='cascade', index=True, store=True)
    x_leave_type = fields.Many2one('hr.leave.type', 'Leave Type', copy=False)
    x_current_balance = fields.Float(string='Current Balance', compute='leaves_balance', store=True, digits=(12, 3))
    x_requested_days = fields.Float(string='Requested Days', digits=(12, 3))
    x_remaining_balance = fields.Float(string='Remaining Balance', digits=(12, 3), compute='_compute_remaining_balance',
                                       store=True)
    # x_annual_leave = fields.Float(string='Annual', compute='annual_leaves', store=True)
    # x_overtime_leave = fields.Float(string='Overtime', compute='_compute_overtime_leave', store=True)
    # x_requested_annual_leave = fields.Float(string='Request Annual Leave', digits=(12, 3))
    # x_requested_overtime_leave = fields.Float(string='Request Overtime Leave', digits=(12, 3))
    # annual_amount = fields.Float(string='Annual Amount', digits=(12, 3), store=True, compute='_compute_annual_amount')
    # overtime_amount = fields.Float(string='Overtime Amount', digits=(12, 3), store=True,
    #                                compute='_compute_overtime_amount')
    total_amount = fields.Float(string='Total Amount', digits=(12, 3), compute='_compute_total_amount')

    # total_amount = fields.Float(string='Total Amount', digits=(12, 3), store=True, compute='_compute_total_amount')
    x_annual_id = fields.Many2one('hr.leave', 'Annual', readonly=True, copy=False)
    x_overtime_id = fields.Many2one('hr.leave', 'Overtime', readonly=True, copy=False)

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

    # @api.depends('x_id.employee_name')
    # def _compute_overtime_leave(self):
    #     for employee in self:
    #         overtime_leave = self.env['hr.leave.report'].search([
    #             ('employee_id.id', '=', employee.x_id.employee_name.id),
    #             ('holiday_status_id.active', '=', True),
    #             ('state', '=', 'validate'),
    #             ('holiday_status_id.x_leave_types', '=', 'Overtime Leave')
    #         ])
    #         employee.x_overtime_leave = sum(overtime_leave.mapped('number_of_days'))

    # @api.depends('x_id.employee_name')
    # def _compute_annual_amount(self):
    #     for rec in self:
    #         rec.annual_amount = rec.x_id.x_salary_per_day * rec.x_requested_annual_leave
    #
    # @api.depends('x_id.employee_name')
    # def _compute_overtime_amount(self):
    #     for rec in self:
    #         rec.overtime_amount = rec.x_id.x_salary_per_day * rec.x_requested_overtime_leave
    #

    @api.depends('x_id.employee_name')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = ((rec.x_id.basic_salary * 12) / 365) * rec.x_requested_days
