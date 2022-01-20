from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class Vacation(models.Model):
    _name = 'vacation.payment'

    x_sett_id = fields.Many2one('hr.settlement', string='Settlement', ondelete='cascade', index=True, store=True)
    x_total_leaves_taken = fields.Float(string='Total Allocation', store=True, digits=(12, 3))
    # x_due_days = fields.Float(string='Due Leave Days', compute='_compute_annual_leave', store=True)
    # x_vacation_payment = fields.Float(string='Vacation Payment', compute='_compute_vacation_payment', digits=(12, 3),
    #                                   store=True)
    x_vacation_payment = fields.Float(string='Vacation Payment', digits=(12, 3), store=True)
    x_grand_total = fields.Float(string='Grand total', digits=(12, 3), store=True)
    # x_grand_total = fields.Float(string='Grand total', compute='_compute_grand_total', digits=(12, 3), store=True)
    x_leave_type = fields.Many2one('hr.leave.type', 'Leave Type', copy=False)
    x_leave = fields.Float(string='Remaining', store=True, digits=(12, 3))
    # x_total_annual = fields.Float(string='', store=True)
    # x_overtime_leave = fields.Float(string='', store=True)
    # x_total_overtime = fields.Float(string='', store=True)
    # x_total_days = fields.Float(string='', store=True)
    x_total = fields.Float(string='Total', digits=(12, 3), store=True)
    x_leaves_taken = fields.Float(string='Leaves Taken', digits=(12, 3), store=True)

    # if sum(annual_leave.mapped('number_of_days')) + sum(
    #         overtime_leave.mapped('number_of_days')) != 0:
    # employee.x_due_days = sum(annual_leave.mapped('number_of_days')) + sum(
    #     overtime_leave.mapped('number_of_days'))
    # else:
    #     employee.x_due_days = 0

    # @api.depends('x_sett_id.employee_name')
    # def _compute_vacation_payment(self):
    #     for rec in self:
    #         rec.x_vacation_payment = ((rec.x_sett_id.basic_salary * 12) / 365) * rec.x_due_days

    # @api.depends('x_sett_id.employee_name')
    # def _compute_grand_total(self):
    #     for rec in self:
    #         rec.x_grand_total = rec.x_vacation_payment
