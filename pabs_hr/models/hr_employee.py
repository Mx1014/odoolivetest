from odoo import models, fields, api, _
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo.osv import expression


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'
    _order = 'id DESC'
    date_of_join = fields.Date(string='Date Of Join')
    payment_method = fields.Selection([
        ('Cash', 'Cash'),
        ('Bank Transfer', 'Bank Transfer')],
        string='Payment Method')
    license_availability = fields.Selection([
        ('Yes', 'Yes'),
        ('No', 'NO')],
        string='License Availability')
    employee_status = fields.Selection([
        ('Temporary', 'Temporary'),
        ('Permanent', 'Permanent'),
        ('Part Time', 'Part Time'),
        ('Full Time', 'Full Time')],
        string='Employee Status')
    address_home_id = fields.Many2one(
        'res.partner', 'Address',
        help='Enter here the private address of the employee, not the one linked to your company.',
        groups="hr.group_hr_user", tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    reference_by = fields.Many2one('res.partner', string='Reference By')
    first_reference_details = fields.Boolean(string='First Reference')
    second_reference_details = fields.Boolean(string='Second Reference')
    third_reference_details = fields.Boolean(string='Third Reference')
    age = fields.Char(string='Age')
    x_country_address = fields.Char(string='Country Address')
    religion = fields.Char(string='Religion')
    first_relation = fields.Char(string='Relation', track_visibility='onchange')
    second_relation = fields.Char(string='Relation', track_visibility='onchange')
    third_relation = fields.Char(string='Relation', track_visibility='onchange')
    first_name = fields.Char(string='First Name', track_visibility='onchange')
    second_name = fields.Char(string='Second Name', track_visibility='onchange')
    third_name = fields.Char(string='Third Name', track_visibility='onchange')
    first_phone = fields.Char(string='First Phone', track_visibility='onchange')
    second_phone = fields.Char(string='Second Phone', track_visibility='onchange')
    third_phone = fields.Char(string='Third Phone', track_visibility='onchange')
    x_iban = fields.Char(string='IBAN', related='bank_account_id.x_iban')
    mobile = fields.Char(string='mobile', related='address_home_id.mobile')
    identification_expiration = fields.Date(string='Identification Expiration')
    passport_expiration = fields.Date(string='Passport  Expiration', track_visibility='onchange')
    passport_issue_date = fields.Date(string='Passport  Issue Date', track_visibility='onchange')
    passport_issue_place = fields.Many2one('res.country', string='Passport  Issue Place', track_visibility='onchange')
    job_id = fields.Many2one('hr.job', string='Job Position', track_visibility='onchange')
    license_number = fields.Char(string='License No')
    license_expiration = fields.Date(string='License  Expiration')
    short_name = fields.Char(string='Short Name', size=25)
    cr_no = fields.Char(string='CR', track_visibility='onchange')
    x_cpr = fields.Binary(string='C.P.R')
    x_passport = fields.Binary(string='Passport', track_visibility='onchange')
    x_bank_account_iban = fields.Binary(string='Bank Account And IBAN')
    x_experience_certificate = fields.Binary(string='Experience Certificate')
    x_education_certificate = fields.Binary(string='Education Certificate')
    x_address_proof = fields.Binary(string='Address Proof')
    x_photographs = fields.Binary(string='Photographs')
    x_medical_checkup = fields.Binary(string='Medical Checkup')
    x_good_conduct_certificate = fields.Binary(string='Good Conduct Certificate')
    registration_number = fields.Char('Registration Number of the Employee', groups="", copy=False)
    x_is_expats = fields.Boolean(string="Expats")
    registration_number = fields.Char('Code ID', groups="hr.group_hr_user", copy=False, default=lambda self: _('New'),
                                      readonly=True)
    visa_issue_date = fields.Date(string='Visa Issue Date', track_visibility='onchange')
    # validation_type = fields.Selection([
    #     ('both', 'Team Leader and Time Off Officer')], default='both', string='Validation')
    responsible_id = fields.Many2one('res.users', 'Responsible',
                                     domain=lambda self: [
                                         ('groups_id', 'in', self.env.ref('hr_holidays.group_hr_holidays_user').id)])
    private_email = fields.Char(related='address_home_id.email', string="Private Email", groups="hr.group_hr_user",
                                track_visibility='onchange')
    mobile_phone = fields.Char(track_visibility='onchange')
    work_phone = fields.Char(track_visibility='onchange')
    x_duration_of_work = fields.Char(track_visibility='onchange')
    parent_id = fields.Many2one('hr.employee', track_visibility='onchange')
    loan_availability = fields.Selection([
        ('Yes', 'Yes'),
        ('No', 'NO')],
        string='Loan Availability')
    x_annual_leave = fields.Float(string='Annual', compute='annual_leaves')
    x_full_paid = fields.Float(string='Full Paid', compute='full_paid_sick')
    x_half_paid = fields.Float(string='Half Paid', compute='half_paid_sick')
    x_unpaid_sick = fields.Float(string='Unpaid ', compute='unpaid_sick')
    x_last_annual_leave = fields.Date(string='Last Annual Leave Date ', compute='last_annual_leave')
    x_last_annual_leave_return = fields.Date(string='Last Annual Leave Return Date ',
                                             compute='last_annual_leave')

    def action_allocate_leave(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.leave.allocation',
            # 'res_id': self.id,
            'context': {'default_holiday_type': 'employee', 'default_employee_id': self.id},
            'views': [
                (self.env.ref('hr_holidays.hr_leave_allocation_view_form_manager').id, 'form'),
            ],
            'target': 'new',
        }

    def action_suspend(self):
        self.x_is_expats = True

    def action_resume(self):
        self.x_is_expats = False

    def total_duration_of_work(self):
        for rec in self:
            work = self.env['hr.work.entry'].search([
                ('employee_id.name', '=', rec.name), ('state', '=', 'validated'),
                ('work_entry_type_id.name', '=', 'Attendance')])
            rec.x_duration_of_work = sum(work.mapped('duration'))

    def annual_leaves(self):
        for employee in self:
            annual_leave = self.env['hr.leave.report'].search([
                ('employee_id.name', '=', employee.name),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('holiday_status_id.x_leave_types', '=', 'Annual Leave')
            ])
            employee.x_annual_leave = sum(annual_leave.mapped('number_of_days'))

    def last_annual_leave(self):
        for employee in self:
            annual_leave = self.env['hr.leave.report'].search([
                ('employee_id.name', '=', employee.name),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('holiday_status_id.x_leave_types', '=', 'Annual Leave')
            ], order='id desc', limit=1)
            employee.x_last_annual_leave = annual_leave.date_from
            employee.x_last_annual_leave_return = annual_leave.date_to

    def full_paid_sick(self):
        for employee in self:
            annual_leave = self.env['hr.leave.report'].search([
                ('employee_id.name', '=', employee.name),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('holiday_status_id.code', '=', 'FSL')
            ])
            employee.x_full_paid = sum(annual_leave.mapped('number_of_days'))

    def half_paid_sick(self):
        for employee in self:
            annual_leave = self.env['hr.leave.report'].search([
                ('employee_id.name', '=', employee.name),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('holiday_status_id.code', '=', 'HSL')
            ])
            employee.x_half_paid = sum(annual_leave.mapped('number_of_days'))

    def unpaid_sick(self):
        for employee in self:
            unoaid_leave = self.env['hr.leave.report'].search([
                ('employee_id.name', '=', employee.name),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('holiday_status_id.code', '=', 'USL')
            ])
            employee.x_unpaid_sick = sum(unoaid_leave.mapped('number_of_days'))

    # self.env['res.company'].create({'name': 'Opoo'})
    @api.model
    def create(self, vals):
        if vals.get('registration_number', _('New')) == _('New'):
            vals['registration_number'] = self.env['ir.sequence'].next_by_code('employee.code') or _('New')
        result = super(HrEmployeeInherit, self).create(vals)
        return result

    def action_upload_cpr(self):
        self.ensure_one()
        x = self.name + ' ' + str(self.id) + ' cpr'
        return {
            'name': _('Uplaod'),
            'view_mode': 'form',
            'views': [(self.env.ref('pabs_hr.view_attachment_form_pabs_hr').id, 'form')],
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
                'default_name': x
            }
        }

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []

        if name:
            if self.check_access_rights('read', raise_exception=False):
                domain = ['|', ('name', operator, name), ('registration_number', operator, name)]
            else:
                domain = [('name', operator, name)]

        emp_id = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(emp_id).name_get()

    # def name_get(self):
    #     result = []
    #     for rec in self:
    #         if rec.registration_number:
    #             result.append((rec.id, str(rec.registration_number) + ' ' + ' ' + rec.name))
    #         else:
    #             result.append((rec.id, rec.name))
    #     return result

    # def action_unlink_attachment(self):
    #     self.emp_cpr = None
    #
    # def test(self, val):
    #     y = self.env['documents.document'].search([('attachment_id', '=', val)])
    #     self.emp_cpr = y

    # def _compute_emp_docs(self):
    #     x = self.env['ir.attachment'].search([('res_model', '=', self._name), ('res_id', '=', self.id)])
    #     self.emp_docs = x

    # emp_docs = fields.Many2many('ir.attachment', string='emp', compute=_compute_emp_docs)
    # emp_cpr = fields.Many2one('documents.document', string='C.P.R')


class BankAccount(models.Model):
    _inherit = 'res.partner.bank'
    x_iban = fields.Char(string='IBAN', track_visibility='onchange')

