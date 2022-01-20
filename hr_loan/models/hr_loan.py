# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import math
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import date
from datetime import timedelta
from datetime import datetime
from dateutil.relativedelta import relativedelta
import dateutil


class hr_loan(models.Model):
    _name = 'hr.loan'
    _description = 'Employees Loan'
    _inherit = 'mail.thread'

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, rec.name))
        return result

    name = fields.Char(string='Description', readonly=True, track_visibility='onchange',
                       states={'new': [('readonly', False)]}, required=True)
    reference = fields.Char(string='Reference', default='New', readonly=1)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True, track_visibility='onchange',
                                  states={'new': [('readonly', False)]}, required=True)
    payment_type = fields.Many2one('payment.type', string='Payment Type')
    pay_type = fields.Char(string='Payment Type', related='payment_type.name')
    date = fields.Date(string='Date', readonly=True, track_visibility='onchange', copy=False,
                       states={'new': [('readonly', False)]}, required=True, default=fields.Date.today())
    amount = fields.Monetary(string='Amount', digits=dp.get_precision('Payroll'), readonly=True,
                             track_visibility='onchange', copy=False, states={'new': [('readonly', False)]},
                             required=True)
    paid = fields.Monetary(string='Paid', digits=dp.get_precision('Payroll'), readonly=True,
                           compute="_compute_paid_and_due_amount",
                           copy=False)
    balance = fields.Monetary(string='Amount Due', digits=dp.get_precision('Payroll'), readonly=True,
                              compute="_compute_paid_and_due_amount",
                              copy=False)
    state = fields.Selection(
        [('new', 'New'), ('open', 'Running'), ('paid', 'Paid'), ('cancel', 'Cancelled'), ('suspended', 'Suspended')],
        string='State', default='new', readonly=True, track_visibility='onchange', copy=False)
    installment = fields.Monetary(string='Installment Amount', digits=dp.get_precision('Payroll'), readonly=True,
                                  track_visibility='onchange', copy=False, states={'new': [('readonly', False)]},
                                  required=True)
    move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)
    # zero_loan_lines_move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)
    memo_loan = fields.Char(string='Memo')
    journal_id = fields.Many2one('account.journal', 'Journal', readonly=True, required=True,
                                 track_visibility='onchange',
                                 states={'new': [('readonly', False)]},
                                 default=lambda self: self.env['account.journal'].search([('type', '=', 'general')],
                                                                                         limit=1))
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency")
    loan_ids = fields.One2many('hr.loan.lines', 'loan_id', 'Lines', readonly=True, copy=False,
                               track_visibility='onchange')
    payment_ids = fields.One2many('loan.payment.line', 'payment_line_id', readonly=True, copy=False,
                                  track_visibility='onchange')
    discounted_loan_line_ids = fields.One2many('discounted.loan.lines', 'discounted_line_id', readonly=True, copy=False,
                                               track_visibility='onchange')
    suspend_date = fields.Date(string='Suspend Date', track_visibility='onchange')
    suspend_reason = fields.Char(string='Suspend Reason', track_visibility='onchange')
    installment_start_date = fields.Date(string='Installment Start Date', track_visibility='onchange', required=True)
    installment_number = fields.Integer(string='Installment Number', track_visibility='onchange',
                                        compute='calculate_installment_number')
    actual_number = fields.Float(string='Actual Number', track_visibility='onchange',
                                 compute='calculate_installment_number_for_actual_number', digits=(14, 5))
    resume_date = fields.Date(string='Resume Date', default=fields.Date.today())
    x_pay = fields.Boolean(string='Pay')
    x_registration_number = fields.Char(string='Code ID', related='employee_id.registration_number')
    x_slips_count = fields.Integer(string='Slips', compute='get_slips_count')

    def get_slips_count(self):
        count = self.env['hr.payslip'].search_count(
            [('employee_id', '=', self.employee_id.id), ('input_line_ids.x_is_true', '=', True),
             ('state', '!=', 'cancel')])
        self.x_slips_count = count

    def action_view_loan_slips(self):
        return {
            'name': _('Slips'),
            'domain': [('employee_id', '=', self.employee_id.id), ('input_line_ids.x_is_true', '=', True),
                       ('state', '!=', 'cancel')],
            'res_model': 'hr.payslip',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def _compute_paid_and_due_amount(self):
        total_due = 0
        installment = self.payment_ids
        for line in self:
            line.paid = sum(installment.mapped('installment_amount')) - sum(installment.mapped('installment_unpaid'))
            total_due += line.amount - line.paid
            line.balance = total_due
            if line.balance == 0.0:
                line.state = 'paid'

    def calculate_installment_number(self):
        for line in self:
            if self.amount != 0 and self.installment != 0:
                x = line.amount / line.installment
                line.installment_number = math.ceil(x)
            else:
                raise UserError(_('You Have To Insert Amount And Installment Amount....!!!Try Again'))

    def calculate_installment_number_for_actual_number(self):
        for line in self:
            line.actual_number = line.amount / line.installment

    def action_draft(self):
        for rec in self:
            if rec.state == 'cancel':
                if rec.balance != 0:
                    rec.write({'state': 'open'})
                else:
                    rec.write({'state': 'new'})
            return True

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})
        return True

    def action_suspend(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.loan',
            'res_id': self.id,
            'views': [
                (self.env.ref('hr_loan.hr_loan_view_suspend_form').id, 'form'),
            ],
            'target': 'new',
        }

    def action_continue(self):
        for rec in self:
            rec.write({'state': 'open'})
        return True

    def action_resume(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.loan',
            'res_id': self.id,
            'views': [
                (self.env.ref('hr_loan.hr_loan_view_resume_form').id, 'form'),
            ],
            'target': 'new',
        }
        # for rec in self:
        #     rec.suspend_date = False
        #     rec.suspend_reason = False
        #     rec.write({'state': 'open'})
        # return True

    def action_save_resume(self):

        # resume_date = self.suspend_date + relativedelta(days=1)
        count = 0
        vals = {'suspend_date': False,
                'suspend_reason': False,
                'state': 'open',
                }
        x = self.env['loan.payment.line'].search([('payment_line_id', '=', self.id), ('state', '=', 'pending')],
                                                 order='installment_date asc')
        month = 0
        for line in x:
            line.installment_date = self.resume_date + relativedelta(months=month)
            month += 1
        self.write(vals)

    def check_loan_suspended(self):
        x = self.env['hr.loan'].search([('state', '=', 'suspended')])
        if x:
            for rec in x:
                if rec.suspend_date:
                    if rec.suspend_date <= fields.Date.today():
                        rec.write({'state': 'open'})

    def action_save_suspend(self):

        # resume_date = self.suspend_date + relativedelta(days=1)
        count = 0
        vals = {'suspend_date': self.suspend_date,
                'suspend_reason': self.suspend_reason,
                'state': 'suspended',
                }
        x = self.env['loan.payment.line'].search([('payment_line_id', '=', self.id), ('state', '=', 'pending')],
                                                 order='installment_date asc')
        month = 0
        for line in x:
            line.installment_date = self.suspend_date + relativedelta(months=month)
            month += 1
        self.write(vals)

    def action_confirm(self):
        for rec in self:
            x = 1
            if rec.amount % rec.installment == 0:
                x = 0
            for i in range(rec.installment_number):
                line = {
                    'installment_date': self.installment_start_date + relativedelta(months=i),
                    'installment_amount': self.installment,
                    'installment_unpaid': self.installment,
                    'payment_line_id': self.id,
                }
                self.env['loan.payment.line'].create(line)
            for record in self.payment_ids[len(self.payment_ids) - 1]:
                record.installment_amount = record.installment_amount * (
                        1 - (rec.installment_number - rec.actual_number))
                record.installment_unpaid = record.installment_unpaid * (
                        1 - (rec.installment_number - rec.actual_number))
        rec.write({'state': 'open'})
        self.create_journal_entry()
        return True

    # for i in range(rec.installment_number):
    #     print(rec.installment_number, 'rrrrrr')
    #     rec.payment_ids = [
    #         (0, 0, {'installment_date': rec.installment_start_date + dateutil.relativedelta(+i),
    #                 'installment_amount': rec.amount, 'state': rec.state})]
    # rec.payment_ids.append(
    #     (0, 0, {'installment_date': rec.installment_start_date + dateutil.relativedelta(+i),
    #             'installment_amount': rec.amount,
    #             'state': rec.state,
    #             }))
    def create_journal_entry(self):
        debit_vals = {
            'name': self.name,
            'debit': abs(self.amount),
            'credit': 0.0,
            'account_id': self.payment_type.x_account.id,
        }
        credit_vals = {
            'name': self.name,
            'debit': 0.0,
            'credit': abs(self.amount),
            'account_id': self.journal_id.default_credit_account_id.id,
        }
        vals = {
            'date': self.date,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'ref': self.name,
            'type': 'entry',
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
        }
        if self.x_pay:
            move = self.env['account.move'].create(vals)
            move.post()
            self.move_id = move

    def unlink(self):
        # if any(bool(rec.move_id) for rec in self):
        #     raise UserError(_("You can not delete a loan that is already running"))
        if self.paid > 0:
            raise UserError(_('It is not allowed to delete a loan that already confirmed.'))
        return super(hr_loan, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            payment = self.env['payment.type'].browse(vals.get('payment_type'))
            if payment and payment.x_sequence_id:
                vals['reference'] = payment.x_sequence_id.next_by_id() or _('New')
        result = super(hr_loan, self).create(vals)
        return result

    def action_register_payment_loan(self):
        context = dict(self._context or {})
        context.update(active_ids=self.ids, active_model='hr.loan', active_id=self.id, default_x_loan_id=self.id,
                       employee=self.employee_id.address_home_id.id, default_payment_type='inbound',
                       default_journal_id=9)
        # context = {'default_x_loan_id': self.id,}
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'view_id': self.env.ref('hr_loan.payment_loan_form').id,
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_zero_loan_lines(self):
        context = dict(self._context or {})
        context.update(active_ids=self.ids, active_model='hr.loan', active_id=self.id, default_x_loan_id=self.id,
                       employee=self.employee_id.address_home_id.id,
                       default_journal_id=self.payment_type.loan_exemption_account.id)
        # context = {'default_x_loan_id': self.id,}
        return {
            'name': _('Zero Loan Line'),
            'res_model': 'pay.loan.lines',
            'view_mode': 'form',
            'view_id': self.env.ref('hr_loan.pay_loan_lines_form').id,
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
