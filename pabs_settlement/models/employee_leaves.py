from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class EmployeeLeaves(models.Model):
    _name = 'employee.leaves'
    x_set_id = fields.Many2one('hr.settlement', string='Settlement', ondelete='cascade', index=True, store=True)
    settlement_annual_leave = fields.Float(string='Annual Leave', compute='annual_leaves', store=True)
    settlement_overtime_leave = fields.Float(string='Overtime Leave', compute='_compute_overtime_leave', store=True)
    x_annual_id = fields.Many2one('hr.leave', 'Annual', readonly=True, copy=False)
    x_overtime_id = fields.Many2one('hr.leave', 'Overtime', readonly=True, copy=False)

    @api.depends('x_set_id.employee_name')
    def annual_leaves(self):
        for employee in self:
            annual_leave = self.env['hr.leave.report'].search([
                ('employee_id.id', '=', employee.x_set_id.employee_name.id),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('holiday_status_id.x_leave_types', '=', 'Annual Leave')
            ])
            employee.x_annual_leave = sum(annual_leave.mapped('number_of_days'))
            employee.settlement_annual_leave = sum(annual_leave.mapped('number_of_days'))

    @api.depends('x_set_id.employee_name')
    def _compute_overtime_leave(self):
        for employee in self:
            overtime_leave = self.env['hr.leave.report'].search([
                ('employee_id.id', '=', employee.x_set_id.employee_name.id),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('holiday_status_id.x_leave_types', '=', 'Overtime Leave')
            ])
            employee.x_overtime_leave = sum(overtime_leave.mapped('number_of_days'))
            employee.settlement_overtime_leave = sum(overtime_leave.mapped('number_of_days'))


