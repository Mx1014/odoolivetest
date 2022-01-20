# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import email_split, float_is_zero
from datetime import datetime
from odoo.addons.account.models.account_payment import MAP_INVOICE_TYPE_PARTNER_TYPE
from odoo.addons.web.controllers.main import Binary
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception, Response
import base64
import json
import unicodedata
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_is_expense = fields.Boolean(string="Expense Bill", store=True)
    x_payment_mode = fields.Selection([
        ("own_account", "Cash"),
        ("company_account", "Credit Card")
    ], string="Payment Methods")
    x_customer_id = fields.Many2one('res.partner', string="Customer")
    x_expense_state = fields.Selection([
        ('to_submit', 'To Submit'),
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('done', 'Paid'),
        ('post', 'Posted'),
        ('reconcile', 'Reconciled'),
        ('cancel', 'Refused')
    ], string="Report Status", compute="depends_expense_state")

    x_invs_expense_state = fields.Selection([
        ('to_submit', 'To Submit'),
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('done', 'Paid'),
        ('post', 'Posted'),
        ('reconcile', 'Reconciled'),
        ('cancel', 'Refused')
    ], string="Invs Report State", store=True)

    x_payment_journal = fields.Many2one('account.journal', string="Payment Journal")
    x_purchase_journal = fields.Many2one('account.journal', string="Purchase Journal")
    x_hr_expense_sheet = fields.Many2one('hr.expense.sheet', string="Expense Sheet", copy=False)
    x_payment_expenses_id = fields.Many2one('account.payment', string="Expenses Payment Ref", copy=False)

    @api.model
    def default_get(self, default_fields):
        res = super(AccountMove, self).default_get(default_fields)
        if self.x_is_expense and self.state == 'draft':
            self.journal_id = self.env['ir.default'].sudo().get('account.move', 'x_purchase_journal')
        return res

    def depends_expense_state(self):
        for payment in self:
            report = payment.env['hr.expense.sheet'].search([('x_account_move_ids', 'in', payment.id)])
            if report:
                payment.x_expense_state = report.state
                payment.x_invs_expense_state = report.state
            else:
                payment.x_expense_state = 'to_submit'
                payment.x_invs_expense_state = 'to_submit'

    def action_submit_expenses(self):
        todo = self.filtered(lambda x: x.type == 'in_invoice')
        date = []
        if self.env['hr.expense.sheet'].search([('x_account_move_ids', 'in', todo.ids)]):
            print(todo.ids)
            print(self.env['hr.expense.sheet'].search([('x_account_move_ids', 'in', todo.ids)]))
            raise UserError(_("You cannot report twice the same expense bill!"))

        if any(expense.state == 'draft' for expense in todo):
            raise UserError(_("Please report paid expenses bills only!"))

        if len(set(todo.x_payment_journal.mapped('name'))) != 1:
            raise UserError(_("Please report expenses bills which have same payment journal!"))
        for pay in todo:
            date.append(pay.invoice_date)

        return {
            'name': _('New Expense Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'context': {
                'default_x_account_move_ids': todo.ids,
                'default_company_id': self.company_id.id,
                'default_employee_id': self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]).id,
                'default_name': 'Expenses Report - From %s To %s' % (
                datetime.strftime(min(date), '%d/%m'), datetime.strftime(max(date), '%d/%m')),
                'default_x_payment_journal': todo[0].x_payment_journal.id,
                # 'default_name': 'Reimbursements - From %s To %s' % (datetime.strftime(min(date), '%m/%d'), datetime.strftime(max(date), '%m/%d')),
            }
        }

    def post_expenses(self):
        self.action_post()
        self.register_expense_payment()

    def register_expense_payment(self):
        self.ensure_one()
        payment_methods = self.x_payment_journal.outbound_payment_method_ids
        values = {
            'journal_id': self.x_payment_journal.id,
            'payment_method_id': payment_methods and payment_methods[0].id or False,
            'payment_date': self.invoice_date,
            'communication': self.name,
            'invoice_ids': [(4, self.id)],
            'payment_type': 'outbound',
            'amount': abs(self.amount_total),
            'currency_id': self.currency_id.id,
            'partner_id': self.commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[self.type],
            'partner_bank_account_id': self.invoice_partner_bank_id.id,

        }

        if not self.x_payment_expenses_id:
            payments = self.env['account.payment'].create([values])
            self.x_payment_expenses_id = payments.id
            payments.post()
        else:
            self.x_payment_expenses_id.action_draft()
            self.x_payment_expenses_id.update(values)
            self.x_payment_expenses_id.post()


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    x_is_expense = fields.Boolean(string="Expense Journal", store=True, default=False)
    x_employee_id = fields.Many2many('res.users', string="Employee", relation='employee_users')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_paid = fields.Boolean(string="Paid", default=False, copy=False)
    x_total_paid = fields.Monetary(string="Total Paid")
    x_expense_state = fields.Selection([
        ('to_submit', 'To Submit'),
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('done', 'Paid'),
        ('post', 'Posted'),
        ('reconcile', 'Reconciled'),
        ('cancel', 'Refused')
    ], string="Report Status", compute="depends_expense_states")

    x_invs_expense_state = fields.Selection([
        ('to_submit', 'To Submit'),
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('done', 'Paid'),
        ('post', 'Posted'),
        ('reconcile', 'Reconciled'),
        ('cancel', 'Refused')
    ], string="Invs Report State", store=True)
    x_hr_expense_sheet = fields.Many2one('hr.expense.sheet', string="Expense Sheet", copy=False)
    x_payroll_account = fields.Many2one('account.account', string="Payroll Payable Account",
                                        domain=[('user_type_id.type', '=', 'payable')])

    def depends_expense_states(self):
        for payment in self:
            report = payment.env['hr.expense.sheet'].search([('x_move_line_ids', 'in', payment.id)])
            if report:
                payment.x_expense_state = report.state
                payment.x_invs_expense_state = report.state
            else:
                payment.x_expense_state = 'to_submit'
                payment.x_invs_expense_state = 'to_submit'

    def register_journal_payment(self):
        self.ensure_one()
        payment_methods = self.x_hr_expense_sheet.x_payment_journal.outbound_payment_method_ids
        values = {
            'journal_id': self.x_hr_expense_sheet.x_payment_journal.id,
            'payment_method_id': payment_methods and payment_methods[0].id or False,
            'payment_date': self.date,
            'communication': self.move_id.name,
            'payment_type': 'outbound',
            'amount': abs(self.credit),
            'partner_id': self.partner_id.id,
            'partner_type': 'supplier',
            'x_move_line_ref': self.id
            # 'partner_bank_account_id': self.invoice_partner_bank_id.id,

        }
        payments = self.env['account.payment'].create([values])
        # payments.post()
        if payments:
            self.x_paid = True
            self.x_total_paid = abs(self.credit)
            self.x_hr_expense_sheet._compute_all_payment()
            return self.view_registered_payment(payments.id)

    def view_registered_payment(self, id):
        self.ensure_one()
        return {
            'name': _('Register Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'views': [
                (self.env.ref('account.view_account_payment_form').id, 'form'),
            ],
            'res_id': id,
        }


