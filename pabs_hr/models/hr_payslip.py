from babel.dates import format_date
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo.tools import date_utils
from odoo.tools.misc import format_date


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        self.company_id = employee.company_id
        if not self.contract_id or self.employee_id != self.contract_id.employee_id:  # Add a default contract if not already defined
            contracts = employee._get_contracts(date_from, date_to)

            if not contracts or not contracts[0].structure_type_id.default_struct_id:
                self.contract_id = False
                self.struct_id = False
                return
            self.contract_id = contracts[0]
            self.struct_id = contracts[0].structure_type_id.default_struct_id

        payslip_name = self.struct_id.payslip_name or _('Salary Slip')
        self.name = '%s - %s - %s' % (
            payslip_name, self.employee_id.name or '', format_date(self.env, self.date_to, date_format="MMMM y"))
        self.x_month_year_date_to = '%s' % (format_date(self.env, self.date_to, date_format="MMMM y"))

        if date_to > date_utils.end_of(fields.Date.today(), 'month'):
            self.warning_message = _(
                "This payslip can be erroneous! Work entries may not be generated for the period from %s to %s." %
                (date_utils.add(date_utils.end_of(fields.Date.today(), 'month'), days=1), date_from))
        else:
            self.warning_message = False

        self.worked_days_line_ids = self._get_new_worked_days_lines()

    # @api.model
    # def create(self, vals):
    #     result = super(HrPayslip, self).create(vals)
    #     self._update_line()
    #     return result
    #
    # def _update_line(self):
    #     worked_days = self.mapped('payslip_id')
    #     print(worked_days, "nnv")
    #     for work in worked_days:
    #         work_lines = self.filtered(lambda x: x.payslip_id == work)
    #         msg = "<b>" + _("The ordered quantity has been updated.") + "</b><ul>"
    #         print(work_lines, "aaasdddf")
    #         for line in work_lines:
    #             msg += "<li> %s:" % (line.work_entry_type_id.name,)
    #             # msg += "<br/>" + _("Type") + ": %s -> %s <br/>" % (
    #             #     line.product_uom_qty, float(values['product_uom_qty']),)
    #             # if line.product_id.type in ('consu', 'product'):
    #             #     msg += _("Delivered Quantity") + ": %s <br/>" % (line.qty_delivered,)
    #             # msg += _("Invoiced Quantity") + ": %s <br/>" % (line.qty_invoiced,)
    #             print(work, "aaaa")
    #         msg += "</ul>"
    #         work.message_post(body=msg)

    # def set_hour_and_days(self):
    #     res = {}
    #     for work_day in self.worked_days_line_ids:
    #         for line_id in self.line_ids:
    #             for rec in line_id.salary_rule_id.related_worked_days:
    #                 if work_day.name == rec.name:
    #                     line_id.hour = work_day.number_of_hours
    #                     line_id.day = work_day.number_of_days
    #             self.compute_for_set_hour = ''

    # @api.onchange('employee_id')
    # def restrict_payslip(self):
    #     for line in self.employee_id.slip_ids:
    #         if line.date_from >= self.date_from <= line.date_to:
    #             raise UserError(_('Slip Already Created'))
    #         elif line.date_from >= self.date_to <= line.date_to:
    #             raise UserError(_('Slip Already Created'))

    # def action_expats(self):
    #     for rec in self:
    #         if rec.employee_id.x_is_expats:
    #             raise UserError(_('This employee is expats'))
    #     return res

    @api.constrains('employee_id')
    def show_expats_warning(self):
        for rec in self:
            if rec.employee_id.x_is_expats:
                raise UserError(_('This employee is expats'))

    def action_hr_payslip_done(self):
        return {
            'name': _('Slip Confirmation'),
            'res_model': 'payslip.popup',
            'view_mode': 'form',
            'views': [
                (self.env.ref('pabs_hr.payslip_popup_wizard_view_form').id, 'form'),
            ],
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def _compute_how_many_days(self):
        for rec in self:
            if rec.date_from:
                date_end = rec.date_from + relativedelta(months=1)
                rec.x_month_days = (date_end - rec.date_from).days

    x_month_days = fields.Integer(string='Payslip Days', compute=_compute_how_many_days)
    x_work_month_days = fields.Integer(string='Working Days', compute='_compute_work_month_days')
    x_department = fields.Many2one('hr.department', string='Department', related='employee_id.department_id', store=True)
    name = fields.Char(string='Payslip Name', track_visibility='onchange', readonly=True, required=True,
                       states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', track_visibility='onchange', string='Contract', readonly=True,
                                  states={'draft': [('readonly', False)], 'verify': [('readonly', False)]},
                                  domain="[('company_id', '=', company_id)]")
    # x_leave_cal = fields.Many2one('hr.leave.report', 'Leaves')
    struct_id = fields.Many2one('hr.payroll.structure', track_visibility='onchange', string='Structure',
                                readonly=True, states={'draft': [('readonly', False)], 'verify': [('readonly', False)]},
                                help='Defines the rules that have to be applied to this payslip, accordingly '
                                     'to the contract chosen. If you let empty the field contract, this field isn\'t '
                                     'mandatory anymore and thus the rules applied will be all the rules set on the '
                                     'structure of all contracts of the employee valid for the chosen period')
    x_total_leaves = fields.Float('Total Number of Leave Days', compute='_compute_total_leaves')
    x_overtime_leaves = fields.Float('Number of Overtime Leave Days', compute='_compute_overtime_leaves')
    x_annual_leave = fields.Float('Number of Annual Leave Days', compute='_compute_annual_leave')
    remark = fields.Char(string='Remark')
    refunded = fields.Boolean(string='Refunded', default=False)
    date_from = fields.Date(string='From', readonly=True, track_visibility='onchange', required=True,
                            default=lambda self: fields.Date.to_string(
                                (datetime.now() + relativedelta(months=-1, day=25)).date()),
                            states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    date_to = fields.Date(string='To', track_visibility='onchange', readonly=True, required=True,
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(day=25, days=-1)).date()),
                          states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    x_month_year_date_to = fields.Char(string='Date By Month and Year')
    holiday_overtime_amount = fields.Monetary(compute='_compute_basic_net', string='1.5 Overtime Amount')
    holiday_overtime_hour = fields.Float(compute='_compute_work_hours', string='1.5 Overtime Hour')
    overtime_amount = fields.Monetary(compute='_compute_basic_net', string='1.25 Overtime Amount')
    overtime_hour = fields.Float(compute='_compute_work_hours', string='1.25 Overtime hour')
    weekly_off_overtime_hour = fields.Float(compute='_compute_work_hours', string='2.0 Overtime hour')
    weekly_off_overtime_amount = fields.Monetary(compute='_compute_basic_net', string='2.0 Overtime amount')
    loan = fields.Monetary(compute='_compute_basic_net', string='Loan')
    traffic_fine = fields.Monetary(compute='_compute_basic_net', string='Traffic Fine')
    miscellaneous_deduction = fields.Monetary(compute='_compute_basic_net', string='Miscellaneous Deduction')
    miscellaneous_earning = fields.Monetary(compute='_compute_basic_net', string='Miscellaneous Earning')
    attendance = fields.Float(compute='_compute_work_days', string='Attendance')
    sick_leave = fields.Float(compute='_compute_work_days', string='Sick Leave')
    death_leave = fields.Float(compute='_compute_work_days', string='Death Leave')
    absent = fields.Float(compute='_compute_work_days', string='Absent')
    half_sick_leave = fields.Float(compute='_compute_work_days', string='Half Sick Leave')
    unpaid_leave = fields.Float(compute='_compute_work_days', string='Unpaid Sick Leave')
    other_leave = fields.Float(compute='_compute_work_days', string='Other Leave')
    marriage_leave = fields.Float(compute='_compute_work_days', string='Marriage Leave')
    day_deduction = fields.Float(compute='_compute_basic_net', string='Day Deduction')
    total_deduction = fields.Float(compute='_compute_basic_net', string='Total Deduction')
    basic_sal = fields.Float(string='Basic', related='employee_id.contract_id.x_gross_salary')
    total_earnings = fields.Float(string='Total Earnings', compute='_compute_total_earnings')
    advance_salary = fields.Float(string='Advance Salary', compute='_compute_basic_net')
    credit_purchase = fields.Float(string='Credit Purchase', compute='_compute_basic_net')
    total_allowances = fields.Float(string='Total Allowances', compute='_compute_basic_net')
    unpaid_leaves = fields.Float(string='Unpaid Leave', compute='_compute_work_days')
    shortage = fields.Float(string='Shortage', compute='_compute_work_days')
    overtime_leave = fields.Float(string='Overtime Leave', compute='_compute_work_days')
    hajj_leave = fields.Float(string='Hajj Leave', compute='_compute_work_days')
    annual_leave = fields.Float(string='Annual Leave', compute='_compute_work_days')
    maternity_leave = fields.Float(string='Maternity Leave', compute='_compute_work_days')
    bonus = fields.Float(string='Bonus', compute='_compute_basic_net')
    reward = fields.Float(string='Reward', compute='_compute_basic_net')
    incentives = fields.Float(string='Incentives ', compute='_compute_basic_net')
    commission = fields.Float(string='Commission ', compute='_compute_basic_net')
    installment_refunds = fields.Float(string='Installment Refunds ', compute='_compute_basic_net')
    penalty = fields.Float(string='Penalty  ', compute='_compute_basic_net')
    x_category_id = fields.Char(string='Category', related='employee_id.category_ids.name')
    # x_settlement = fields.Many2one('hr.settlement', string='Settlement')
    #settlement_id = fields.Many2one('hr.settlement', string='Settlement', store=True)

    def compute_sheet(self):
        for rec in self:
            # Check if the employee join date is greater than the start date of the payslip
            if rec.employee_id.date_of_join > rec.date_from:
                # Add absent work entry type to the worked_days_line_ids (Only if it does not exist)
                # Check if the absent work entry type is exist
                absent_work_entry_type_id = self.env['hr.work.entry.type'].search([('code', '=', 'ABS')], limit=1)
                if absent_work_entry_type_id:
                    is_exist = self.env['hr.payslip.worked_days'].search([('work_entry_type_id', '=', absent_work_entry_type_id.id)], limit=1)
                    if not is_exist:
                        self.env['hr.payslip.worked_days'].create({
                            'payslip_id': rec.id,
                            'work_entry_type_id': absent_work_entry_type_id.id,
                            'number_of_days': 30 - rec.x_work_month_days,
                        })
        return super(HrPayslip, self).compute_sheet()

    @api.depends('date_from', 'date_to', 'employee_id.date_of_join')
    def _compute_work_month_days(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.employee_id:
                if rec.employee_id.date_of_join:
                    if rec.employee_id.date_of_join > rec.date_from:
                        rec.x_work_month_days = (rec.date_to - rec.employee_id.date_of_join).days+1
                    else:
                        date_end = rec.date_from + relativedelta(months=1)
                        rec.x_work_month_days = (date_end - rec.date_from).days
                else:
                    rec.x_work_month_days = 0
            else:
                rec.x_work_month_days = 0

    # compute_for_set_hour = fields.Float('Hour and Days', compute='set_hour_and_days')
    def get_anual_provision(self):
        for rec in self:
            for line_id in self.line_ids:
                if line_id.code == 'ALP':
                    vals = {
                        'employee_name': rec.employee_id.id,
                        'name': rec.name,
                        'x_date': rec.create_date,
                        'x_rule': 'ALP',
                        'x_reference': rec.number,
                        'x_total': line_id.total,
                    }
                    anual = self.env['anual.provision'].create(vals)
                if line_id.code == 'ANLPP':
                    vals1 = {
                        'employee_name': rec.employee_id.id,
                        'name': rec.name,
                        'x_date': rec.create_date,
                        'x_rule': 'ANLPP',
                        'x_reference': rec.number,
                        'x_total': -line_id.total,
                    }
                    anual1 = self.env['anual.provision'].create(vals1)
                if line_id.code == 'ALU':
                    vals2 = {
                        'employee_name': rec.employee_id.id,
                        'name': rec.name,
                        'x_date': rec.create_date,
                        'x_rule': 'ALU',
                        'x_reference': rec.number,
                        'x_total': -line_id.total,
                    }
                    anual2 = self.env['anual.provision'].create(vals2)
                if line_id.code == 'EVP':
                    vals2 = {
                        'employee_name': rec.employee_id.id,
                        'name': rec.name,
                        'x_date': rec.create_date,
                        'x_rule': 'EVP',
                        'x_reference': rec.number,
                        'x_total': -line_id.total,
                    }
                    anual3 = self.env['anual.provision'].create(vals2)
                if line_id.code == 'IVP':
                    vals2 = {
                        'employee_name': rec.employee_id.id,
                        'name': rec.name,
                        'x_date': rec.create_date,
                        'x_rule': 'IVP',
                        'x_reference': rec.number,
                        'x_total': -line_id.total,
                    }
                    anual3 = self.env['anual.provision'].create(vals2)
                # if line_id.code == 'ALP':
                #     sel.x_x_anual_provision = line_id.total

    def get_indemnity_provision(self):
        for rec in self:
            if rec.employee_id.country_id.id != 23:
                for line_id in self.line_ids:
                    if line_id.code == 'ID':
                        vals = {
                            'employee_name': rec.employee_id.id,
                            'name': rec.name,
                            'x_rule': 'ID',
                            'x_reference': rec.number,
                            'x_date': rec.create_date,
                            'x_total': line_id.total,
                        }
                        indemnity = self.env['indemnity.provision'].create(vals)
                    if line_id.code == 'INPP':
                        vals1 = {
                            'employee_name': rec.employee_id.id,
                            'name': rec.name,
                            'x_date': rec.create_date,
                            'x_rule': 'INPP',
                            'x_reference': rec.number,
                            'x_total': -line_id.total,
                        }
                        indemnity1 = self.env['indemnity.provision'].create(vals1)

    def _compute_total_earnings(self):
        for rec in self:
            rec.total_earnings = rec.basic_sal + rec.holiday_overtime_amount + rec.overtime_amount + rec.weekly_off_overtime_amount + \
                                 rec.bonus + rec.reward + rec.incentives + rec.commission + rec.installment_refunds + rec.miscellaneous_earning

    def _compute_basic_net(self):
        for payslip in self:
            payslip.basic_wage = payslip._get_salary_line_total('BASIC')
            payslip.net_wage = payslip._get_salary_line_total('NET')
            payslip.holiday_overtime_amount = payslip._get_salary_line_total('OV15')
            payslip.weekly_off_overtime_amount = payslip._get_salary_line_total('OVT20')
            payslip.overtime_amount = payslip._get_salary_line_total('OV125')
            payslip.loan = payslip._get_salary_line_total('LORP')
            payslip.advance_salary = payslip._get_salary_line_total('ADRP')
            payslip.credit_purchase = payslip._get_salary_line_total('CPI')
            payslip.traffic_fine = payslip._get_salary_line_total('TRFN')
            payslip.miscellaneous_deduction = payslip._get_salary_line_total('MSDED')
            payslip.day_deduction = payslip._get_salary_line_total('WAFN')
            payslip.total_deduction = payslip._get_salary_line_total('TDEC')
            payslip.total_allowances = payslip._get_salary_line_total('TALW')
            payslip.bonus = payslip._get_salary_line_total('BON')
            payslip.reward = payslip._get_salary_line_total('REW')
            payslip.incentives = payslip._get_salary_line_total('INC')
            payslip.commission = payslip._get_salary_line_total('COM')
            payslip.installment_refunds = payslip._get_salary_line_total('INSRF')
            payslip.penalty = payslip._get_salary_line_total('PEN')
            payslip.miscellaneous_earning = payslip._get_salary_line_total('MISCER')

    def _compute_work_days(self):
        for payslip in self:
            payslip.attendance = payslip._get_work_days('WORK100')
            payslip.sick_leave = payslip._get_work_days('FPSL')
            payslip.death_leave = payslip._get_work_days('DL')
            payslip.absent = payslip._get_work_days('ABS')
            payslip.half_sick_leave = payslip._get_work_days('HSL')
            payslip.unpaid_leave = payslip._get_work_days('USL')
            payslip.other_leave = payslip._get_work_days('OTL')
            payslip.marriage_leave = payslip._get_work_days('ML')
            payslip.unpaid_leaves = payslip._get_work_days('UNPAL')
            payslip.shortage = payslip._get_work_days('LAT')
            payslip.overtime_leave = payslip._get_work_days('OVTL')
            payslip.hajj_leave = payslip._get_work_days('HJL')
            payslip.annual_leave = payslip._get_work_days('ANL')
            payslip.maternity_leave = payslip._get_work_days('MTL')

    def _compute_work_hours(self):
        for payslip in self:
            payslip.weekly_off_overtime_hour = payslip._get_work_hours('OVT20')
            payslip.overtime_hour = payslip._get_work_hours('OV125')
            payslip.holiday_overtime_hour = payslip._get_work_hours('OV15')

    def _get_work_hours(self, code):
        lines = self.line_ids.filtered(lambda line: line.code == code)
        return sum([line.hour for line in lines])

    def _get_work_days(self, code):
        lines = self.worked_days_line_ids.filtered(lambda line: line.work_entry_type_id.code == code)
        return sum([line.number_of_days for line in lines])

    def _get_salary_line_total(self, code):
        lines = self.line_ids.filtered(lambda line: line.code == code)
        return sum([line.total for line in lines])

    # def _get_salary_line_hour(self, code):
    #     lines = self.worked_days_line_ids.filtered(lambda line: line.code == code)
    #     return sum([line.number_of_days for line in lines])

    def _compute_total_leaves(self):
        for employee in self:
            total_leaves = self.env['hr.leave.report'].search([
                ('employee_id.id', '=', employee.employee_id.id),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('holiday_status_id.x_leave_types', '!=', 0)
            ])
            employee.x_total_leaves = sum(total_leaves.mapped('number_of_days'))

    def _compute_overtime_leaves(self):
        for employee in self:
            overtime_leaves = self.env['hr.leave.report'].search([
                ('employee_id.id', '=', employee.employee_id.id),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('holiday_status_id.x_leave_types', '=', 'Overtime Leave')
            ])
            employee.x_overtime_leaves = sum(overtime_leaves.mapped('number_of_days'))

    def _compute_annual_leave(self):
        for employee in self:
            annual_leave = self.env['hr.leave.report'].search([
                ('employee_id.id', '=', employee.employee_id.id),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('holiday_status_id.x_leave_types', '=', 'Annual Leave')
            ])
            employee.x_annual_leave = sum(annual_leave.mapped('number_of_days'))

    def set_hour_and_days(self):
        for work_day in self.worked_days_line_ids:
            for line_id in self.line_ids:
                for rec in line_id.salary_rule_id.related_worked_days:
                    if work_day.code == rec.code:
                        line_id.hour = work_day.number_of_hours
                        line_id.day = work_day.number_of_days
    #
    # def compute_sheet(self):
    #     # self.restrict_payslip()
    #     res = super(HrPayslip, self).compute_sheet()
    #     for rec in self:
    #         if rec.settlement_id:
    #             rec.settlement_id.x_employee_slips = rec.id
    #             print(rec.settlement_id)
    #             rec.settlement_id.write({'state': 'final_review'})
    #     self.set_hour_and_days()
    #
    #     return res

    def refund_sheet(self):
        self.refunded = True
        res = super(HrPayslip, self).refund_sheet()
        return res

    @api.constrains('employee_id')
    def slips_restriction(self):
        if self.env.context.get('active_model') == 'hr.payslip':
            slip = self.employee_id.slip_ids.search(
                [('employee_id', '=', self.employee_id.id), ('id', '!=', self.id), ('id', '!=', False)])
            for slips in slip:
                if slips.date_from <= self.date_from <= slips.date_to:
                    raise UserError('Slip Already Created %s %s' % (slips.date_from, slips.name))
        # print(slip, "1111")
        # if slip:
        #     raise UserError('Slip Already Created')
        # else:
        #     return True

    # @api.onchange('employee_id')
    # def restrict_payslip(self):
    #     for line in self.employee_id.slip_ids:
    #         if line.date_from >= self.date_from <= line.date_to:
    #             raise UserError(_('Slip Already Created'))
    #         elif line.date_from >= self.date_to <= line.date_to:
    #             raise UserError(_('Slip Already Created'))

    # @api.onchange('employee_id')
    # def restrict_payslip(self):
    #     for line in self.employee_id.slip_ids:
    #         if line.date_from >= self.date_from <= line.date_to:
    #             raise UserError(_('Slip Already Created'))
    #         elif line.date_from >= self.date_to <= line.date_to:
    #             raise UserError(_('Slip Already Created'))

    # @api.onchange('employee_id')
    # def restrict_payslip(self):
    #     date_from = datetime.strftime(self.date_from, "%Y-%m")
    #     date_to = datetime.strftime(self.date_to, "%Y-%m")
    #     for line in self.employee_id.slip_ids:
    #         line_date_from = datetime.strftime(line.date_from, "%Y-%m")
    #         line_date_to = datetime.strftime(line.date_to, "%Y-%m")
    #         print(date_from == line_date_from, "linee from")
    #         print(date_to == line_date_to, "linee too")
    #         if line_date_from == date_from:
    #             raise UserError(_('Slip Already Created'))
    #         elif date_to == line_date_to:
    #             raise UserError(_('Slip Already Created'))

    # def date_range(self):


class HrPayslipEmployeesInherit(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    x_payment_method = fields.Selection([
        ('Cash', 'Cash'),
        ('Bank Transfer', 'Bank Transfer')],
        string='Payment Method', default='Cash')
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees',
                                    required=True)

    @api.onchange('x_payment_method')
    def _compute_employee_batch_slip(self):
        res = {}
        is_cash = self.env['hr.employee'].search(
            [('payment_method', '=', 'Cash'), ('x_is_expats', '!=', 'True'),
             ('contract_id.state', 'in', ('open', 'close'))])
        is_bank_transfer = self.env['hr.employee'].search(
            [('payment_method', '=', 'Bank Transfer'), ('x_is_expats', '!=', 'True'),
             ('contract_id.state', 'in', ('open', 'close'))])
        # if self.contract_id.state in ('open', 'close'):
        if self.x_payment_method == 'Cash':
            self.employee_ids = [(6, 0, is_cash.ids)]
            res['domain'] = {'employee_ids': [('payment_method', '=', 'Cash')]}
            return res
        elif self.x_payment_method == 'Bank Transfer':
            self.employee_ids = [(6, 0, is_bank_transfer.ids)]
            res['domain'] = {'employee_ids': [('payment_method', '=', 'Bank Transfer')]}
            return res

    def _get_available_contracts_domain(self):
        # return [('contract_ids.state', 'in', ('open', 'close')), ('company_id', '=', self.env.company.id)]
        print("fffff")

    def _get_employees(self):
        # YTI check dates too
        # return self.env['hr.employee'].search(self._get_available_contracts_domain())
        print("fff")
