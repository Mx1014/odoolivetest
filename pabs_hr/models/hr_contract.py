from odoo import models, fields, api, _
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class HrContract(models.Model):
    _inherit = 'hr.contract'
    x_date_today = fields.Date(string='Date Repaired', default=fields.Date.today())
    contract_category = fields.Many2one('contract.category', string='Contract Category', track_visibility='onchange')
    gosi_salary = fields.Monetary(string='Gosi Salary', track_visibility='onchange')
    increments = fields.Monetary(string='Increments', track_visibility='onchange')
    home_rent_allowance = fields.Monetary(string='Home Rent Allowance', track_visibility='onchange')
    food_allowance = fields.Monetary(string='Food Allowance', track_visibility='onchange')
    labour_allowance = fields.Monetary(string='Labour Allowance', track_visibility='onchange')
    other_allowance = fields.Monetary(string='Other Allowance', track_visibility='onchange')
    performance_allowance = fields.Monetary(string='Performance Allowance', track_visibility='onchange')
    shift_allowance = fields.Monetary(string='Shift Allowance', track_visibility='onchange')
    social_allowance = fields.Monetary(string='Social Allowance', track_visibility='onchange')
    special_allowance = fields.Monetary(string='Special Allowance', track_visibility='onchange')
    transportation_allowance = fields.Monetary(string='Transportation Allowance', track_visibility='onchange')
    phone_allowance = fields.Monetary(string='Phone Allowance', track_visibility='onchange')
    x_netpayable = fields.Monetary(string='Net Salary', track_visibility='onchange', compute='net_salary')
    trial_date_end = fields.Date('Probation Period',
                                 help="End date of the trial period (if there is one).", track_visibility='onchange')
    sio_employee_deduction = fields.Float(string='Sio Employee Deduction', track_visibility='onchange')
    sio_employee_deduction_amount = fields.Monetary(string='Sio Employee Deduction', track_visibility='onchange',
                                                    compute='sio_deduction_amount')
    sio_employer_contribution = fields.Float(string='Sio Employer Contribution', track_visibility='onchange')
    x_gross_salary = fields.Float(string='Gross Salary', compute='gross_salary', track_visibility='onchange')
    x_fixed_salary = fields.Float(string='Fixed Salary', compute='fixed_salary', track_visibility='onchange')
    sio_employer_contribution_amount = fields.Monetary(string='Sio Employer Contribution', track_visibility='onchange',
                                                       compute='sio_contribution_amount')
    notice_period = fields.Many2one('notice.period', string='Notice Period', track_visibility='onchange')
    contract_type = fields.Many2one('contract.type', string='Contract Type', track_visibility='onchange')
    name = fields.Char('Contract Reference', required=True, track_visibility='onchange')
    department_id = fields.Many2one('hr.department',
                                    domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                    string="Department", track_visibility='onchange')
    job_id = fields.Many2one('hr.job', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                             string='Job Position', track_visibility='onchange')
    resource_calendar_id = fields.Many2one(
        'resource.calendar', 'Working Schedule', track_visibility='onchange',
        default=lambda self: self.env.company.resource_calendar_id.id, copy=False,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    sio_applicable = fields.Selection([
        ('Yes', 'Yes'),
        ('No', 'NO')],
        string='Sio Applicable')
    is_expats = fields.Boolean(string='is Expats', default=False, compute='expats_or_not', store=True)
    count_day = fields.Integer(string='Count Day', default=1)
    x_registration_number = fields.Char(string='Code ID', related='employee_id.registration_number')
    lmra_selection = fields.Selection([('applicable', 'Applicable'), ('not_applicable', 'Not Applicable')],
                                      string='LMRA', tracking="1")
    lmra_charge = fields.Monetary(string='LMRA Charge', tracking="1")

    def net_salary(self):
        for rec in self:
            a = rec.wage + rec.increments + rec.home_rent_allowance + rec.food_allowance + rec.labour_allowance
            b = rec.other_allowance + rec.performance_allowance + rec.shift_allowance + rec.social_allowance + rec.special_allowance
            c = rec.transportation_allowance + rec.phone_allowance
            rec.x_netpayable = a + b + c

    def gross_salary(self):
        for rec in self:
            a = rec.wage + rec.increments + rec.home_rent_allowance + rec.food_allowance + rec.labour_allowance
            b = rec.other_allowance + rec.performance_allowance + rec.shift_allowance + rec.social_allowance + rec.special_allowance
            c = rec.transportation_allowance + rec.phone_allowance
            rec.x_gross_salary = a + b + c

    def fixed_salary(self):
        for rec in self:
            a = rec.wage + rec.increments + rec.home_rent_allowance + rec.food_allowance + rec.labour_allowance
            b = rec.other_allowance + rec.performance_allowance + rec.shift_allowance + rec.social_allowance + rec.special_allowance
            c = rec.transportation_allowance + rec.phone_allowance
            rec.x_fixed_salary = a + b + c - rec.sio_employee_deduction_amount

    def sio_deduction_amount(self):
        for rec in self:
            rec.sio_employee_deduction_amount = (rec.sio_employee_deduction * rec.gosi_salary) / 100

    def sio_contribution_amount(self):
        for rec in self:
            rec.sio_employer_contribution_amount = (rec.sio_employer_contribution * rec.gosi_salary) / 100

    @api.depends('employee_id.country_id')
    def expats_or_not(self):
        for rec in self:
            if rec.employee_id.country_id:
                if rec.employee_id.country_id.id != 23:
                    rec.is_expats = True
                else:
                    rec.is_expats = False

    @api.model
    def increment_wage(self):
        print("vvvvvvvvvvvvvvv")
        contracts = self.env['hr.contract'].search([])
        for contract in contracts:
            if contract.increments > 0:
                # for rec in self:
                # x = rec.date_start + relativedelta(months=12 * rec.count_day)
                # print(x, "xxxxx")
                # if fields.date.today() >= x:
                print(contract.wage, 'wwwww')
                contract.wage = contract.increments + contract.wage
                contract.gosi_salary = contract.increments + contract.gosi_salary
                print(contract.count_day, "ddddddd")
                # rec.count_day += 1
                contract.increments = 0
