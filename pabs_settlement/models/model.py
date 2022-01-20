from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, timedelta
from odoo.tools import float_compare, float_is_zero
from calendar import monthrange
import calendar


class HrSettlement(models.Model):
    _name = 'hr.settlement'
    _description = 'Settlement'
    _inherit = 'mail.thread'

    employee_name = fields.Many2one('hr.employee', string='Employee', track_visibility='onchange',
                                    default=lambda self: self.env.user.employee_id)
    cpr = fields.Char(string="CPR", related='employee_name.identification_id')
    department = fields.Many2one('hr.department', string='Department', track_visibility='onchange',
                                 related='employee_name.department_id', store=True)
    employee_code = fields.Char(string='Code ID', related='employee_name.registration_number')
    date = fields.Date(string='Settlement Date', track_visibility='onchange', copy=False,
                       required=True, default=fields.Date.today())
    resignation_date = fields.Date(string='Resignation Date', track_visibility='onchange')
    nationality = fields.Many2one('res.country', string='Nationality', tracking="1", related='employee_name.country_id')
    passport_no = fields.Char(string='Passport No', related='employee_name.passport_id')
    join_date = fields.Date(string='Date Of Join', related='employee_name.date_of_join')
    basic_salary = fields.Monetary(string='Basic Salary', related='employee_name.contract_id.wage', digits=(12, 3))
    company_id = fields.Many2one('res.company', string='Company', store=True, readonly=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency")
    rejoin_date = fields.Date(string='Last Rejoin Date', compute='last_rejoin_date')
    last_work_date = fields.Date(string='Last Working Date')
    verification_leaving_date = fields.Date(string='Leaving Date')
    verification_leaving_reason = fields.Many2one('leaving.reason', string='Leaving Reason')
    x_employee_status = fields.Selection([
        ('Temporary', 'Temporary'),
        ('Permanent', 'Permanent'),
        ('Part Time', 'Part Time'),
        ('Full Time', 'Full Time')],
        string='Employee Status', related='employee_name.employee_status')
    duration_of_work = fields.Char(string='Duration of Work', compute='total_duration_of_work')
    total_duration_days = fields.Char(string='Total Duration Days')
    due_days = fields.Float(string='Due Leave Days')
    salary_per_day = fields.Monetary(string='Salary Per Day', compute='salary_for_day')
    x_visa_issue_date = fields.Date(string='Visa Issue Date', related='employee_name.visa_issue_date')
    x_visa_expiry_date = fields.Date(string='Visa Expiry Date', related='employee_name.visa_expire')
    ticket_price = fields.Monetary(string='Ticket Price', digits=(12, 3))
    ticket_covered_price = fields.Monetary(string='Ticket Covered Price', digits=(12, 3))
    air_line = fields.Char(string='Air Line')
    ticket_number = fields.Char(string='Ticket Number')
    vacation_payment = fields.Float(string='Vacation Payment', digits=(12, 3))
    Last_month_salary = fields.Float(string='Last Month Salary')
    grand_total = fields.Float(string='Grand total', digits=(12, 3))
    type_of_settlement = fields.Selection(
        [('in_cashment', 'in Cashment'), ('final_settlement', 'Final Settlement')],
        string='Type of Settlement', track_visibility='onchange')
    state = fields.Selection(
        [('draft', 'Draft'), ('approved', 'Approve'), ('review_loans', 'Review Loans'),
         ('final_slip', 'Final Slip'), ('final_review', 'Final Review'), ('validated', 'Validated')],
        string='State', default='draft', readonly=True, track_visibility='onchange', copy=False)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True,
                                 default=lambda self: self.env['account.journal'].search([('type', '=', 'general')],
                                                                                         limit=1))
    x_employee_slips = fields.Many2one('hr.payslip', string='Employee Slip')
    x_move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)
    x_annual_id = fields.Many2one('hr.leave', 'Annual', readonly=True, copy=False)
    x_overtime_id = fields.Many2one('hr.leave', 'Overtime', readonly=True, copy=False)
    name = fields.Char(string='Description', readonly=True, track_visibility='onchange', compute='concat_name')
    settlement_type = fields.Many2one('settlement.type', string='Settlement Type')
    x_employee_contract = fields.Many2one(string='Employee Contract', related='employee_name.contract_id')
    x_notice_period = fields.Many2one(string='Notice Period', related='x_employee_contract.notice_period')
    indemnity_generate = fields.Boolean(string='Indemnity Generate', readonly=True)
    x_related_is_settelment = fields.Boolean(related='settlement_type.is_settlement')
    x_related_is_encashment = fields.Boolean(related='settlement_type.is_encashment')
    x_related_is_vacation_payment = fields.Boolean(related='settlement_type.is_vacation_payment')
    vacation_payment_line = fields.One2many('vacation.payment.lines', 'x_id', store=True)
    indemnity_vacation_payment_line = fields.One2many('indemnity.vacation.payment.lines', 'indemnity_id', store=True)
    indemnity_ids = fields.One2many('indemnity.lines', 'indemnity_id', store=True)
    x_input_line = fields.One2many('hr.input', 'x_settlement_id', store=True, string='Input Line')
    x_vacation_payments = fields.One2many('vacation.payment', 'x_sett_id', store=True, string='Vacation Payment')
    x_employee_leaves = fields.One2many('employee.leaves', 'x_set_id', store=True, string='Vacation Payment')
    x_encashment_leaves = fields.One2many('encashment.lines', 'x_id', store=True, string='Encashment Leave')
    x_deduction_days = fields.One2many('deduction.days', 'x_id', store=True, string='Deduction Days')
    x_anual_proviosn = fields.One2many('anual.provision.lines', 'x_id', store=True, string='Anual Provision')
    x_indemnity_proviosn = fields.One2many('indemnity.provision.lines', 'x_id', store=True,
                                           string='Indemnity Provision')
    x_working_days = fields.Float(string='Working Days', compute='working_days')
    x_annual_leave = fields.Float(string='Annual')
    x_overtime_leave = fields.Float(string='Overtime')
    settlement_annual_leave = fields.Float(string='Annual Leave')
    settlement_overtime_leave = fields.Float(string='Overtime Leave')
    x_requested_annual_leave = fields.Float(string='Annual', digits=(12, 3))
    x_requested_overtime_leave = fields.Float(string='Overtime', digits=(12, 3))
    x_salary_per_day = fields.Float(string='Salary Per Day', digits=(12, 3), compute='salary_per_day', store=True)
    x_journal_count = fields.Integer(string='Slips', compute='get_journal_count')
    x_vacation_payment_count = fields.Integer(string='Slips', compute='get_vacation_payment_count_count')
    x_name = fields.Char(string='Reference', default='New', readonly=1)
    x_count_days = fields.Integer(string='deduction days', compute='calculate_date')
    x_deduction_amount = fields.Float(string='deduction Amount', digits=(12, 3), compute='calculate_amount')
    total_amount = fields.Float(string='Total', compute='calculate_total_amount')
    net_salary = fields.Float(string='Net Salary', compute='calculate_net_salary')
    x_total_vacation = fields.Float(string='Vacation', compute='vac_total')
    x_total_input = fields.Float(string='Input', compute='input_total')
    x_total_indeminty = fields.Float(string='Indemintiy', compute='indeminity_total')
    x_total_deduction = fields.Float(string='Deduction', compute='deduction_total')
    x_total_encashemnt_payment = fields.Float(string='Encashment Payment', compute='encashment_vacation_total')
    x_total_indeminity_payment = fields.Float(string='Indeminity Payment', compute='indeminity_vacation_total')
    x_total_encashment = fields.Float(string='Encashment', compute='encashment_total')
    x_loan_and_credit_amount = fields.Float(string='Loan and Credit', compute='get_loan_credit', store=True)
    x_annual_leave_taken = fields.Float(string='Leave Taken', compute='_compute_annual_leave', store=True)
    x_total_annual = fields.Float(string='', compute='_compute_annual_leave', store=True)
    x_overtime_leave_taken = fields.Float(string='', compute='_compute_annual_leave', store=True)
    x_total_overtime = fields.Float(string='Total overtime', compute='_compute_annual_leave', store=True)
    x_total_days = fields.Float(string='', compute='_compute_annual_leave', store=True)
    x_annual_leave_timeoff = fields.Float(string='', compute='_compute_annual_leave', store=True)
    x_overtime_leave_timeoff = fields.Float(string='', compute='_compute_annual_leave', store=True)
    x_applied_amount = fields.Monetary(string='Applied Amount', digits=(12, 3))
    x_deduct_amount = fields.Monetary(string='Deduct Amount', digits=(12, 3))
    note = fields.Text()
    x_traveling_date = fields.Date(string='Traveling Date')
    x_rejoining_date = fields.Date(string='Rejoining Date')
    # @api.constrains('x_annual_leave', 'x_overtime_leave', 'x_requested_annual_leave', 'x_requested_overtime_leave')
    # def incahsment__restriction(self):
    #     for rec in self:
    #         if rec.x_annual_leave <= rec.x_requested_annual_leave or rec.x_overtime_leave <= rec.x_requested_overtime_leave:
    #             raise UserError('There is No Enough Leave')
    #

    def action_vacation_payment_approve(self):
        if self.x_applied_amount:
            if self.x_applied_amount > self.x_total_indeminity_payment:
                raise UserError('Applied Amount is Greater Than  Indemnity Amount')
        self.write({'state': 'final_slip'})

    @api.constrains('resignation_date', 'verification_leaving_date')
    def date_restriction(self):
        if self.resignation_date > self.verification_leaving_date:
            raise UserError('Resignation Date Greater Than Leaving Date')

    def action_print_report_encashment(self):
        # return self.env.ref('pabs_settlement.annual_leave_settlement_printout').report_action(self)
        return {'type': 'ir.actions.report', 'report_name': 'pabs_settlement.annual_leave_settlement_printout',
                'report_type': "qweb-pdf"}

    def action_print_report_settlement(self):
        # return self.env.ref('pabs_settlement.final_settlement_printout').report_action(self)
        return {'type': 'ir.actions.report', 'report_name': 'pabs_settlement.final_settlement_printout',
                'report_type': "qweb-pdf"}

    @api.constrains('x_encashment_leaves')
    def encahsment_restriction(self):
        if self.x_encashment_leaves[len(self.x_encashment_leaves) - 1].x_leave_type.id == \
                self.x_encashment_leaves[0].x_leave_type.id and self.x_encashment_leaves.search_count(
            [('x_id', '=', self.id)]) > 1:
            raise UserError('You Have To Choose Different Leaves')
        if self.x_encashment_leaves.search_count([('x_id', '=', self.id)]) > 2:
            raise UserError('You are Allowed To Add 2 Lines Only')
            # employee.count = self.env['drs2.employee'].search_count([('dep_id', '=', self.id)])

    def get_loan_credit(self):
        loans = self.env['hr.loan'].search(
            [('employee_id.id', '=', self.employee_name.id), ('state', 'in', ['open', 'suspended'])])
        print(loans, "get_loan_credit")
        for rec in self:
            for line in loans:
                rec.x_loan_and_credit_amount = abs(sum(line.mapped('balance')))
                print(abs(sum(line.mapped('balance'))), "dddddd")

    def get_journal_count(self):
        count = self.env['account.move'].search_count(
            [('id', '=', self.x_move_id.id),
             ('state', '!=', 'cancel')])
        self.x_journal_count = count

    def get_vacation_payment_count_count(self):
        count = self.env['hr.settlement'].search_count(
            [('x_related_is_vacation_payment', '=', True),
             ('state', '!=', 'cancel'), ('employee_name', '=', self.employee_name.id)])
        self.x_vacation_payment_count = count

    def action_view_accounting_entry(self):
        return {
            'name': _('Accounting Entry'),
            'domain': [('id', '=', self.x_move_id.id)],
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def action_view_vacation_payment_settelment(self):
        return {
            'name': _('Vacation Payments'),
            'domain': [('x_related_is_vacation_payment', '=', True), ('employee_name', '=', self.employee_name.id)],
            'res_model': 'hr.settlement',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    @api.depends('employee_name')
    def salary_per_day(self):
        for rec in self:
            rec.x_salary_per_day = (rec.basic_salary * 12) / 365

    def working_days(self):
        for rec in self:
            if rec.x_related_is_settelment:
                d1 = datetime.strptime(str(rec.employee_name.date_of_join), '%Y-%m-%d')
                d2 = datetime.strptime(str(rec.verification_leaving_date), '%Y-%m-%d')
                d3 = d2 - d1
                rec.x_working_days = str(d3.days)
            elif rec.x_related_is_vacation_payment:
                d1 = datetime.strptime(str(rec.employee_name.date_of_join), '%Y-%m-%d')
                d2 = datetime.strptime(str(rec.date), '%Y-%m-%d')
                d3 = d2 - d1
                rec.x_working_days = str(d3.days)
            elif rec.x_related_is_vacation_payment:
                d1 = datetime.strptime(str(rec.employee_name.date_of_join), '%Y-%m-%d')
                d2 = datetime.strptime(str(rec.date), '%Y-%m-%d')
                d3 = d2 - d1
                rec.x_working_days = str(d3.days)
            else:
                rec.x_working_days = 0
            # elif rec.x_related_is_vacation_payment:
            #     d1 = datetime.strptime(str(rec.employee_name.date_of_join), '%Y-%m-%d')
            #     d2 = datetime.strptime(str(rec.date), '%Y-%m-%d')
            #     d3 = d2 - d1
            #     rec.x_working_days = str(d3.days)
            # else:
            #     rec.x_working_days = 0

    def vacation_lines(self):
        for rec in self:
            anl = ((rec.basic_salary * 12) / 365) * rec.x_annual_leave_taken
            ovt = ((rec.basic_salary * 12) / 365) * rec.x_overtime_leave_taken
            # if rec.x_annual_leave_taken:
            rec.x_vacation_payments = [
                (0, 0,
                 {'x_sett_id': self._context.get('active_id'),
                  'x_leave_type': 41,
                  'x_total_leaves_taken': rec.x_total_annual,
                  'x_leave': rec.x_annual_leave_taken,
                  'x_leaves_taken': abs(rec.x_annual_leave_timeoff),
                  'x_total': anl})]
            # if rec.x_overtime_leave_taken:
            rec.x_vacation_payments = [
                (0, 0, {'x_sett_id': self._context.get('active_id'),
                        'x_leave_type': 47,
                        'x_total_leaves_taken': rec.x_total_overtime,
                        'x_leave': rec.x_overtime_leave_taken,
                        'x_leaves_taken': abs(rec.x_overtime_leave_timeoff),
                        'x_total': ovt}),
            ]

            #     rec.x_vacation_payments = [
            #         (0, 0, {'x_sett_id': self._context.get('active_id'),
            #                 'x_leave_type': 41,
            #                 'x_total_leaves_taken_days': rec.x_total_annual,
            #                 'x_annual_leave': rec.x_annual_leave_taken,
            #                 'x_total': anl,
            #                 })]
            # if rec.x_overtime_leave_taken:
            #     rec.x_vacation_payments = [
            #         (0, 0, {'x_sett_id': self._context.get('active_id'),
            #                 'x_leave_type': 47,
            #                 'x_total_leaves_taken_days': rec.x_total_overtime,
            #                 'x_annual_leave': rec.x_overtime_leave_taken,
            #                 'x_total': ovt,
            #                 })
            # ]
            # ]

    @api.depends('employee_name')
    def _compute_annual_leave(self):
        for employee in self:
            annual_leave = self.env['hr.leave.report'].search([
                ('employee_id.id', '=', employee.employee_name.id),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('holiday_status_id.x_leave_types', '=', 'Annual Leave')
            ])
            annual_leave_allocation = self.env['hr.leave.report'].search([
                ('employee_id.id', '=', employee.employee_name.id),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('leave_type', '=', 'allocation'),
                ('holiday_status_id.x_leave_types', '=', 'Annual Leave')
            ])
            annual_leave_timeoff = self.env['hr.leave.report'].search([
                ('employee_id.id', '=', employee.employee_name.id),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('leave_type', '=', 'request'),
                ('holiday_status_id.x_leave_types', '=', 'Annual Leave')
            ])
            overtime_leave = self.env['hr.leave.report'].search([
                ('employee_id.id', '=', employee.employee_name.id),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('holiday_status_id.x_leave_types', '=', 'Overtime Leave')
            ])
            overtime_leave_allocation = self.env['hr.leave.report'].search([
                ('employee_id.id', '=', employee.employee_name.id),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('leave_type', '=', 'allocation'),
                ('holiday_status_id.x_leave_types', '=', 'Overtime Leave')
            ])
            annual_overtime_timeoff = self.env['hr.leave.report'].search([
                ('employee_id.id', '=', employee.employee_name.id),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('leave_type', '=', 'request'),
                ('holiday_status_id.x_leave_types', '=', 'Overtime Leave')
            ])
            employee.x_annual_leave_taken = sum(annual_leave.mapped('number_of_days'))
            employee.x_total_annual = sum(annual_leave_allocation.mapped('number_of_days'))
            employee.x_overtime_leave_taken = sum(overtime_leave.mapped('number_of_days'))
            employee.x_total_overtime = sum(overtime_leave_allocation.mapped('number_of_days'))
            employee.x_annual_leave_timeoff = sum(annual_leave_timeoff.mapped('number_of_days'))
            employee.x_overtime_leave_timeoff = sum(annual_overtime_timeoff.mapped('number_of_days'))

    def indemnity_lines(self):
        for rec in self:
            # if rec.indemnity_ids.x_total_working_days <= 1095:
            unpaid_leave = self.env['hr.leave.report'].search([
                ('employee_id.id', '=', rec.employee_name.id),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('holiday_status_id.name', '=', 'Unpaid Leave')
            ])
            unpaid = abs(sum(unpaid_leave.mapped('number_of_days')))
            # if rec.verification_leaving_date and rec.employee_name.date_of_join:
            #     d1 = datetime.strptime(str(rec.employee_name.date_of_join), '%Y-%m-%d')
            #     d2 = datetime.strptime(str(rec.verification_leaving_date), '%Y-%m-%d')
            #     d3 = d2 - d1
            #     verification_leaving_date = str(d3.days)
            # else:
            #     verification_leaving_date = 0

            if rec.x_working_days <= float(1095):
                working_dates = rec.x_working_days
            else:
                working_dates = 1095
            final_working_days = working_dates
            indemnity_balance = (final_working_days * 15) / 365
            indemnity_amount = ((rec.basic_salary * 12) / 365) * indemnity_balance

            rec.indemnity_ids = [
                (0, 0, {'indemnity_id': self._context.get('active_id'),
                        'x_total_working_days': working_dates,
                        'x_unpaid_leave': 0,
                        'x_period': 'Period1',
                        'x_date_of_join': rec.employee_name.date_of_join,
                        'x_date_to': rec.employee_name.date_of_join + relativedelta(days=working_dates),
                        'x_indemnity_balance': indemnity_balance,
                        'x_final_working_days': final_working_days,
                        'x_indemnity_amount': indemnity_amount})]
            if rec.x_working_days >= float(1095):
                rec.indemnity_ids = [
                    (0, 0, {'indemnity_id': self._context.get('active_id'),
                            'x_total_working_days': rec.x_working_days - 1 - 1095,
                            'x_unpaid_leave': unpaid,
                            'x_period': 'Period2',
                            'x_date_of_join': rec.employee_name.date_of_join + relativedelta(
                                days=working_dates) + relativedelta(days=1),
                            'x_date_to': rec.verification_leaving_date,
                            'x_indemnity_balance': (rec.x_working_days - 1 - 1095 - unpaid) * 30 / 365,
                            'x_final_working_days': (rec.x_working_days - 1 - 1095) - unpaid,
                            'x_indemnity_amount': ((rec.basic_salary * 12) / 365) * (
                                    (rec.x_working_days - 1095 - 1 - unpaid) * 30) / 365})]

    def action_vacation_payment(self):
        for rec in self:
            unpaid_leave = self.env['hr.leave.report'].search([
                ('employee_id.id', '=', rec.employee_name.id),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('holiday_status_id.name', '=', 'Unpaid Leave')
            ])
            unpaid = abs(sum(unpaid_leave.mapped('number_of_days')))
            if rec.x_working_days <= float(1095):
                working_dates = rec.x_working_days
            else:
                working_dates = 1095
            final_working_days = working_dates
            indemnity_balance = (final_working_days * 15) / 365
            indemnity_amount = ((rec.basic_salary * 12) / 365) * indemnity_balance

            rec.indemnity_vacation_payment_line = [
                (0, 0, {'indemnity_id': self._context.get('active_id'),
                        'x_total_working_days': working_dates,
                        'x_unpaid_leave': 0,
                        'x_period': 'Period1',
                        'x_date_of_join': rec.employee_name.date_of_join,
                        'x_date_to': rec.employee_name.date_of_join + relativedelta(days=working_dates),
                        'x_indemnity_balance': indemnity_balance,
                        'x_final_working_days': final_working_days,
                        'x_indemnity_amount': indemnity_amount})]
            if rec.x_working_days >= float(1095):
                rec.indemnity_vacation_payment_line = [
                    (0, 0, {'indemnity_id': self._context.get('active_id'),
                            'x_total_working_days': rec.x_working_days - 1 - 1095,
                            'x_unpaid_leave': unpaid,
                            'x_period': 'Period2',
                            'x_date_of_join': rec.employee_name.date_of_join + relativedelta(
                                days=working_dates) + relativedelta(days=1),
                            'x_date_to': rec.date,
                            'x_indemnity_balance': (rec.x_working_days - 1 - 1095 - unpaid) * 30 / 365,
                            'x_final_working_days': (rec.x_working_days - 1 - 1095) - unpaid,
                            'x_indemnity_amount': ((rec.basic_salary * 12) / 365) * (
                                    (rec.x_working_days - 1095 - 1 - unpaid) * 30) / 365})]
            # for rec in self:
            #     anual = self.env['anual.provision'].search(
            #         [('employee_name.id', '=', self.employee_name.id)])
            #     total = sum(anual.mapped('x_total'))
            #     indemnity = self.env['indemnity.provision'].search(
            #         [('employee_name.id', '=', self.employee_name.id)])
            #     total_indemnity = sum(indemnity.mapped('x_total'))
            #     rec.indemnity_generate = True
            #     rec.indemnity_lines()
            #     self.x_anual_proviosn = [
            #         (0, 0, {'anual_amount': sum(rec.x_vacation_payments.mapped('x_total')),
            #                 'anual_provision_amount': total,
            #                 'total': sum(rec.x_vacation_payments.mapped('x_total')) - total})]
            #
            #     self.x_indemnity_proviosn = [
            #         (0, 0, {'indemnity_amount': sum(amt.x_indemnity_amount for amt in rec.indemnity_ids),
            #                 'indemnity_provision_amount': total_indemnity,
            #                 'total': sum(amt.x_indemnity_amount for amt in rec.indemnity_ids) - total_indemnity})
            self.create_reference()
            rec.write({'state': 'approved'})

    def generate_indemnity(self):
        for rec in self:
            anual = self.env['anual.provision'].search(
                [('employee_name.id', '=', self.employee_name.id)])
            total = sum(anual.mapped('x_total'))
            indemnity = self.env['indemnity.provision'].search(
                [('employee_name.id', '=', self.employee_name.id)])
            total_indemnity = sum(indemnity.mapped('x_total'))
            rec.indemnity_generate = True
            rec.indemnity_lines()
            rec.vacation_lines()
            rec.get_loan_credit()
            # self.x_vacation_payments = [
            #     (0, 0, {'x_due_days': rec.x_vacation_payments.x_due_days,
            #             'x_vacation_payment': rec.x_vacation_payments.x_vacation_payment,
            #             'x_grand_total': rec.x_vacation_payments.x_grand_total})]
            self.x_employee_leaves = [
                (0, 0, {'settlement_annual_leave': rec.x_employee_leaves.settlement_annual_leave,
                        'settlement_overtime_leave': rec.x_employee_leaves.settlement_overtime_leave,
                        'x_annual_id': rec.x_employee_leaves.x_annual_id,
                        'x_overtime_id': rec.x_employee_leaves.x_overtime_id})]
            self.x_deduction_days = [
                (0, 0, {'difference_days': rec.x_deduction_days.difference_days,
                        'deduction_amount': rec.x_deduction_days.deduction_amount})]
            # self.x_anual_proviosn = [
            #     (0, 0, {'anual_amount': rec.x_vacation_payments.x_grand_total,
            #             'anual_provision_amount': total,
            #             'total': rec.x_vacation_payments.x_grand_total - total})]
            self.x_anual_proviosn = [
                (0, 0, {'anual_amount': sum(rec.x_vacation_payments.mapped('x_total')),
                        'anual_provision_amount': total,
                        'total': sum(rec.x_vacation_payments.mapped('x_total')) - total})]

            self.x_indemnity_proviosn = [
                (0, 0, {'indemnity_amount': sum(amt.x_indemnity_amount for amt in rec.indemnity_ids),
                        'indemnity_provision_amount': total_indemnity,
                        'total': sum(amt.x_indemnity_amount for amt in rec.indemnity_ids) - total_indemnity})]
        rec.write({'state': 'review_loans'})

    def compute_sheet(self):
        for rec in self:
            anual = self.env['anual.provision'].search(
                [('employee_name.id', '=', self.employee_name.id)])
            total = sum(anual.mapped('x_total'))
            # self.x_vacation_payments = [
            #     (0, 0, {'x_due_days': self.x_vacation_payments.x_due_days,
            #             'x_vacation_payment': self.x_vacation_payments.x_vacation_payment,
            #             'x_grand_total': self.x_vacation_payments.x_grand_total})]
            rec.vacation_lines()
            self.x_anual_proviosn = [
                (0, 0, {'anual_amount': sum(rec.x_vacation_payments.mapped('x_total')),
                        'anual_provision_amount': total,
                        'total': sum(rec.x_vacation_payments.mapped('x_total')) - total})]
            self.x_employee_leaves = [
                (0, 0, {'settlement_annual_leave': self.x_employee_leaves.settlement_annual_leave,
                        'settlement_overtime_leave': self.x_employee_leaves.settlement_overtime_leave,
                        'x_annual_id': self.x_employee_leaves.x_annual_id,
                        'x_overtime_id': self.x_employee_leaves.x_overtime_id})]
            self.x_deduction_days = [
                (0, 0, {'difference_days': self.x_deduction_days.difference_days,
                        'deduction_amount': self.x_deduction_days.deduction_amount})]
            self.create_reference()
            rec.write({'state': 'review_loans'})

    def compute_sheet_encashment(self):
        for rec in self:
            self.create_reference()
            rec.write({'state': 'final_review'})

    # def _send_data_to_review_loan_wizard(self):
    #     data = {}
    #     for rec in self:
    #         data = {
    #             'x_employee_name': rec.employee_name,
    #         }
    #     return True

    def action_review_loans(self):
        loans = self.env['hr.loan'].search(
            [('employee_id.id', '=', self.employee_name.id), ('state', 'in', ['open', 'suspended'])])
        ctx = dict(self.env.context)
        ctx.update({
            'default_x_employee_name': self.employee_name.id,
            'default_x_loan_ids': [(6, 0, loans.ids)],
            'default_x_id': self.id,
        })
        return {
            'name': _('Review Loans'),
            'res_model': 'review.loan',
            'view_mode': 'form',
            'views': [
                (self.env.ref('pabs_settlement.review_loans_wizard_view_form').id, 'form'),
            ],
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': ctx,
        }

    def action_create_slip(self):
        for rec in self:
            if rec.nationality.id != 23:
                if rec.x_related_is_settelment:
                    ctx = dict(rec.env.context)
                    print(ctx, "aaassdf")
                    ctx.update({
                        'default_employee_id': rec.employee_name.id,
                        'default_contract_id': rec.employee_name.contract_id.id,
                        'default_settlement_id': rec.id,
                        'default_date_to': rec.verification_leaving_date,
                        # 'default_input_line_ids': [
                        #             (0, 0, {'payslip_id': payslip.id, 'loan_installment_id': rec.id, 'date': payslip.date_to,
                        #                     'amount': to_pay})],
                        'default_input_line_ids': [
                            (0, 0, {'amount': sum(rec.x_deduction_days.mapped('deduction_amount')), 'x_is_true': False,
                                    'input_type_id'
                                    : self.env.ref('pabs_settlement.resignation_penalty').id}),
                            (0, 0,
                             {'amount': sum(rec.x_indemnity_proviosn.mapped('indemnity_provision_amount')),
                              'x_is_true': False, 'input_type_id'
                              : self.env.ref('pabs_settlement.indemnity_provision').id}),
                            (
                                0, 0,
                                {'amount': sum(rec.x_anual_proviosn.mapped('anual_provision_amount')),
                                 'x_is_true': False,
                                 'input_type_id'
                                 : self.env.ref('pabs_settlement.annual_provision').id}),
                            (0, 0,
                             {'amount': sum(rec.x_indemnity_proviosn.mapped('total')), 'x_is_true': False,
                              'input_type_id'
                              : self.env.ref('pabs_settlement.indemnity_expense').id}),
                            (0, 0, {'amount': sum(rec.x_anual_proviosn.mapped('total')), 'x_is_true': False,
                                    'input_type_id'
                                    : self.env.ref('pabs_settlement.annual_expense').id}),
                            (0, 0, {'amount': rec.ticket_covered_price, 'x_is_true': False,
                                    'input_type_id'
                                    : self.env.ref('pabs_settlement.covered_ticket_price').id}),
                        ],
                    })
            if rec.nationality.id != 23:
                if rec.x_related_is_vacation_payment:
                    ctx = dict(rec.env.context)
                    print(ctx, "aaassdf")
                    ctx.update({
                        'default_employee_id': rec.employee_name.id,
                        'default_contract_id': rec.employee_name.contract_id.id,
                        'default_settlement_id': rec.id,
                        'default_date_to': rec.date,
                        'default_input_line_ids': [
                            (0, 0, {'amount': rec.x_applied_amount, 'x_is_true': False,
                                    'input_type_id'
                                    : self.env.ref('pabs_settlement.indemnity_vacation_payment').id}),
                            (0, 0, {'amount': rec.x_deduct_amount, 'x_is_true': False,
                                    'input_type_id'
                                    : self.env.ref('pabs_settlement.vacation_payment_deduction').id}),
                            (0, 0,
                             {'amount': sum(rec.vacation_payment_line.mapped('total_amount')),
                              'x_is_true': False, 'input_type_id'
                              : self.env.ref('pabs_settlement.encashment_vacation_payment').id}),
                            (0, 0, {'amount': rec.ticket_covered_price, 'x_is_true': False,
                                    'input_type_id'
                                    : self.env.ref('pabs_settlement.covered_ticket_price').id}),
                            # (
                            #     0, 0,
                            #     {'amount': sum(rec.x_anual_proviosn.mapped('anual_provision_amount')),
                            #      'x_is_true': False,
                            #      'input_type_id'
                            #      : self.env.ref('pabs_settlement.annual_provision').id}),
                            # (0, 0,
                            #  {'amount': sum(rec.x_indemnity_proviosn.mapped('total')), 'x_is_true': False,
                            #   'input_type_id'
                            #   : self.env.ref('pabs_settlement.indemnity_expense').id}),
                            # (0, 0, {'amount': sum(rec.x_anual_proviosn.mapped('total')), 'x_is_true': False,
                            #         'input_type_id'
                            #         : self.env.ref('pabs_settlement.annual_expense').id}),
                            # (0, 0, {'amount': rec.ticket_covered_price, 'x_is_true': False,
                            #         'input_type_id'
                            #         : self.env.ref('pabs_settlement.covered_ticket_price').id}),
                        ],
                    })
            if rec.nationality.id == 23:
                ctx = dict(rec.env.context)
                print(ctx, "aaassdf")
                ctx.update({
                    'default_employee_id': rec.employee_name.id,
                    'default_contract_id': rec.employee_name.contract_id.id,
                    'default_settlement_id': rec.id,
                    'default_date_to': rec.verification_leaving_date,
                    # 'default_input_line_ids': [
                    #             (0, 0, {'payslip_id': payslip.id, 'loan_installment_id': rec.id, 'date': payslip.date_to,
                    #                     'amount': to_pay})],
                    'default_input_line_ids': [
                        (0, 0, {'amount': sum(rec.x_deduction_days.mapped('deduction_amount')), 'x_is_true': False,
                                'input_type_id'
                                : self.env.ref('pabs_settlement.resignation_penalty').id}),
                        (0, 0,
                         {'amount': sum(rec.x_anual_proviosn.mapped('anual_provision_amount')), 'x_is_true': False,
                          'input_type_id'
                          : self.env.ref('pabs_settlement.annual_provision').id}),
                        (0, 0, {'amount': sum(rec.x_anual_proviosn.mapped('total')), 'x_is_true': False,
                                'input_type_id'
                                : self.env.ref('pabs_settlement.annual_expense').id}),
                    ],
                })
        return {
            'name': _('Create Final Slip'),
            'res_model': 'hr.payslip',
            'view_mode': 'form',
            # 'views': [
            #     (self.env.ref('pabs_settlement.review_loans_wizard_view_form').id, 'form'),
            # ],
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': ctx,
        }

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state == 'validated':
                if not rec.x_move_id:
                    rec.write({'state': 'draft'})
                else:
                    raise UserError(_('You Have To Delete Journal Entry....!!!Try Again'))
            return True

    def action_final_review(self):
        for rec in self:
            rec.write({'state': 'validated'})

    @api.depends('employee_name.name', 'settlement_type.name')
    def concat_name(self):
        for rec in self:
            if rec.employee_name:
                if rec.settlement_type:
                    print(rec.create_date)
                    if rec.create_date:
                        rec.name = rec.employee_name.name + ' ' + str(rec.settlement_type.name) + ' ' + str(rec.create_date.date())
                    else:
                        rec.name = rec.employee_name.name + ' ' + str(rec.settlement_type.name)
                else:
                    rec.name = ""
            else:
                rec.name = ""

                    # def last_basic_salary(self):
    #     # [len(rec.employee_name.slip_ids) - 1]
    #     for rec in self:
    #         for record in rec.employee_name.slip_ids.search([('state', '=', 'done')],
    #                                                         order='id desc', limit=1):
    #             print(record, "sssss")
    #             rec.basic_salary = record.basic_wage

    def last_net_salary(self):
        for rec in self:
            for record in rec.employee_name.slip_ids[len(rec.employee_name.slip_ids) - 1]:
                rec.Last_month_salary = record.net_wage

    def salary_for_day(self):
        for rec in self:
            rec.salary_per_day = (rec.basic_salary * 12) / 365

    # def annual_leaves(self):
    #     for employee in self:
    #         annual_leave = self.env['hr.leave.report'].search([
    #             ('employee_id.id', '=', employee.employee_name.id),
    #             ('holiday_status_id.active', '=', True),
    #             ('state', '=', 'validate'),
    #             ('holiday_status_id.x_leave_types', '=', 'Annual Leave')
    #         ])
    #         employee.x_annual_leave = sum(annual_leave.mapped('number_of_days'))
    #         employee.settlement_annual_leave = sum(annual_leave.mapped('number_of_days'))
    #
    # def _compute_overtime_leave(self):
    #     for employee in self:
    #         overtime_leave = self.env['hr.leave.report'].search([
    #             ('employee_id.id', '=', employee.employee_name.id),
    #             ('holiday_status_id.active', '=', True),
    #             ('state', '=', 'validate'),
    #             ('holiday_status_id.x_leave_types', '=', 'Overtime Leave')
    #         ])
    #         employee.x_overtime_leave = sum(overtime_leave.mapped('number_of_days'))
    #         employee.settlement_overtime_leave = sum(overtime_leave.mapped('number_of_days'))

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, rec.employee_name.name + ' ' + ' ' + str(rec.date)))
        return result

    def total_duration_of_work(self):
        for rec in self:
            work = self.env['hr.work.entry'].search([
                ('employee_id.id', '=', rec.employee_name.id), ('state', '=', 'validated'),
                ('work_entry_type_id.name', '=', 'Attendance')])
            # list = []
            # sum = 0
            # print(work.mapped('duration'), 'fileddddd')
            # for line in work:
            #     # list.append(line.id)
            #     # print(list)
            #     sum += line.duration
            rec.duration_of_work = sum(work.mapped('duration'))

    def action_contract_expired(self):
        for rec in self:
            for line in rec.x_employee_contract:
                line.write({'state': 'close'})

    # def create_annual_provision(self):
    #     for rec in self:
    #         for line in rec.x_anual_proviosn:
    #             vals = {
    #                 'employee_name': rec.employee_name.id,
    #                 'name': rec.name,
    #                 'x_total': -line.total,
    #             }
    #             annual = self.env['anual.provision'].create(vals)
    #             print(annual, "aaaa")

    def create_indemnity_provision(self):
        for rec in self:
            for lines in rec.x_indemnity_proviosn:
                vals = {
                    'employee_name': rec.employee_name.id,
                    'name': rec.name,
                    'x_total': -lines.total,
                }
                indem = self.env['indemnity.provision'].create(vals)
                print(indem, "indem")

    def create_anual_provision_encashment(self):
        for rec in self:
            for line in self.x_encashment_leaves:
                if line.x_leave_type.code == "ANL":
                    vals = {
                        'employee_name': rec.employee_name.id,
                        'name': rec.name,
                        'x_date': rec.create_date,
                        'x_rule': 'ANL',
                        'x_reference': rec.x_name,
                        'x_total': -line.total_amount,
                    }
                    anual = self.env['anual.provision'].create(vals)

    def unlink(self):
        for rec in self:
            if rec.state == 'validated':
                raise UserError(_('It is not allowed to delete a Settlement that already validated.'))
            return super(HrSettlement, self).unlink()

    def action_validate(self):
        for rec in self:
            if rec.x_related_is_settelment:
                if rec.nationality.id != 23:
                    # air_ticket_account = {
                    #     'name': rec.name,
                    #     'debit': abs(rec.ticket_price),
                    #     'credit': 0.0,
                    #     'account_id': rec.settlement_type.x_air_ticket_account.id,
                    # }
                    # annual_leave_account = {
                    #     'name': rec.name,
                    #     'debit': abs(sum(vac.x_vacation_payment for vac in rec.x_vacation_payments)),
                    #     'credit': 0.0,
                    #     'account_id': rec.settlement_type.x_annual_leave_account.id,
                    # }
                    # indemnity_account = {
                    #     'name': rec.name,
                    #     'debit': abs(sum(amt.x_indemnity_amount for amt in rec.indemnity_ids)),
                    #     'credit': 0.0,
                    #     'account_id': rec.settlement_type.x_indemnity_account.id,
                    # }
                    # payable_account = {
                    #     'name': rec.name,
                    #     'debit': 0.0,
                    #     'credit': abs(
                    #         sum(amt.x_indemnity_amount for amt in
                    #             rec.indemnity_ids) + sum(
                    #             vac.x_vacation_payment for vac in rec.x_vacation_payments) + rec.ticket_price),
                    #     'account_id': rec.settlement_type.x_payable_account.id,
                    # }
                    # vals = {
                    #     'date': rec.date,
                    #     'journal_id': rec.settlement_type.journal_id.id,
                    #     'company_id': rec.company_id.id,
                    #     'ref': rec.name,
                    #     'type': 'entry',
                    #     'line_ids': [(0, 0, air_ticket_account), (0, 0, annual_leave_account),
                    #                  (0, 0, indemnity_account),
                    #                  (0, 0, payable_account)]
                    # }
                    self.create_annual_leave()
                    self.create_overtime_leve()
                    self.action_contract_expired()
                    # self.create_annual_provision()
                    self.create_indemnity_provision()
                    # move = self.env['account.move'].create(vals)
                    # move.post()
                    # self.x_move_id = move
                    rec.write({'state': 'validated'})
                    if rec.x_related_is_settelment:
                        rec.employee_name.active = False

            if rec.x_related_is_settelment:
                if rec.nationality.id == 23:
                    # annual_leave_account = {
                    #     'name': rec.name,
                    #     'debit': abs(sum(vac.x_vacation_payment for vac in rec.x_vacation_payments)),
                    #     'credit': 0.0,
                    #     'account_id': rec.settlement_type.x_annual_leave_account.id,
                    # }
                    # payable_account = {
                    #     'name': rec.name,
                    #     'debit': 0.0,
                    #     'credit': abs(
                    #         sum(amt.x_indemnity_amount for amt in
                    #             rec.indemnity_ids) + sum(vac.x_vacation_payment for vac in rec.x_vacation_payments)),
                    #     'account_id': rec.settlement_type.x_payable_account.id,
                    # }
                    # vals = {
                    #     'date': rec.date,
                    #     'journal_id': rec.settlement_type.journal_id.id,
                    #     'company_id': rec.company_id.id,
                    #     'ref': rec.name,
                    #     'type': 'entry',
                    #     'line_ids': [(0, 0, annual_leave_account), (0, 0, payable_account)]
                    # }
                    self.create_annual_leave()
                    self.create_overtime_leve()
                    self.action_contract_expired()
                    # self.create_annual_provision()

                    # move = self.env['account.move'].create(vals)
                    # move.post()
                    # self.x_move_id = move
                    rec.write({'state': 'validated'})
                    if rec.x_related_is_settelment:
                        rec.employee_name.active = False

            # if rec.x_related_is_encashment:
            #     a = 0.0
            #     b = 0.0
            #     for line in self.x_encashment_leaves:
            #         if line.x_leave_type.code == "ANL":
            #             a = line.total_amount
            #         elif line.x_leave_type.code == "OVTL":
            #             b = line.total_amount
            #         else:
            #             a = 0.0
            #             b = 0.0
            #
            #     annual_leave_account = {
            #         'name': rec.name,
            #         'debit': abs(a),
            #         'credit': 0.0,
            #         'account_id': rec.settlement_type.x_annual_leave_account.id,
            #     }
            #     overtime_account = {
            #         'name': rec.name,
            #         'debit': abs(b),
            #         'credit': 0.0,
            #         'account_id': rec.settlement_type.x_overtime_account.id,
            #     }
            #     payable_account = {
            #         'name': rec.name,
            #         'debit': 0.0,
            #         'credit': abs(a) + abs(b),
            #         'account_id': rec.settlement_type.x_payable_account.id,
            #     }
            #     vals = {
            #         'date': rec.date,
            #         'journal_id': rec.settlement_type.journal_id.id,
            #         'company_id': rec.company_id.id,
            #         'ref': rec.name,
            #         'type': 'entry',
            #         'line_ids': [(0, 0, annual_leave_account), (0, 0, overtime_account), (0, 0, payable_account)]
            #     }
            #     self.create_annual_leave()
            #     self.create_overtime_leve()
            #     move = self.env['account.move'].create(vals)
            #     move.post()

            if rec.x_related_is_encashment:
                a = 0.0
                b = 0.0
                for line in self.x_encashment_leaves:
                    if line.x_leave_type.code == "ANL":
                        a = line.total_amount
                    elif line.x_leave_type.code == "OVTL":
                        b = line.total_amount
                    else:
                        a = 0.0
                        b = 0.0

                annual_leave_account = {
                    'name': rec.name,
                    'debit': abs(a),
                    'credit': 0.0,
                    'account_id': rec.settlement_type.x_annual_leave_account.id,
                }
                overtime_account = {
                    'name': rec.name,
                    'debit': abs(b),
                    'credit': 0.0,
                    'account_id': rec.settlement_type.x_overtime_account.id,
                }
                payable_account = {
                    'name': rec.name,
                    'debit': 0.0,
                    'credit': abs(a) + abs(b),
                    'account_id': rec.settlement_type.x_payable_account.id,
                }
                vals = {
                    'date': rec.date,
                    'journal_id': rec.settlement_type.journal_id.id,
                    'company_id': rec.company_id.id,
                    'ref': rec.name,
                    'type': 'entry',
                    'line_ids': [(0, 0, annual_leave_account), (0, 0, overtime_account), (0, 0, payable_account)]
                }
                self.create_annual_leave()
                self.create_overtime_leve()
                move = self.env['account.move'].create(vals)
                move.post()
                self.x_move_id = move
                self.create_anual_provision_encashment()

            if rec.x_related_is_vacation_payment:
                a = 0.0
                b = 0.0
                for line in self.vacation_payment_line:
                    if line.x_leave_type.code == "ANL":
                        a = line.total_amount
                    elif line.x_leave_type.code == "OVTL":
                        b = line.total_amount
                    else:
                        a = 0.0
                        b = 0.0

                annual_leave_account = {
                    'name': rec.name,
                    'debit': abs(a),
                    'credit': 0.0,
                    'account_id': rec.settlement_type.x_annual_leave_account.id,
                }
                overtime_account = {
                    'name': rec.name,
                    'debit': abs(b),
                    'credit': 0.0,
                    'account_id': rec.settlement_type.x_overtime_account.id,
                }
                payable_account = {
                    'name': rec.name,
                    'debit': 0.0,
                    'credit': abs(a) + abs(b),
                    'account_id': rec.settlement_type.x_payable_account.id,
                }
                vals = {
                    'date': rec.date,
                    'journal_id': rec.settlement_type.journal_id.id,
                    'company_id': rec.company_id.id,
                    'ref': rec.name,
                    'type': 'entry',
                    'line_ids': [(0, 0, annual_leave_account), (0, 0, overtime_account), (0, 0, payable_account)]
                }
                print(annual_leave_account, "a")
                print(overtime_account, "b")
                print(payable_account, "c")
                self.create_annual_leave()
                self.create_overtime_leve()
                self.create_unpaid_leave()
                if rec.employee_name.x_is_expats:
                    self.employee_name.action_suspend()
                move = self.env['account.move'].create(vals)
                move.post()
        rec.write({'state': 'validated'})

    def last_rejoin_date(self):
        for rec in self:
            date = self.env['hr.rejoin.line'].search([('rejoin_id.employee_id.id', '=', rec.employee_name.id)],
                                                     order='id desc', limit=1)
            # rec.rejoin_date = date.start_date
            rec.rejoin_date = date.employee_rejoin_date

    def create_annual_leave(self):
        for rec in self:
            if rec.x_related_is_encashment:
                for line in self.x_encashment_leaves:
                    if line.x_leave_type.code == "ANL":
                        a = line.x_requested_days
                    else:
                        a = 0.0
                    if a != 0.0:
                        vals = {
                            'employee_id': rec.employee_name.id,
                            'name': rec.name,
                            'request_date_from': rec.date,
                            'request_date_to': str(rec.date),
                            'holiday_status_id': 41,
                            'number_of_days': a,
                            'state': 'draft',
                        }
                        anual = self.env['hr.leave'].create(vals)
                        rec.x_encashment_leaves.x_annual_id = anual
                        anual.action_confirm()
                        anual.action_validate()
            if rec.x_related_is_vacation_payment:
                for line in self.vacation_payment_line:
                    if line.x_leave_type.code == "ANL":
                        a = line.x_requested_days
                        annual_date_from = line.x_date_from
                        annual_date_to = line.x_date_from + timedelta(days=line.x_requested_days)
                        print(a, "aaaa")
                    else:
                        a = 0.0
                        print(a, "BBBB")
                    if a != 0.0:
                        vals = {
                            'employee_id': rec.employee_name.id,
                            'name': rec.name,
                            'request_date_from': annual_date_from,
                            'request_date_to': annual_date_to,
                            'holiday_status_id': 41,
                            'number_of_days': a,
                            'state': 'draft',
                        }
                        print(vals, "CCCC")
                        anual = self.env['hr.leave'].create(vals)
                        print(anual, 'dddd')
                        rec.vacation_payment_line.x_annual_id = anual
                        anual.action_confirm()
                        anual.action_validate()
            if rec.x_related_is_settelment:
                if rec.x_employee_leaves.settlement_annual_leave != 0:
                    vals = {
                        'employee_id': rec.employee_name.id,
                        'name': rec.name,
                        'request_date_from': rec.date,
                        'request_date_to': str(rec.date),
                        'holiday_status_id': 41,
                        'number_of_days': rec.x_employee_leaves.settlement_annual_leave,
                        'state': 'draft',
                    }
                    anual = self.env['hr.leave'].create(vals)
                    rec.x_employee_leaves.x_annual_id = anual
                    anual.action_confirm()
                    anual.action_validate()

    # @api.depends('employee_name')
    # def annual_leaves(self):
    #     for employee in self:
    #         annual_leave = self.env['hr.leave.report'].search([
    #             ('employee_id.id', '=', employee.employee_name.id),
    #             ('holiday_status_id.active', '=', True),
    #             ('state', '=', 'validate'),
    #             ('holiday_status_id.x_leave_types', '=', 'Annual Leave')
    #         ])
    #         employee.x_annual_leave = sum(annual_leave.mapped('number_of_days'))
    #
    # @api.depends('employee_name')
    # def _compute_overtime_leave(self):
    #     for employee in self:
    #         overtime_leave = self.env['hr.leave.report'].search([
    #             ('employee_id.id', '=', employee.employee_name.id),
    #             ('holiday_status_id.active', '=', True),
    #             ('state', '=', 'validate'),
    #             ('holiday_status_id.x_leave_types', '=', 'Overtime Leave')
    #         ])
    #         employee.x_overtime_leave = sum(overtime_leave.mapped('number_of_days'))

    def create_unpaid_leave(self):
        for rec in self:
            if rec.x_related_is_vacation_payment:
                for line in self.vacation_payment_line:
                    if line.x_leave_type.code == "ANL":
                        a = line.x_unpaid_days
                        annual_date_from = line.x_date_from + timedelta(days=line.x_requested_days) + timedelta(days=1)
                        annual_date_to = line.x_date_to
                        if a != 0.0:
                            if line.x_leave_type.code == "ANL":
                                vals = {
                                    'employee_id': rec.employee_name.id,
                                    'name': rec.name,
                                    'request_date_from': annual_date_from,
                                    'request_date_to': annual_date_to,
                                    'holiday_status_id': 44,
                                    'number_of_days': a,
                                    'state': 'draft',
                                }
                                anual = self.env['hr.leave'].create(vals)
                                # rec.vacation_payment_line.x_annual_id = anual
                                anual.action_confirm()
                                anual.action_validate()
                        print(a, "aaaa")
                    if line.x_leave_type.code == "OVTL":
                        a = line.x_unpaid_days
                        overtime_date_from =  line.x_date_from + timedelta(days=line.x_requested_days) + timedelta(days=1)
                        overtime_date_to = line.x_date_to
                        if line.x_leave_type.code == "OVTL":
                            vals = {
                                'employee_id': rec.employee_name.id,
                                'name': rec.name,
                                'request_date_from': overtime_date_from,
                                'request_date_to': overtime_date_to,
                                'holiday_status_id': 44,
                                'number_of_days': a,
                                'state': 'draft',
                            }
                            overtime = self.env['hr.leave'].create(vals)
                            # rec.vacation_payment_line.x_annual_id = overtime
                            overtime.action_confirm()
                            overtime.action_validate()
                    else:
                        a = 0.0
                        print(a, "BBBB")
                    # if a != 0.0:
                    #     if line.x_leave_type.code == "ANL":
                    #         vals = {
                    #             'employee_id': rec.employee_name.id,
                    #             'name': rec.name,
                    #             'request_date_from': annual_date_from,
                    #             'request_date_to': annual_date_to,
                    #             'holiday_status_id': 41,
                    #             'number_of_days': a,
                    #             'state': 'draft',
                    #         }
                    #         anual = self.env['hr.leave'].create(vals)
                    #         rec.vacation_payment_line.x_annual_id = anual
                    #         anual.action_confirm()
                    #         anual.action_validate()
                    #     if line.x_leave_type.code == "OVTL":
                    #         vals = {
                    #             'employee_id': rec.employee_name.id,
                    #             'name': rec.name,
                    #             'request_date_from': overtime_date_from,
                    #             'request_date_to': overtime_date_to,
                    #             'holiday_status_id': 41,
                    #             'number_of_days': a,
                    #             'state': 'draft',
                    #         }
                    #         anual = self.env['hr.leave'].create(vals)
                    #         rec.vacation_payment_line.x_annual_id = anual
                    #         anual.action_confirm()
                    #         anual.action_validate()


    def create_overtime_leve(self):
        for rec in self:
            if rec.x_related_is_encashment:
                for line in self.x_encashment_leaves:
                    if line.x_leave_type.code == "OVTL":
                        a = line.x_requested_days
                    else:
                        a = 0.0
                    if a != 0.0:
                        vals = {
                            'employee_id': rec.employee_name.id,
                            'name': rec.name,
                            'request_date_from': rec.date,
                            'request_date_to': str(rec.date),
                            'holiday_status_id': 47,
                            'number_of_days': a,
                            'state': 'draft',
                        }
                        overtime = self.env['hr.leave'].create(vals)
                        rec.x_encashment_leaves.x_overtime_id = overtime
                        overtime.action_confirm()
                        overtime.action_validate()
            if rec.x_related_is_vacation_payment:
                for line in self.vacation_payment_line:
                    if line.x_leave_type.code == "OVTL":
                        a = line.x_requested_days
                        overtime_date_from = line.x_date_from
                        overtime_date_to = line.x_date_from + timedelta(days=line.x_requested_days)
                    else:
                        a = 0.0
                    if a != 0.0:
                        vals = {
                            'employee_id': rec.employee_name.id,
                            'name': rec.name,
                            'request_date_from': overtime_date_from,
                            'request_date_to': overtime_date_to,
                            'holiday_status_id': 47,
                            'number_of_days': a,
                            'state': 'draft',
                        }
                        overtime = self.env['hr.leave'].create(vals)
                        rec.x_encashment_leaves.x_overtime_id = overtime
                        overtime.action_confirm()
                        overtime.action_validate()
            if rec.x_related_is_settelment:
                if rec.x_employee_leaves.settlement_overtime_leave != 0:
                    vals = {
                        'employee_id': rec.employee_name.id,
                        'name': rec.name,
                        'request_date_from': rec.date,
                        'request_date_to': str(rec.date),
                        'holiday_status_id': 47,
                        'number_of_days': rec.x_employee_leaves.settlement_overtime_leave,
                        'state': 'draft',
                    }
                    overtime = self.env['hr.leave'].create(vals)
                    rec.x_employee_leaves.x_overtime_id = overtime
                    overtime.action_confirm()
                    overtime.action_validate()

    def create_reference(self):
        print("15151515")
        if self.x_name == 'New':
            seq = self.settlement_type
            if seq and seq.x_sequence_id:
                self['x_name'] = seq.x_sequence_id.next_by_id() or _('New')
        return True

    def calculate_date(self):
        for rec in self:
            if rec.verification_leaving_date and rec.resignation_date:
                d1 = datetime.strptime(str(self.verification_leaving_date), '%Y-%m-%d')
                d2 = datetime.strptime(str(self.resignation_date), '%Y-%m-%d')
                d4 = timedelta(rec.x_notice_period.period_countable)
                d5 = timedelta(days=1)
                d3 = (d2 + d4) - d1 - d5
                # a = calendar.monthrange(self.verification_leaving_date.year, self.verification_leaving_date.month)
                # print(a, ";;;;;;")
                # print(a[1], ";;;;;;")
                rec.x_count_days = str(d3.days)
                if rec.x_count_days > 0:
                    rec.x_deduction_days.difference_days = str(d3.days)
                if rec.x_count_days < 0:
                    rec.x_deduction_days.difference_days = 0
            else:
                rec.x_count_days = 0
                rec.x_deduction_days.difference_days = 0

    @api.depends('employee_name')
    def calculate_amount(self):
        # for rec in self:
        self.x_deduction_amount = 0
        if self.x_count_days > 0:
            self.x_deduction_amount = self.x_count_days * (self.basic_salary * 12) / 365
            self.x_deduction_days.deduction_amount = self.x_deduction_amount
            print(self.x_deduction_amount, "11")
        else:
            self.x_deduction_amount = 0
            self.x_deduction_days.deduction_amount = 0
            print(self.x_deduction_amount, "22")
        # self.total_amount = self.total_amount - self.x_deduction_amount
        # return

    def vac_total(self):
        for rec in self:
            rec.x_total_vacation = sum(rec.x_vacation_payments.mapped('x_total'))

    def input_total(self):
        for rec in self:
            rec.x_total_input = sum(rec.x_input_line.mapped('x_amount'))

    def indeminity_total(self):
        for rec in self:
            rec.x_total_indeminty = sum(rec.indemnity_ids.mapped('x_indemnity_amount'))

    def deduction_total(self):
        for rec in self:
            rec.x_total_deduction = sum(rec.x_deduction_days.mapped('deduction_amount'))

    def encashment_total(self):
        for rec in self:
            rec.x_total_encashment = sum(rec.x_encashment_leaves.mapped('total_amount'))

    def encashment_vacation_total(self):
        for rec in self:
            rec.x_total_encashemnt_payment = sum(rec.vacation_payment_line.mapped('total_amount'))

    def indeminity_vacation_total(self):
        for rec in self:
            rec.x_total_indeminity_payment = sum(rec.indemnity_vacation_payment_line.mapped('x_indemnity_amount'))

    # @api.depends('employee_name')
    def calculate_total_amount(self):
        for rec in self:
            rec.total_amount = 0
            if rec.nationality.id == 23:
                if rec.x_related_is_settelment:
                    rec.total_amount = rec.x_total_vacation - rec.x_total_deduction
                    print(rec.total_amount, "aa")
            if rec.nationality.id != 23:
                if rec.x_related_is_settelment:
                    rec.total_amount = rec.x_total_vacation + rec.x_total_indeminty - rec.x_total_deduction
                    print(rec.total_amount, "bb")
            if rec.x_related_is_encashment:
                rec.total_amount = rec.x_total_encashment
                print(rec.total_amount, "cc")
            if rec.nationality.id != 23:
                if rec.x_related_is_vacation_payment:
                    rec.total_amount = rec.x_total_encashemnt_payment + rec.x_applied_amount - rec.x_deduct_amount
                    # rec.total_amount = rec.x_total_encashemnt_payment + rec.x_total_indeminity_payment
                    print(rec.total_amount, "dd")
            # if not rec.x_related_is_settelment:
            #     rec.total_amount = rec.x_total_encashment
            #     print(rec.total_amount, "cc")

    def calculate_net_salary(self):
        for rec in self:
            if rec.x_employee_slips:
                rec.net_salary = rec.x_employee_slips.net_wage
            else:
                rec.net_salary = 0.0

    # class HrPayslipCreate(models.Model):
    #     _inherit = 'hr.payslip'
    #
    #     def action_payslip_done(self):
    #         """
    #             Generate the accounting entries related to the selected payslips
    #             A move is created for each journal and for each month.
    #         """
    #         res = super(HrPayslipCreate, self).action_payslip_done()
    #         precision = self.env['decimal.precision'].precision_get('Payroll')
    #
    #         # Add payslip without run
    #         payslips_to_post = self.filtered(lambda slip: not slip.payslip_run_id)
    #
    #         # Adding pay slips from a batch and deleting pay slips with a batch that is not ready for validation.
    #         payslip_runs = (self - payslips_to_post).mapped('payslip_run_id')
    #         for run in payslip_runs:
    #             if run._are_payslips_ready():
    #                 payslips_to_post |= run.slip_ids
    #
    #         # A payslip need to have a done state and not an accounting move.
    #         payslips_to_post = payslips_to_post.filtered(lambda slip: slip.state == 'done' and not slip.move_id)
    #
    #         # Check that a journal exists on all the structures
    #         if any(not payslip.struct_id for payslip in payslips_to_post):
    #             raise ValidationError(_('One of the contract for these payslips has no structure type.'))
    #         if any(not structure.journal_id for structure in payslips_to_post.mapped('struct_id')):
    #             raise ValidationError(_('One of the payroll structures has no account journal defined on it.'))
    #
    #         # Map all payslips by structure journal and pay slips month.
    #         # {'journal_id': {'month': [slip_ids]}}
    #         slip_mapped_data = {
    #             slip.struct_id.journal_id.id: {fields.Date().end_of(slip.date_to, 'month'): self.env['hr.payslip']} for slip
    #             in
    #             payslips_to_post}
    #         for slip in payslips_to_post:
    #             slip_mapped_data[slip.struct_id.journal_id.id][fields.Date().end_of(slip.date_to, 'month')] |= slip
    #
    #         for journal_id in slip_mapped_data:  # For each journal_id.
    #             for slip_date in slip_mapped_data[journal_id]:  # For each month.
    #                 line_ids = []
    #                 debit_sum = 0.0
    #                 credit_sum = 0.0
    #                 date = slip_date
    #                 move_dict = {
    #                     'narration': '',
    #                     'ref': date.strftime('%B %Y'),
    #                     'journal_id': journal_id,
    #                     'date': date,
    #                 }
    #
    #                 for slip in slip_mapped_data[journal_id][slip_date]:
    #                     move_dict['narration'] += slip.number or '' + ' - ' + slip.employee_id.name or ''
    #                     move_dict['narration'] += '\n'
    #                     for line in slip.line_ids.filtered(lambda line: line.category_id):
    #                         amount = -line.total if slip.credit_note else line.total
    #                         if line.code == 'NET':  # Check if the line is the 'Net Salary'.
    #                             for tmp_line in slip.line_ids.filtered(lambda line: line.category_id):
    #                                 if tmp_line.salary_rule_id.not_computed_in_net:  # Check if the rule must be computed in the 'Net Salary' or not.
    #                                     if amount > 0:
    #                                         amount -= abs(tmp_line.total)
    #                                     elif amount < 0:
    #                                         amount += abs(tmp_line.total)
    #                         if float_is_zero(amount, precision_digits=precision):
    #                             continue
    #                         debit_account_id = line.salary_rule_id.account_debit.id
    #                         credit_account_id = line.salary_rule_id.account_credit.id
    #
    #                         if debit_account_id:  # If the rule has a debit account.
    #                             debit = amount if amount > 0.0 else 0.0
    #                             credit = -amount if amount < 0.0 else 0.0
    #
    #                             existing_debit_lines = (
    #                                 line_id for line_id in line_ids if
    #                                 line_id['name'] == line.name
    #                                 and line_id['account_id'] == debit_account_id
    #                                 and ((line_id['debit'] > 0 and credit <= 0) or (line_id['credit'] > 0 and debit <= 0)))
    #                             debit_line = next(existing_debit_lines, False)
    #
    #                             if not debit_line:
    #                                 debit_line = {
    #                                     'name': line.name,
    #                                     'partner_id': False,
    #                                     'account_id': debit_account_id,
    #                                     'journal_id': slip.struct_id.journal_id.id,
    #                                     'date': date,
    #                                     'debit': debit,
    #                                     'credit': credit,
    #                                     'analytic_account_id': line.salary_rule_id.analytic_account_id.id or slip.contract_id.analytic_account_id.id,
    #                                 }
    #                                 line_ids.append(debit_line)
    #                             else:
    #                                 debit_line['debit'] += debit
    #                                 debit_line['credit'] += credit
    #
    #                         if credit_account_id:  # If the rule has a credit account.
    #                             debit = -amount if amount < 0.0 else 0.0
    #                             credit = amount if amount > 0.0 else 0.0
    #                             existing_credit_line = (
    #                                 line_id for line_id in line_ids if
    #                                 line_id['name'] == line.name
    #                                 and line_id['account_id'] == credit_account_id
    #                                 and (line_id['debit'] > 0 and credit <= 0) or (line_id['credit'] > 0 and debit <= 0)
    #                             )
    #                             credit_line = next(existing_credit_line, False)
    #
    #                             if not credit_line:
    #                                 credit_line = {
    #                                     'name': line.name,
    #                                     'partner_id': False,
    #                                     'account_id': credit_account_id,
    #                                     'journal_id': slip.struct_id.journal_id.id,
    #                                     'date': date,
    #                                     'debit': debit,
    #                                     'credit': credit,
    #                                     'analytic_account_id': line.salary_rule_id.analytic_account_id.id or slip.contract_id.analytic_account_id.id,
    #                                 }
    #                                 line_ids.append(credit_line)
    #                             else:
    #                                 credit_line['debit'] += debit
    #                                 credit_line['credit'] += credit
    #
    #                 for line_id in line_ids:  # Get the debit and credit sum.
    #                     debit_sum += line_id['debit']
    #                     credit_sum += line_id['credit']
    #
    #                 # The code below is called if there is an error in the balance between credit and debit sum.
    #                 if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
    #                     acc_id = slip.journal_id.default_credit_account_id.id
    #                     if not acc_id:
    #                         raise UserError(
    #                             _('The Expense Journal "%s" has not properly configured the Credit Account!') % (
    #                                 slip.journal_id.name))
    #                     existing_adjustment_line = (
    #                         line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
    #                     )
    #                     adjust_credit = next(existing_adjustment_line, False)
    #
    #                     if not adjust_credit:
    #                         adjust_credit = {
    #                             'name': _('Adjustment Entry'),
    #                             'partner_id': False,
    #                             'account_id': acc_id,
    #                             'journal_id': slip.journal_id.id,
    #                             'date': date,
    #                             'debit': 0.0,
    #                             'credit': debit_sum - credit_sum,
    #                         }
    #                         line_ids.append(adjust_credit)
    #                     else:
    #                         adjust_credit['credit'] = debit_sum - credit_sum
    #
    #                 elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
    #                     acc_id = slip.journal_id.default_debit_account_id.id
    #                     if not acc_id:
    #                         raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (
    #                             slip.journal_id.name))
    #                     existing_adjustment_line = (
    #                         line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
    #                     )
    #                     adjust_debit = next(existing_adjustment_line, False)
    #
    #                     if not adjust_debit:
    #                         adjust_debit = {
    #                             'name': _('Adjustment Entry'),
    #                             'partner_id': False,
    #                             'account_id': acc_id,
    #                             'journal_id': slip.journal_id.id,
    #                             'date': date,
    #                             'debit': credit_sum - debit_sum,
    #                             'credit': 0.0,
    #                         }
    #                         line_ids.append(adjust_debit)
    #                     else:
    #                         adjust_debit['debit'] = credit_sum - debit_sum
    #
    #                 # Add accounting lines in the move
    #                 move_dict['line_ids'] = [(0, 0, line_vals) for line_vals in line_ids]
    #                 move = self.env['account.move'].create(move_dict)
    #                 for slip in slip_mapped_data[journal_id][slip_date]:
    #                     slip.write({'move_id': move.id, 'date': date})
    #         return res
