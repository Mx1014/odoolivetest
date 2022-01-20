# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import email_split, float_is_zero
from datetime import datetime


class HrSheetLine(models.Model):
    _name = 'hr.sheet.line'
    _description = 'Hr Expense Sheet Line'
    _rec_name = 'partner_id'

    name = fields.Char(string="Number")
    expense_sheet_id = fields.Many2one('hr.expense.sheet', string="Expense Sheet")
    state = fields.Selection([
        ('to_submit', 'To Submit'),
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('done', 'Paid'),
        ('post', 'Posted'),
        ('reconcile', 'Reconciled'),
        ('cancel', 'Refused')
    ], string='Report Status', index=True, readonly=True, tracking=True, copy=False, required=True,
        help='Expense Report State')
    parent_state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Status', required=True, readonly=True, copy=False, tracking=True)
    total_paid = fields.Monetary(string="Total Paid")
    total = fields.Monetary(string="Total")
    partner_id = fields.Many2one('res.partner', string="Partner")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    date = fields.Date(string="Date")


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    def _domain_get_field(self):
        return [('x_hr_expense_sheet', '=', False), ('credit', '!=', 0.0),
                ('account_id', '=', self.env['ir.default'].sudo().get('account.move.line', 'x_payroll_account'))]



    x_account_move_ids = fields.One2many('account.move', 'x_hr_expense_sheet', string="Expenses Bills", copy=False)
    x_payment_mode = fields.Selection([
        ("own_account", "Cash"),
        ("company_account", "Credit Card")
    ], string="Payment Methods", readonly=True)
    x_total_amount = fields.Monetary('Total Expenses', currency_field='currency_id', compute='_compute_amount_bill', store=True)
    x_total_journals = fields.Monetary('Total Journals', currency_field='currency_id',
                                       compute='_compute_amount_journal', store=True)
    x_payment_journal = fields.Many2one('account.journal', string="Payment Journal",
                                        domain=[('x_is_expense', '=', True)])
    x_expenses_totals = fields.Monetary('Total Payments', currency_field='currency_id',
                                        compute='_compute_amount_all')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('post', 'Posted'),
        ('done', 'Paid'),
        ('reconcile', 'Reconciled'),
        ('cancel', 'Refused')
    ], string='Status', index=True, readonly=True, tracking=True, copy=False, default='draft', required=True,
        help='Expense Report State')

    x_bank_statement_id = fields.Many2one('account.bank.statement', string="Cash Statement")
    x_statement_state = fields.Selection(related='x_bank_statement_id.state')
    x_statement_state_cu = fields.Boolean(compute="_get_state_reconcile")
    x_ownwer_journal = fields.Many2one('account.journal')
    x_payment_id = fields.Many2one('account.payment', copy=False)
    # total_amount = fields.Monetary('Total Amount', currency_field='currency_id', compute='_compute_amount_payment',
    #                                store=True)
    x_all_lines_reconciled = fields.Boolean(related="x_bank_statement_id.all_lines_reconciled")
    x_move_line_ids = fields.One2many('account.move.line', 'x_hr_expense_sheet', string="Journals", copy=False)
    # x_sheet_line = fields.One2many('hr.sheet.line', 'expense_sheet_id', string="Expense Lines",
    #                                compute="_get_combine_expenses", store=True)

    x_payment_paid_ids = fields.Many2many('account.payment', string="Payments", copy=False, compute="_compute_all_payment", store=True)

    @api.depends('x_move_line_ids', 'x_account_move_ids')
    @api.onchange('x_move_line_ids', 'x_account_move_ids')
    def _compute_all_payment(self):
        default = self.env['account.payment'].search([('x_move_line_ref', 'in', self.x_move_line_ids.ids)])
        default1 = self.env['account.payment'].search([('invoice_ids', 'in', self.x_account_move_ids.ids)])
        self.x_payment_paid_ids = [(6, 0, default.ids + default1.ids)]


    # @api.depends('x_move_line_ids', 'x_account_move_ids')
    # @api.onchange('x_move_line_ids', 'x_account_move_ids')
    # def _get_combine_expenses(self):
    #     move_ls = []
    #     self.x_sheet_line = [(2, c.id) for c in self.x_sheet_line]
    #     for move in self.mapped('x_account_move_ids'):
    #         move_ls.append((0, 0, {
    #             'name': move.name,
    #             'state': move.x_expense_state,
    #             'parent_state': move.state,
    #             'partner_id': move.partner_id.id,
    #             'date': move.invoice_date,
    #             'total': move.amount_total_signed,
    #             'total_paid': move.amount_total,
    #             'expense_sheet_id': self.id,
    #         }))
    #     for journal in self.mapped('x_move_line_ids'):
    #         move_ls.append((0, 0, {
    #             'name': journal.move_id.name,
    #             'state': journal.x_invs_expense_state,
    #             'parent_state': journal.parent_state,
    #             'partner_id': journal.partner_id.id,
    #             'date': journal.date,
    #             'total': journal.credit,
    #             'total_paid': journal.x_total_paid,
    #             'expense_sheet_id': self.id,
    #         }))
    #     self.x_sheet_line = move_ls

    # @api.onchange('x_sheet_line')
    # def lines_for_staff_journals(self):
    #     structs = []
    #     res = {}
    #     for struct in self.env['hr.payroll.structure'].search([('journal_id', '!=', False)]):
    #         if struct.journal_id.id not in structs:
    #             structs.append(struct.journal_id.id)
    #     res['domain'] = {'x_move_line_ids': [('journal_id', 'in', structs), ('move_id.state', '=', 'posted')]}

    @api.depends('x_account_move_ids.amount_total')
    def _compute_amount_bill(self):
        for sheet in self:
            sheet.x_total_amount = sum(sheet.x_account_move_ids.mapped('amount_total'))

    @api.depends('x_move_line_ids.credit')
    def _compute_amount_journal(self):
        for sheet in self:
            sheet.x_total_journals = sum(sheet.x_move_line_ids.mapped('credit'))

    #@api.depends('x_payment_paid_ids.amount')
    def _compute_amount_all(self):
        for sheet in self:
            sheet.x_expenses_totals = sum(sheet.x_payment_paid_ids.mapped('amount'))

    def action_sheet_move_create(self):
        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids') \
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(
                    r.currency_id or self.env.company.currency_id).rounding))
        res = expense_line_ids.action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        # self.write({'state': 'done'})
        self.activity_update()

        return res

    @api.depends('x_all_lines_reconciled', 'x_statement_state')
    def _get_state_reconcile(self):
        if not self.x_all_lines_reconciled and self.state == 'reconcile':
            self.x_statement_state_cu = True
            self.write({'state': 'reconcile'})
        elif self.x_all_lines_reconciled and self.state == 'reconcile' and self.x_statement_state == 'open':
            self.x_statement_state_cu = True
            self.write({'state': 'reconcile'})
        else:
            self.x_statement_state_cu = False

    def unlink(self):
        for expense in self:
            if expense.state not in ['draft', 'cancel']:
                raise UserError(_('You cannot delete the expense Report.'))
        super(HrExpenseSheet, self).unlink()

    def validate(self):
        self.x_bank_statement_id.check_confirm_bank()
        self.write({'state': 'reconcile'})

    def post_register_payment(self):
        self.ensure_one()
        return {
            'name': _('Register Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'views': [
                (self.env.ref('account.view_account_payment_form').id, 'form'),
            ],
            'context': {
                'default_payment_date': self.create_date,
                'default_journal_id': self.x_payment_journal.id,
                'default_amount': self.x_total_journals + self.x_total_amount,
                'default_communication': self.name,
                'default_payment_type': 'transfer',
                # 'default_payment_method_id': payment_methods and payment_methods[0].id or False,
                'default_partner_type': 'supplier',
                # 'partner_id': '',
            },
            'target': 'new',
        }

    def view_payment_send(self):
        self.ensure_one()
        return {
            'name': _('Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'views': [
                (self.env.ref('account.view_account_payment_form').id, 'form'),
            ],
            'res_id': self.x_payment_id.id,
        }

    def view_journal_statement(self):
        self.ensure_one()
        return {
            'name': _('Statement'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.bank.statement',
            'views': [
                (self.env.ref('account.view_bank_statement_form').id, 'form'),
            ],
            'res_id': self.x_bank_statement_id.id,
        }

    def reconcile(self):
        self.ensure_one()
        bank_stmt_lines = self.x_bank_statement_id.mapped('line_ids')
        return {
            'type': 'ir.actions.client',
            'tag': 'bank_statement_reconciliation_view',
            'context': {'statement_line_ids': bank_stmt_lines.ids,
                        'company_ids': self.x_bank_statement_id.mapped('company_id').ids},
        }

    def expense_register_payment(self):
        payment_methods = self.x_payment_journal.outbound_payment_method_ids
        statement_line_vals = []
        vals = {
            'payment_date': self.create_date,
            'journal_id': self.env['ir.default'].sudo().get('account.user.statement', 'x_voucher_journal'),
            'destination_journal_id': self.x_payment_journal.id,
            'amount': self.x_total_journals + self.x_total_amount,
            'communication': self.name,
            'payment_type': 'transfer',
            'payment_method_id': payment_methods and payment_methods[0].id or False,
            'partner_type': 'supplier',
            'x_expense_sheet_id': self.id,
        }
        payment = self.env['account.payment'].create([vals])
        self.x_payment_id = payment.id
        #self.state = 'done'
        # payment.post()
        if payment:
            # val = {
            #     # 'name': '%s/%s' %(self.name, user_statement.name),
            #     'name': self.name,
            #     'journal_type': self.x_payment_journal.type,
            #     'journal_id': self.x_payment_journal.id,
            #     'date': fields.Date.today(),
            #     # 'statement_for_pabs': True,
            #     'balance_start': 0.0,
            # }
            # self.x_bank_statement_id = self.env['account.bank.statement'].create(val)
            if self.x_bank_statement_id:
                #voucher = self.env['account.journal'].search([('id', '=', self.env['ir.default'].sudo().get('account.user.statement', 'x_voucher_journal'))])
                # vals = {
                #     'name': 'Total Payments',
                #     'statement_id': self.x_bank_statement_id.id,
                #     'journal_id': voucher.id,
                #     'date': payment.payment_date,
                #     'amount': -payment.amount,
                #     #'partner_id': payment.partner_id.id,
                #     # 'note': '',
                #     # 'transaction_type': '',
                #     'ref': payment.name,
                #     # 'user_id': self.env.user.id,
                # }
                # statement_line_vals.append((0, 0, vals))
                vals1 = {
                    'name': 'Total Reimbursements',
                    'statement_id': self.x_bank_statement_id.id,
                    'journal_id': self.x_payment_journal.id,
                    'date': payment.payment_date,
                    'amount': payment.amount,
                    #'partner_id': payment.partner_id.id,
                    # 'note': '',
                    # 'transaction_type': '',
                    'ref': payment.name,
                    # 'user_id': self.env.user.id,
                }
                statement_line_vals.append((0, 0, vals1))
                self.x_bank_statement_id.write({'line_ids': statement_line_vals})
            else:
                raise UserError(_('Please Select Payment Journal'))
                #self.x_expense_sheet_id.x_bank_statement_id = self.x_bank_statement_id.id


    @api.onchange('x_payment_paid_ids')
    def names_get(self):
        date = []
        for payment in self.x_payment_paid_ids:
            date.append(payment.payment_date)
        if date != []:
           self.name = 'Expenses Report - From %s To %s' % (datetime.strftime(min(date), '%d/%m'), datetime.strftime(max(date), '%d/%m'))

# def approve_expense_sheets(self):
#     res = super(HrExpenseSheet, self).approve_expense_sheets()
#     print(res)
#     if not self.x_move_line_ids:
#         self.state = 'done'
#     return res


# payment_mode = fields.Selection(related='expense_line_ids.payment_mode', default='own_account', readonly=True,
#                                 string="Payment Type")
#
# x_payment_ids = fields.Many2many('account.payment', string="Payment Report")
# x_bank_statement_id = fields.Many2one('account.bank.statement', string="Statement")
# x_statement_state = fields.Selection(related='x_bank_statement_id.state')
# x_statement_state_cu = fields.Boolean(compute="get_state_reconcile")
# x_ownwer_journal = fields.Many2one('account.journal')
#
# state = fields.Selection([
#     ('draft', 'Draft'),
#     ('submit', 'Submitted'),
#     ('approve', 'Approved'),
#     ('done', 'Paid'),
#     ('post', 'Posted'),
#     ('reconcile', 'Reconciled'),
#     ('cancel', 'Refused')
# ], string='Status', index=True, readonly=True, tracking=True, copy=False, default='draft', required=True,
#     help='Expense Report State')
#
# @api.depends('x_statement_state')
# def get_state_reconcile(self):
#     print('test')
#     if self.x_statement_state == 'confirm':
#        self.x_statement_state_cu = True
#        self.write({'state': 'reconcile'})
#     else:
#         self.x_statement_state_cu = False
#
#
#
# @api.model
# def _default_journal_id(self):
#     default_company_id = self.default_get(['company_id'])['company_id']
#     default_employee_id = self.default_get(['employee_id'])['employee_id']
#     employee = self.env['hr.employee'].search([('id', '=', default_employee_id)])
#     journal = self.env['account.journal'].search(
#         [('type', '=', 'cash'), ('id', '=', employee.x_cash_account.id), ('company_id', '=', default_company_id)], limit=1)
#     return journal.id
#
# @api.onchange('journal_id')
# def get_journal_id_domain(self):
#     res = {}
#     res['domain'] = {'journal_id': [('id', '=', self.employee_id.x_cash_account.id)]}
#     return res
#
# @api.model
# def _default_bank_journal_id(self):
#     default_company_id = self.default_get(['company_id'])['company_id']
#     default_employee_id = self.default_get(['employee_id'])['employee_id']
#     employee = self.env['hr.employee'].search([('id', '=', default_employee_id)])
#     return self.env['account.journal'].search(
#         [('type', 'in', ['cash', 'bank']), ('id', '=', employee.x_bank_account.id), ('company_id', '=', default_company_id)], limit=1)
#
# @api.onchange('bank_journal_id')
# def get_bank_journal_id_domain(self):
#     res = {}
#     res['domain'] = {'bank_journal_id': [('id', '=', self.employee_id.x_bank_account.id)]}
#     return res
#
#
# journal_id = fields.Many2one('account.journal', string='Cash Journal',
#                              states={'done': [('readonly', True)], 'post': [('readonly', True)]},
#                              check_company=True,
#                              domain="[('type', '=', 'cash'), ('company_id', '=', company_id)]",
#                              default=_default_journal_id, help="The journal used when the expense is done.")
#
# bank_journal_id = fields.Many2one('account.journal', string='Bank Journal',
#                                   states={'done': [('readonly', True)], 'post': [('readonly', True)]},
#                                   check_company=True,
#                                   domain="[('type', 'in', ['cash', 'bank']), ('company_id', '=', company_id)]",
#                                   default=_default_bank_journal_id,
#                                   help="The payment method used when the expense is paid by the company.")

# @api.constrains('expense_line_ids')
# def _check_payment_mode(self):
#     for sheet in self:
#         expense_lines = sheet.mapped('expense_line_ids')
#         if expense_lines and any(
#                 expense.payment_mode != expense_lines[0].payment_mode for expense in expense_lines):
#             raise ValidationError(_("Expenses must be paid by the same type (Cash or Credit Card)."))
#

# def action_sheet_move_create(self):
#     if any(not sheet.journal_id for sheet in self):
#         raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))
#
#     expense_line_ids = self.mapped('expense_line_ids')\
#         .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.company.currency_id).rounding))
#     res = expense_line_ids.action_move_create()
#
#     if not self.accounting_date:
#         self.accounting_date = self.account_move_id.date
#
#
#     self.write({'state': 'post'})
#     self.activity_update()
#
#     return res

# def action_sheet_move_create(self):
#     res = super(HrExpenseSheet, self).action_sheet_move_create()
#     expense_line_ids = self.mapped('expense_line_ids') \
#         .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(
#                 r.currency_id or self.env.company.currency_id).rounding))

# if self.payment_mode == 'own_account' and expense_line_ids:
#     self.write({'state': 'done'})
#
# if any(expense.state == 'draft' for expense in self.mapped('x_payment_ids')):
#     raise UserError(_("You cannot post a report with a draft payment!"))
#
# for payment in self.mapped('x_payment_ids'):
#     statement_line_vals = []
#     statement_id = False
#     if not self.env['account.bank.statement'].search(
#             [('date', '=', fields.Date.today()), ('journal_id', '=', payment.journal_id.id)]):
#         val = {
#             # 'name': '%s/%s' %(self.name, user_statement.name),
#             'name': '%s/%s' % ( payment.journal_id.name, str(fields.Date.today())),
#             'journal_type': 'bank',
#             'journal_id':  payment.journal_id.id,
#             'date': fields.Date.today(),
#             #'statement_for_pabs': True,
#             'balance_start': 0.0,
#         }
#         statement_id = self.env['account.bank.statement'].create(val)
#     else:
#         statement_id = self.env['account.bank.statement'].search(
#             [('date', '=', fields.Date.today()), ('journal_id', '=', payment.journal_id.id),
#              ('state', '=', 'open')], limit=1, order="id desc")
#
#
#     if statement_id:
#         vals = {
#             'name': payment.journal_id.name,
#             'statement_id': statement_id.id,
#             'journal_id': payment.journal_id.id,
#             'date': payment.payment_date,
#             'amount': -payment.amount,
#             # 'note': '',
#             # 'transaction_type': '',
#             'ref': payment.name,
#             'user_id': self.env.user.id,
#         }
#         statement_line_vals.append((0, 0, vals))
#         statement_id.write({'line_ids': statement_line_vals})
#         self.x_bank_statement_id = statement_id.id

# return res

# def post_register_payment(self):
#     self.ensure_one()
#     amount = sum(self.x_payment_ids.mapped('amount'))
#     if any(expense.state == 'draft' for expense in self.mapped('x_payment_ids')):
#         raise UserError(_("You cannot post a report with a draft payment!"))
#     return {
#         'name': _('Register Payment'),
#         'type': 'ir.actions.act_window',
#         'res_model': 'account.payment',
#         'views': [
#             (self.env.ref('account.view_account_payment_form').id, 'form'),
#         ],
#         'context': {
#             'default_payment_type': 'transfer',
#             'default_x_is_expense': True,
#             'default_destination_journal_id': self.env['ir.default'].sudo().get('hr.expense.sheet', 'x_ownwer_journal'), #self.x_payment_ids.mapped('journal_id')[0].id or False,
#             'default_x_total_expense': sum(self.x_payment_ids.mapped('amount')),
#             'default_x_expense_sheet_id': self.id,
#             'default_communication': self.name,
#             'default_amount': amount,
#         },
#         'target': 'new',
#     }


# def reconcile(self):
#     return {
#         'name': _('Statement'),
#         'res_model': 'account.bank.statement',
#         'res_id': self.x_bank_statement_id.id,
#         'views': [
#             (self.env.ref('account.view_bank_statement_form').id, 'form'),
#         ],
#         'type': 'ir.actions.act_window',
#         'target': 'new',
#     }
# for line in self.mapped('payment_ids'):
#     vals = {
#         'payment_date': line.payment_date,
#         'journal_id': self.journal_id.id,
#         'amount': line.amount,
#         'communication': self.name,
#         'payment_type': 'transfer',
#         'destination_journal_id': self.x_deposit_to.id,
#         'payment_method_id': self.payment_method_id.id,
#         'x_batch_payment_id': self.id,
#         'cheque_number': line.cheque_number,
#         'cheque_date': line.cheque_date,
#         'account_number': line.account_number,
#         'bank_id': line.bank_id.id
#     }
#     id = self.env['account.payment'].create([vals])
#     id.post()
