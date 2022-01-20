# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import email_split, float_is_zero

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    payment_mode = fields.Selection([
        ("own_account", "Cash"),
        ("company_account", "Credit Card")
    ], default='own_account', states={'done': [('readonly', True)], 'approved': [('readonly', True)], 'reported': [('readonly', True)]}, string="Payment Type")
    x_partner_id = fields.Many2one('res.partner', string="Partner")
    #x_invoice_line = fields.One2many('account.move.line', 'x_expense_id', string="Expense Line")
    x_expense_line = fields.One2many('hr.expense.line', 'expense_id', string="Expense Line")
    total_amount = fields.Monetary("Total", compute='_compute_amount_sum', store=True, currency_field='currency_id')
    unit_amount = fields.Float("Unit Price", readonly=True, required=False, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, digits='Product Price')
    untaxed_amount = fields.Float("Subtotal", store=True, compute='_compute_amount_sum', digits='Account')


    def _get_account_move_line_values(self):
        res = super(HrExpense, self)._get_account_move_line_values()
        i = 0
        id = 0
        for expense in res:
            for line in range(len(res[expense])):
               res[expense][line]['partner_id'] = self.sheet_id.mapped('expense_line_ids')[i].x_partner_id.id
               if 'tax_repartition_line_id' not in res[expense][line]:
                   res[expense][line]['name'] = self.sheet_id.mapped('expense_line_ids')[i].x_partner_id.name
            i = i + 1
        #     if id == 0:
        #        id = expense
        #
        # debit = 0
        # credit = 0
        # #print(res)
        # #res_cash = {id: res[id]}
        # #res = res_cash
        # for test in res:
        #         for dict in res[test]:
        #             # temp = dict
        #             if dict['debit'] != 0:
        #                 debit += dict['debit']
        #             if dict['credit'] != 0:
        #                 credit += dict['credit']
        # for test in res:
        #         for dict in res[test]:
        #             if dict['debit'] != 0:
        #                 dict['debit'] = debit
        #             if dict['credit'] != 0:
        #                 dict['credit'] = credit
        # res[id] = []
        # print(res)
        return res

    # def _get_expense_account_destination(self):
    #     res = super(HrExpense, self)._get_expense_account_destination()
    #     self.ensure_one()
    #     account_dest = self.env['account.account']
    #     if self.payment_mode == 'own_account':
    #         # if not self.employee_id.address_home_id:
    #         #     raise UserError(_("No Home Address found for the employee %s, please configure one.") % (self.employee_id.name))
    #         # partner = self.employee_id.address_home_id.with_context(force_company=self.company_id.id)
    #         account_dest = self.sheet_id.journal_id.default_credit_account_id.id
    #         res = account_dest
    #     return res

    def _get_expense_account_destination(self):
        self.ensure_one()
        account_dest = self.env['account.account']
        if self.payment_mode == 'company_account':
            if not self.sheet_id.bank_journal_id.default_credit_account_id:
                raise UserError(_("No credit account found for the %s journal, please configure one.") % (
                    self.sheet_id.bank_journal_id.name))
            account_dest = self.sheet_id.bank_journal_id.default_credit_account_id.id
        else:
            account_dest = self.sheet_id.journal_id.default_credit_account_id.id
        return account_dest



    def action_move_create_cash(self):
        move_group_by_sheet = self._get_account_move_by_sheet()

        move_line_values_by_expense = self._get_account_move_line_values()

        for expense in self:
            if expense.payment_mode == 'own_account':
                company_currency = expense.company_id.currency_id
                different_currency = expense.currency_id != company_currency

                # get the account move of the related sheet
                #move = move_group_by_sheet[expense.sheet_id.id]

                # get move line values
                move_line_values = move_line_values_by_expense.get(expense.id)
                #print(move_line_values)
                move_line_dst = move_line_values[-1]
                #print(move_line_dst)
                total_amount = move_line_dst['debit'] or -move_line_dst['credit']
                total_amount_currency = move_line_dst['amount_currency']

                # create one more move line, a counterline for the total on payable account
                if not expense.sheet_id.journal_id.default_credit_account_id:
                    raise UserError(_("No credit account found for the %s journal, please configure one.") % (
                        expense.sheet_id.journal_id.name))
                journal = expense.sheet_id.journal_id
                # create payment
                payment_methods = journal.outbound_payment_method_ids if total_amount < 0 else journal.inbound_payment_method_ids
                journal_currency = journal.currency_id or journal.company_id.currency_id
                payment = self.env['account.payment'].create({
                        'payment_method_id': payment_methods and payment_methods[0].id or False,
                        'payment_type': 'outbound' if total_amount < 0 else 'inbound',
                        'partner_id': expense.x_partner_id.id,
                        'partner_type': 'supplier',
                        'journal_id': journal.id,
                        'payment_date': expense.date,
                        'state': 'reconciled',
                        'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
                        'amount': abs(total_amount_currency) if different_currency else abs(total_amount),
                        'name': expense.name,
                    })
                move_line_dst['payment_id'] = payment.id


            if expense.payment_mode == 'own_account':
                expense.sheet_id.paid_expense_sheets()

        # post the moves
        # for move in move_group_by_sheet.values():
        #     move.post()

        return move_group_by_sheet



    def action_move_create(self):
        res = super(HrExpense, self).action_move_create()
        self.action_move_create_cash()
        return res
    #
    # def action_move_create(self):
    #     '''
    #     main function that is called when trying to create the accounting entries related to an expense
    #     '''
    #     move_group_by_sheet = self._get_account_move_by_sheet()
    #
    #     move_line_values_by_expense = self._get_account_move_line_values()
    #
    #     for expense in self:
    #         if expense.payment_mode == 'company_account':
    #             company_currency = expense.company_id.currency_id
    #             different_currency = expense.currency_id != company_currency
    #
    #             # get the account move of the related sheet
    #             move = move_group_by_sheet[expense.sheet_id.id]
    #
    #             # get move line values
    #             move_line_values = move_line_values_by_expense.get(expense.id)
    #             move_line_dst = move_line_values[-1]
    #             total_amount = move_line_dst['debit'] or -move_line_dst['credit']
    #             total_amount_currency = move_line_dst['amount_currency']
    #
    #             # create one more move line, a counterline for the total on payable account
    #
    #             if not expense.sheet_id.bank_journal_id.default_credit_account_id:
    #                 raise UserError(_("No credit account found for the %s journal, please configure one.") % (expense.sheet_id.bank_journal_id.name))
    #             journal = expense.sheet_id.bank_journal_id
    #             # create payment
    #             payment_methods = journal.outbound_payment_method_ids if total_amount < 0 else journal.inbound_payment_method_ids
    #             journal_currency = journal.currency_id or journal.company_id.currency_id
    #             payment = self.env['account.payment'].create({
    #                 'payment_method_id': payment_methods and payment_methods[0].id or False,
    #                 'payment_type': 'outbound' if total_amount < 0 else 'inbound',
    #                 'partner_id': expense.employee_id.address_home_id.commercial_partner_id.id,
    #                 'partner_type': 'supplier',
    #                 'journal_id': journal.id,
    #                 'payment_date': expense.date,
    #                 'state': 'reconciled',
    #                 'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
    #                 'amount': abs(total_amount_currency) if different_currency else abs(total_amount),
    #                 'name': expense.name,
    #             })
    #             move_line_dst['payment_id'] = payment.id
    #
    #             # link move lines to move, and move to expense sheet
    #             move.write({'line_ids': [(0, 0, line) for line in move_line_values]})
    #             expense.sheet_id.write({'account_move_id': move.id})
    #
    #
    #             expense.sheet_id.paid_expense_sheets()
    #
    #             # post the moves
    #             for move in move_group_by_sheet.values():
    #                 move.post()
    #
    #     return move_group_by_sheet

    @api.depends('x_expense_line')
    def _compute_amount_sum(self):
        for expense in self:
            expense.unit_amount = sum(expense.x_expense_line.mapped('price_total'))
            expense.untaxed_amount = sum(expense.x_expense_line.mapped('price_subtotal'))
            expense.total_amount = sum(expense.x_expense_line.mapped('price_total'))



    def action_submit_expenses(self):
        # if any(expense.state != 'draft' or expense.sheet_id for expense in self):
        #     raise UserError(_("You cannot report twice the same line!"))
        # if len(self.mapped('employee_id')) != 1:
        #     raise UserError(_("You cannot report expenses for different employees in the same report."))



        todo = self.filtered(lambda x: x.payment_mode=='own_account') or self.filtered(lambda x: x.payment_mode=='company_account')
        return {
            'name': _('New Expense Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'context': {
                'default_expense_line_ids': todo.ids,
                'default_company_id': self.company_id.id,
                'default_employee_id': self[0].employee_id.id,
                'default_name': todo[0].name if len(todo) == 1 else ''
            }
        }