class AccountAccount(models.Model):
    _inherit = 'account.account'

    x_paying_expense = fields.Boolean(string='Allow in Expenses', default=False, store=True)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    x_move_line_ref = fields.Many2one('account.move.line', string="Move Line Ref")
    x_expense_sheet_id = fields.Many2one('hr.expense.sheet', string="Expenses Sheet")

    # def post(self):
    #     res = super(AccountPayment, self).post()
    #     sheet = self.x_expense_sheet_id
    #     if sheet:
    #         sheet.state = 'done'
    #     return res
    #
    # def action_draft(self):
    #     res = super(AccountPayment, self).action_draft()
    #     sheet = self.x_expense_sheet_id
    #     if sheet:
    #         sheet.state = 'approve'
    #     return res

class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    x_is_expense = fields.Boolean(string="Expense Statement", store=True)


    def action_view_bank_statement(self):
        #self.ensure_one()
        #line = self.env['purchase.order.line'].search([('order_id', '=', self.id)]).x_task_id.ids
        journal = self.env['account.journal'].search([('x_employee_id', '=', self.env.user.id)], limit=1)
        return {
            'name': _('Account Bank Statement'),
            'res_model': 'account.bank.statement',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_bank_statement_tree').id, 'tree'),
                (self.env.ref('account.view_bank_statement_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('x_is_expense', '=', True), ('journal_id', '=', journal.id)],
            'context': {'default_x_is_expense': True, 'default_journal_id': journal.id}
        }

class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    x_upload_file = fields.Binary(string="Upload PDF")
    x_expense_bill_id = fields.Many2one('account.move', string="Expense Bills")


    def upload_document(self,):
        if not self.x_expense_bill_id:
            if self.x_upload_file == 0:
                raise UserError(_('Please upload an Attachement'))
            Model = self.env['ir.attachment']
            bill = self.env['account.move'].create({
                 'x_is_expense': True,
                 'type': 'in_invoice',
                 'partner_id': self.partner_id,
            })

            self.x_expense_bill_id = bill.id

            attachment = Model.create({
                'name': 'attachment',
                'datas':  self.x_upload_file,
                'res_model': 'account.move',
                'res_id': int(bill.id)
            })
            attachment._post_add_create()