class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    payment_mode = fields.Selection(related='expense_line_ids.payment_mode', default='own_account', readonly=True,
                                    string="Payment Type")

    x_payment_ids = fields.Many2many('account.payment', string="Payment Report")
    x_bank_statement_id = fields.Many2one('account.bank.statement', string="Statement")
    x_statement_state = fields.Selection(related='x_bank_statement_id.state')
    x_statement_state_cu = fields.Boolean(compute="get_state_reconcile")
    x_ownwer_journal = fields.Many2one('account.journal')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('done', 'Paid'),
        ('post', 'Posted'),
        ('reconcile', 'Reconciled'),
        ('cancel', 'Refused')
    ], string='Status', index=True, readonly=True, tracking=True, copy=False, default='draft', required=True,
        help='Expense Report State')

    @api.depends('x_statement_state')
    def get_state_reconcile(self):
        print('test')
        if self.x_statement_state == 'confirm':
           self.x_statement_state_cu = True
           self.write({'state': 'reconcile'})
        else:
            self.x_statement_state_cu = False



    @api.model
    def _default_journal_id(self):
        default_company_id = self.default_get(['company_id'])['company_id']
        default_employee_id = self.default_get(['employee_id'])['employee_id']
        employee = self.env['hr.employee'].search([('id', '=', default_employee_id)])
        journal = self.env['account.journal'].search(
            [('type', '=', 'cash'), ('id', '=', employee.x_cash_account.id), ('company_id', '=', default_company_id)], limit=1)
        return journal.id

    @api.onchange('journal_id')
    def get_journal_id_domain(self):
        res = {}
        res['domain'] = {'journal_id': [('id', '=', self.employee_id.x_cash_account.id)]}
        return res

    @api.model
    def _default_bank_journal_id(self):
        default_company_id = self.default_get(['company_id'])['company_id']
        default_employee_id = self.default_get(['employee_id'])['employee_id']
        employee = self.env['hr.employee'].search([('id', '=', default_employee_id)])
        return self.env['account.journal'].search(
            [('type', 'in', ['cash', 'bank']), ('id', '=', employee.x_bank_account.id), ('company_id', '=', default_company_id)], limit=1)

    @api.onchange('bank_journal_id')
    def get_bank_journal_id_domain(self):
        res = {}
        res['domain'] = {'bank_journal_id': [('id', '=', self.employee_id.x_bank_account.id)]}
        return res


    journal_id = fields.Many2one('account.journal', string='Cash Journal',
                                 states={'done': [('readonly', True)], 'post': [('readonly', True)]},
                                 check_company=True,
                                 domain="[('type', '=', 'cash'), ('company_id', '=', company_id)]",
                                 default=_default_journal_id, help="The journal used when the expense is done.")

    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal',
                                      states={'done': [('readonly', True)], 'post': [('readonly', True)]},
                                      check_company=True,
                                      domain="[('type', 'in', ['cash', 'bank']), ('company_id', '=', company_id)]",
                                      default=_default_bank_journal_id,
                                      help="The payment method used when the expense is paid by the company.")

    @api.constrains('expense_line_ids')
    def _check_payment_mode(self):
        for sheet in self:
            expense_lines = sheet.mapped('expense_line_ids')
            if expense_lines and any(
                    expense.payment_mode != expense_lines[0].payment_mode for expense in expense_lines):
                raise ValidationError(_("Expenses must be paid by the same type (Cash or Credit Card)."))


    def action_sheet_move_create(self):
        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.company.currency_id).rounding))
        res = expense_line_ids.action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date


        self.write({'state': 'post'})
        self.activity_update()

        return res

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

        #return res

    def post_register_payment(self):
        self.ensure_one()
        amount = sum(self.x_payment_ids.mapped('amount'))
        if any(expense.state == 'draft' for expense in self.mapped('x_payment_ids')):
            raise UserError(_("You cannot post a report with a draft payment!"))
        return {
            'name': _('Register Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'views': [
                (self.env.ref('account.view_account_payment_form').id, 'form'),
            ],
            'context': {
                'default_payment_type': 'transfer',
                'default_x_is_expense': True,
                'default_destination_journal_id': self.env['ir.default'].sudo().get('hr.expense.sheet', 'x_ownwer_journal'), #self.x_payment_ids.mapped('journal_id')[0].id or False,
                'default_x_total_expense': sum(self.x_payment_ids.mapped('amount')),
                'default_x_expense_sheet_id': self.id,
                'default_communication': self.name,
                'default_amount': amount,
            },
            'target': 'new',
        }



    def reconcile(self):
        return {
            'name': _('Statement'),
            'res_model': 'account.bank.statement',
            'res_id': self.x_bank_statement_id.id,
            'views': [
                (self.env.ref('account.view_bank_statement_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
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









