# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, Warning
from odoo.tools.misc import formatLang
from functools import partial


class AccountUserStatement(models.Model):
    _inherit = 'account.user.statement'

    cash_on_hand = fields.Float(string="Real Closing Balance", compute="_cash_on_hand")
    cash_total = fields.Float(string="Total Cash", compute="get_cash_total")
    voucher_total = fields.Float(string="Total Vouchers", compute="get_voucher_total")
    return_total = fields.Float(string="Total Cash Returns", readonly=True)
    transaction = fields.Float(string="(-/+) Cash Transaction", compute="get_compute", readonly=True,
                               help="Cash Sales - Total Vouchers - Total Cash Return")
    transaction_pivot = fields.Float(string="Cash Total")
    end_difference = fields.Float(string="Difference", compute="get_compute")
    voucher_count = fields.Integer(string="Voucher", compute="_compute_voucher_count")
    close_cash_ids = fields.One2many('sale.cashbox.close.line', 'statement_id', readonly=True)
    open_cash_ids = fields.One2many('sale.cashbox.line', 'statement_id', readonly=True)
    cheque_total = fields.Float(string="Total Cheques", compute="get_bank_payment")
    card_total = fields.Float(string="Total Credit Cards", compute="get_bank_payment")
    cheque_total_pivot = fields.Float(string="Total Cheques")
    card_total_pivot = fields.Float(string="Total Credit Cards")
    x_account_move_id = fields.Many2one('account.move', string="Difference account", readonly=True)
    user_statement_line_ids = fields.One2many('account.user.statement.line', 'statement_id', string="Transactions",
                                              readonly=True)
    user_statement_cash_line_ids = fields.Many2many('account.user.statement.line', relation='cash_ref', string="Cash Transactions",
                                              readonly=True, compute="_get_only_cash", store=True)
    user_statement_cheque_line_ids = fields.Many2many('account.user.statement.line',  relation='check_ref', string="Cheque Transactions",
                                               readonly=True, compute="_get_only_cheque", store=True)
    user_statement_card_line_ids = fields.Many2many('account.user.statement.line',  relation='credit_card_ref', string="Credit Card Transactions",
                                               readonly=True, compute="_get_only_credit_card", store=True)
    voucher_journal = fields.Many2one('account.journal', compute="get_voucher_journal")  # , compute="get_voucher_journal"
    total_closing = fields.Float(string="Total Closing", digits=(14, 3))
    x_voucher_journal = fields.Many2one('account.journal', string="voucher Journal")
    master_cashier = fields.Many2one('res.users', string="Master Cashier")

    def print_closing_report(self):
        return {'type': 'ir.actions.report', 'report_name': 'pabs_sale_extra.report_closing_template', 'report_type': "qweb-pdf"}


    def group_paymeny(self):
        for order in self:
            # currency = order.currency_id or order.company_id.currency_id
            # fmt = partial(formatLang, self.with_context(lang=order.partner_id.lang).env, currency_obj=currency)
            res = {}
            for line in order.user_statement_card_line_ids:
                # for tax in line.tax_ids:
                group = line.journal_id.name
                res.setdefault(group, {'payment_method': '', 'qty': 0, 'amount': 0.0})
                res[group]['payment_method'] = line.journal_id.name
                res[group]['qty'] += 1
                res[group]['amount'] += line.amount
            # res = sorted(res.items(), key=lambda l: l[0].sequence)
            return res

    # def action_view_create_voucher(self):
    #     self.ensure_one()
    #     return {
    #         'name': _('Vouchers'),
    #         'res_model': 'account.payment',
    #         'view_mode': 'form',
    #         'views': [
    #             (self.env.ref('account.view_account_payment_form').id, 'form'),
    #         ],
    #         'type': 'ir.actions.act_window',
    #         'context': {'default_payment_type': 'transfer',
    #                     'default_journal_id': self.voucher_journal.id,
    #                     'default_destination_journal_id': self.env['ir.default'].sudo().get('account.user.statement','x_voucher_journal'),
    #                     'default_communication': self.name, 'default_statement_id': self.id},
    #         'target': 'new',
    #     }

    def action_open_invoices(self):
        self.ensure_one()
        return {
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_invoice_tree').id, 'tree'),
                (self.env.ref('account.view_move_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'default_type': 'out_invoice'},
            'domain': [('type', '=', 'out_invoice'), ('state', '=', 'posted'), ('invoice_payment_state', '=', 'not_paid')],
        }

    def reset_running(self):
        self.write({'state': 'open'})



    def get_voucher_journal(self):
        for journal in self.terminal_id.mapped('allowed_payment_method').filtered(lambda att: att.journal_account_id.type == 'cash'):
            if journal:
                self.voucher_journal = journal.journal_account_id.id
            else:
                self.voucher_journal = False

    @api.depends('user_statement_line_ids')
    def _get_only_cheque(self):
        list = []
        for line in self.user_statement_line_ids:
            if line.bank_type == 'cheque':
                list.append(line.id)
        self.user_statement_cheque_line_ids = list

    @api.depends('user_statement_line_ids')
    def _get_only_credit_card(self):
        list = []
        for line in self.user_statement_line_ids:
            if line.journal_id.type == 'bank' and not line.bank_type == 'cheque':
                list.append(line.id)
        self.user_statement_card_line_ids = list

    @api.depends('user_statement_line_ids')
    def _get_only_cash(self):
        list = []
        for line in self.user_statement_line_ids:
            if line.journal_id.type == 'cash':
                list.append(line.id)
        self.user_statement_cash_line_ids = list

    # def action_confirm(self):  # closing a session with different amount
    #     res = super(AccountUserStatement, self).action_confirm()
    #     all_move_vals = []
    #     if self.end_difference != 0.0:
    #         journal_id = 0
    #         for journal in self.terminal_id.mapped('allowed_journal').filtered(lambda att: att.type == 'cash'):
    #             journal_id = journal
    #         if journal_id == False:
    #             raise UserError(_(
    #                 'You are trying to close the session without a cash journal... Please ask the master casheir to configure that'))
    #         transfer_move_vals = {
    #             'ref': self.name,
    #             'date': self.date,
    #             'journal_id': journal_id.id,
    #             'type': 'entry',
    #             'line_ids': [
    #                 (0, 0, {
    #                     'name': '',
    #                     'debit': self.end_difference > 0.0 and self.end_difference or 0.0,
    #                     'credit': self.end_difference < 0.0 and -self.end_difference or 0.0,
    #                     'account_id': journal_id.default_debit_account_id.id if self.end_difference > 0.0 else journal_id.default_credit_account_id.id,
    #                 }),
    #                 (0, 0, {
    #                     'name': '',
    #                     'debit': self.end_difference < 0.0 and -self.end_difference or 0.0,
    #                     'credit': self.end_difference > 0.0 and self.end_difference or 0.0,
    #                     'account_id': journal_id.profit_account_id.id if self.end_difference > 0.0 else journal_id.loss_account_id.id,
    #                 }),
    #             ],
    #         }
    #         all_move_vals.append(transfer_move_vals)
    #         move = self.env['account.move'].create(transfer_move_vals)
    #         move.post()
    #         self.x_account_move_id = move
    #     return res

    def action_post_entries(self): #action_confirm(self):  # closing a session with different amount
        #res = super(AccountUserStatement, self).action_confirm()
        statement_line_vals = []
        print(self.end_difference)
        if self.end_difference != 0.0:
            vals = {
                'name': 'Difference',
                'statement_id': self.bank_statement_id.id,
                'journal_id': '',
                'date': fields.Date.today(),
                'amount': self.end_difference,
                # 'note': '',
                # 'transaction_type': '',
                'partner_id': self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1).address_home_id.id,
                'ref': self.name,
                'user_id': self.user_id.id,
                'statement_user_id': self.id,
            }
            statement_line_vals.append((0, 0, vals))
        if self.voucher_total != 0.0:
            vals = {
                'name': 'Total Voucher - %s' %(self.name),
                'statement_id': self.bank_statement_id.id,
                'journal_id': '',
                'date': fields.Date.today(),
                'amount': self.voucher_total,
                # 'note': '',
                # 'transaction_type': '',
                'ref': self.name,
                'user_id': self.user_id.id,
                'statement_user_id': self.id,
            }
            statement_line_vals.append((0, 0, vals))
        if self.return_total != 0.0:
            vals = {
                'name': 'Total Return - %s' %(self.name),
                'statement_id': self.bank_statement_id.id,
                'journal_id': '',
                'date': fields.Date.today(),
                'amount': self.return_total,
                # 'note': '',
                # 'transaction_type': '',
                'ref': self.name,
                'user_id': self.user_id.id,
                'statement_user_id': self.id,
            }
            statement_line_vals.append((0, 0, vals))
        if self.cash_total != 0.0:
            vals = {
                'name': self.name,
                'statement_id': self.bank_statement_id.id,
                'journal_id': '',
                'date': fields.Date.today(),
                'amount': self.cash_total,
                # 'note': '',
                #'transaction_type': '',
                'ref': self.name,
                'user_id': self.user_id.id,
                'statement_user_id': self.id,
            }
            statement_line_vals.append((0, 0, vals))
        # if self.total_closing != 0.0:
        #     vals = {
        #         'name': 'Opening Cash',
        #         'statement_id': self.bank_statement_id.id,
        #         'journal_id': '',
        #         'date': fields.Date.today(),
        #         'amount': -self.total_closing,
        #         # 'note': '',
        #         #'transaction_type': '',
        #         'ref': self.name,
        #         'user_id': self.user_id.id,
        #         'statement_user_id': self.id,
        #     }
        #     statement_line_vals.append((0, 0, vals))
        # if self.cash_on_hand != 0.0:
        #     vals = {
        #         'name': 'Cash on Hand',
        #         'statement_id': self.bank_statement_id.id,
        #         'journal_id': '',
        #         'date': fields.Date.today(),
        #         'amount': self.cash_on_hand,
        #         # 'note': '',
        #         #'transaction_type': '',
        #         'ref': self.name,
        #         'user_id': self.user_id.id,
        #     }
        #     statement_line_vals.append((0, 0, vals))



        #self.env['account.bank.statement.line'].create(statement_line_vals)
        self.bank_statement_id.write({'line_ids': statement_line_vals})
        #return res


    def _compute_voucher_count(self):
        for statement in self:
            statement.voucher_count = self.env['account.payment'].search_count(
                [('statement_id', '=', statement.id)])


    def action_view_voucher_transfer(self):
        self.ensure_one()
        return {
            'name': _('Vouchers'),
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_account_payment_tree').id, 'tree'),
                (self.env.ref('account.view_account_payment_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('statement_id', '=', self.id)],
        }


    def action_view_transaction(self):
        self.ensure_one()
        return {
            'name': _('Statement Line'),
            'res_model': 'account.user.statement.line',
            'view_mode': 'tree,search',
            'views': [
                (self.env.ref('pabs_sale_extra.view_account_user_statement_line_tree').id, 'tree'),
                (self.env.ref('pabs_sale_extra.view_account_user_statement_line_default_group').id, 'search'),
            ],
            # 'search_view_id': (self.env.ref('pabs_sale_extra.view_account_bank_statement_line_default_group').id),
            'type': 'ir.actions.act_window',
            'domain': [('statement_id', '=', self.id)],
            'context': {'search_default_group_by_journal_id': 1},
        }

    def action_view_payment(self):
        self.ensure_one()
        payment_ids = []
        for payment in self.user_statement_line_ids:
            payment_ids.append(payment.payment_id.id)
        return {
            'name': _('Payments'),
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_account_payment_tree').id, 'tree'),
                (self.env.ref('account.view_account_payment_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': ['|', ('id', 'in', payment_ids), ('x_session_id', '=', self.id)],
            'context': {'group_by': ['journal_id', 'state'], 'default_x_session_id': self.id, 'default_payment_type': 'inbound'},
        }



    def action_view_demonation(self):
        self.ensure_one()
        check = self.env['sale.statement.cashbox'].search([('session_id', '=', self.id)])
        return {
            'name': _('Statement Line'),
            'res_model': 'sale.statement.cashbox',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('pabs_sale_extra.sale_statement_cashbox_view_form').id, 'form'),

            ],
            'type': 'ir.actions.act_window',
            'domain': [('session_id', '=', self.id)],
            'context': {'default_session_id': self.id},
            'res_id': check.id,
        }


    def action_start_sales(self):
        self.ensure_one()
        # domain = []
        # context = {}
        # groups = self.env['res.groups'].search([('users', 'in', self.user_id.id), ('category_id', 'in', self.env.ref('pabs_sale_extra.module_category_sales_custom').ids)], limit=1)
        # if groups.id == self.env.ref('pabs_sale_extra.group_cash_memo_sale').id:
        #     domain = [('sale_order_type','=', 'cash_memo')]
        #     context = {'default_sale_order_type': 'cash_memo'}
        #
        # elif groups.id == self.env.ref('pabs_sale_extra.group_cash_pod').id:
        #     domain = [('sale_order_type', '=', 'paid_on_delivery')]
        #     context = {'default_sale_order_type': 'paid_on_delivery'}
        #
        # elif groups.id == self.env.ref('pabs_sale_extra.group_service').id:
        #     domain = [('sale_order_type', '=', 'service')]
        #     context = {'default_sale_order_type': 'service'}
        #
        # elif groups.id == self.env.ref('pabs_sale_extra.group_advanced_payment').id:
        #     domain = [('sale_order_type', '=', 'advance_payment')]
        #     context = {'default_sale_order_type': 'advance_payment'}
        #
        # elif groups.id == self.env.ref('pabs_sale_extra.group_credit_sale').id:
        #     domain = [('sale_order_type', '=', 'credit_sale')]
        #     context = {'default_sale_order_type': 'credit_sale'}

        return {
            'name': "Orders", #groups.name,
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('sale.view_quotation_tree').id, 'list'),
                (self.env.ref('sale.view_order_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            # 'context': context,
            # 'domain': domain,
        }


    def get_voucher_total(self):
        for cash in self:
            voucher_id = self.env['account.payment'].search([('statement_id', '=', cash.id), ('state', 'not in', ['draft', 'cancelled'])])
            if cash.voucher_count > 0:
                total = sum(voucher_id.mapped('amount'))
                cash.voucher_total = -total
            else:
                cash.voucher_total = 0.0


    def get_cash_total(self):
        for cash in self:
            total = 0.0
            returns = 0.0
            for statement in cash.user_statement_line_ids:
                if statement.journal_id.type == 'cash' and statement.amount > 0:
                    total += statement.amount
                elif statement.journal_id.type == 'cash' and statement.amount < 0 and statement.transaction_type != 'transfer':
                    returns += statement.amount
            cash.cash_total = total
            cash.return_total = returns


    @api.onchange('end_difference')
    def get_compute(self):
        for statement in self:
            statement.balance_end = statement.balance_start + (
                    statement.cash_total - abs(statement.voucher_total) - abs(statement.return_total))
            statement.transaction = statement.cash_total - abs(statement.voucher_total) - abs(statement.return_total)
            statement.cash_on_hand = sum(statement.close_cash_ids.mapped('subtotal'))
            statement.end_difference = statement.cash_on_hand - statement.balance_end
            statement.transaction_pivot = statement.transaction
            currency = statement.currency_id
            if currency.is_zero(statement.end_difference):
                statement.end_difference = 0

    def _cash_on_hand(self):
        for statement in self:
            statement.cash_on_hand = sum(statement.close_cash_ids.mapped('subtotal'))


    def get_bank_payment(self):
        for statement in self:
            if not statement.cheque_total:
                statement.cheque_total = 0.0
            if not statement.card_total:
                statement.card_total = 0.0
            for payment in statement.mapped('user_statement_line_ids'):
                if payment.journal_id.type == 'bank' and not payment.journal_id.x_bank_type == 'cheque':
                    statement.card_total += payment.amount
                elif payment.journal_id.type == 'bank' and payment.journal_id.x_bank_type == 'cheque':
                    statement.cheque_total += payment.amount
            statement.cheque_total_pivot = statement.cheque_total
            statement.card_total_pivot = statement.card_total

    # @api.model
    # def create(self, vals):
    #     res = super(AccountUserStatement, self).create(vals)
    #
    #     return res


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _onchange_journal_custom(self):
        # res = {}
        # journal = self.env['account.journal'].search([('x_bill_journal', '!=', False)])
        # print(journal)
        # if self.env.context.get('active_model') == 'account.move':
        #     res['domain'] = {'journal_id': [('id', 'in', journal.ids), ('type', 'in', ('bank', 'cash'))]}
        # return res
        journal = self.env['account.journal'].search([('x_bill_journal', '!=', False)])
        if self.env.context.get('active_model') == 'account.move':
            return [('id', 'in', journal.ids), ('type', 'in', ('bank', 'cash'))]

    statement_id = fields.Many2one('account.user.statement', string="Statement")
    x_bank_statement_id = fields.Many2one('account.bank.statement')
    x_amount_to_deposit = fields.Monetary(related="x_bank_statement_id.x_amount_to_deposit")
    x_batch_payment_id = fields.Many2one('account.batch.payment')
    x_cashbox_id = fields.One2many('sale.cashbox.line', 'payment_id', string='Cash', readonly=True, states={'draft': [('readonly', False)]})
    x_bank_type = fields.Selection(related='journal_id.x_bank_type')
    x_auth = fields.Char(string="Auth Code")
    x_tid = fields.Many2one('bank.card.readers', string="TID")
    x_batch = fields.Char(string="Batch")
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]}, tracking=True,
                                 domain=_onchange_journal_custom)
    x_voucher_no = fields.Char(string="Voucher No.")
    x_deposit_amount = fields.Monetary(string='Deposit Amount')
    x_batch_line_id = fields.Many2one('account.payment', string="Batch Payment", copy=False)
    x_session_id = fields.Many2one('account.user.statement', string="Session")
    x_batch_statement = fields.Many2one('account.bank.statement', related="batch_payment_id.x_bank_statement_id")
    x_is_tranfered = fields.Boolean(string="validated ?", default=False, copy=False)
    x_is_cancelled = fields.Boolean(string="cancelled ?", default=False, copy=False)
    x_return_payment_batch_id = fields.Many2one('account.batch.payment', string="Returned Batch")
    x_cheque_date = fields.Date(string='Cheque Date')
    x_cheque_number = fields.Char(string='Cheque Number')
    x_bank_id = fields.Many2one('res.bank', string='Bank Account')
    x_account_number = fields.Char(string='Bank Account Number')

    #x_payment_methods = fields.Many2one("statement.payment.methods", string="Payment Method")

    #amount = fields.Monetary(string='Amount', required=True, tracking=True)



    def post(self):
        res = super(AccountPayment, self).post()
        statement_line_vals = []
        for payment in self:
            statement_line = self.env['account.user.statement.line'].search([('payment_id', '=', payment.id)], limit=1)
            if statement_line:
                statement_line.update({'amount': payment.amount, 'journal_id': payment.journal_id.id})

            bank_stmt = self.env['account.bank.statement.line'].search([('x_batch_line_id', '=', payment.id)], limit=1)
            if bank_stmt:
                bank_stmt.update({'amount': -payment.amount, 'journal_id': payment.journal_id.id})
            statement = self.env['account.user.statement'].search([('id', '=', self._context.get('active_id') or self._context.get('active_ids'))])
            bank_statement = self.env['account.bank.statement'].search([('id', '=', self._context.get('active_id'))])
            if bank_statement and self.env.context.get('is_voucher') and payment.journal_id and payment.destination_journal_id:
                vals = {
                    'name': 'Cash Voucher',
                    #'statement_id': statement.id,
                    'journal_id': self.journal_id.id,
                    'date': self.payment_date,
                    'amount': -self.amount,
                    #'transaction_type': self.payment_type,
                    'ref': self.name,
                    'partner_id': self.partner_id.id,
                    'note': self.communication,
                    'x_batch_line_id': self.id,
                }
                bank_statement.write({'line_ids': [(0, 0, vals)]})
            if statement and self.env.context.get('active_model') == 'account.user.statement' and payment.x_session_id:
                vals_p = {
                    'name': self.name + "," + statement.name,
                    'statement_id': statement.id,
                    'journal_id': self.journal_id.id,
                    'date': self.payment_date,
                    'amount': self.amount,
                    'transaction_type': self.payment_type,
                    'partner_id': self.partner_id.id,
                    'note': self.communication,
                    'cheque_date': self.cheque_date,
                    'cheque_number': self.cheque_number,
                    'bank_id': self.bank_id.id,
                    'account_number': self.account_number,
                    'cheque_type': self.x_cheque_type,
                    'auth': self.x_auth,
                    'tid': self.x_tid.id,
                    'batch': self.x_batch,
                    'benefit_ref': self.x_benefit_ref,
                    'payment_id': self.id,
                }
                if self.payment_type == 'outbound':
                    vals_p['amount'] = -vals_p['amount']

                statement.write({'user_statement_line_ids': [(0, 0, vals_p)]})

            if self.x_bank_statement_id and self.x_deposit_amount != 0.0:
                if self.amount != self.x_deposit_amount:
                    raise UserError(_("The transfer amount counted from cash denomination should be equal to deposit amount"))
            if sum(payment.x_cashbox_id.mapped('subtotal')) != 0.0:
                if self.x_bank_statement_id and not bank_stmt:
                    vals = {
                        'name': 'Cash Deposit',
                        'statement_id': self.x_bank_statement_id.id,
                        #'journal_id': '',
                        'date': self.payment_date,
                        'amount': -self.amount,
                        # 'transaction_type': '',
                        'ref': self.name,
                        'user_id': self.env.user.id,
                        #'statement_user_id': self.statement_id.id,
                        'x_batch_line_id': self.id,
                    }
                    statement_line_vals.append((0, 0, vals))
                    self.x_bank_statement_id.write({'line_ids': statement_line_vals})

        return res

    def cancel(self):
        res = super(AccountPayment, self).cancel()
        # self.env['account.user.statement.line'].search([('voucher_payment_id', '=', self.id)], limit=1).unlink()
        self.env['account.user.statement.line'].search([('payment_id', '=', self.id)], limit=1).unlink()
        self.env['account.bank.statement.line'].search([('x_batch_line_id', '=', self.id)]).with_context(force_delete=True).unlink()
        # for batch in self.env['account.bank.statement.line'].search([('x_batch_line_id', '=', self.x_batch_line_id.id)]):
        #     statement = batch.statement_id
        #     batch.button_cancel_reconciliation()
        #     batch.unlink()
        #     statement._end_balance()
        return res

    # def action_draft(self):
    #     res = super(AccountPayment, self).action_draft()
    #
    #     return res

    # @api.onchange('active_id')
    # def _onchange_journal_custom(self):
    #     res = {}
    #     journal = self.env['account.journal'].search([('x_bill_journal', '!=', False)])
    #     print(journal)
    #     if self.env.context.get('active_model') == 'account.move':
    #         res['domain'] = {'journal_id': [('id', 'in', journal.ids), ('type', 'in', ('bank', 'cash'))]}
    #     return res

    def _create_statement_line_values(self, vals):
        values = {
            'name': vals['name'],
            'statement_id': self.env['account.user.statement'].search(
                [('user_id', '=', self.env.user.id), ('state', '=', 'open')]).id,
            'journal_id': vals['journal_id'],
            'date': vals['payment_date'],
            # 'user_id': self.env.user.id,
            'amount': vals['amount'],
            'note': vals['communication'],
            'transaction_type': vals['payment_type'],
            'ref': 'To %s Journal' % vals['destination_journal_id'].name,
            # 'partner_id': vals['partner_id'],
            # 'statement_user_id':
        }
        return values

    @api.onchange('journal_id', 'payment_type')
    def get_default_demonations(self):
        self.ensure_one()
        active_id = self._context.get('active_ids') or self._context.get('active_id')
        if self.env['account.move'].search([('id', '=', active_id)]).type not in ['in_invoice', 'in_refund']:
            if self.journal_id.type == 'cash' and self.payment_type == 'transfer' and self._context.get('active_model') == "account.bank.statement":
                if len(self.x_cashbox_id) == 0:
                    self['x_cashbox_id'] = [
                        (0, 0, {'coin_value': 20.0}), (0, 0, {'coin_value': 10.0}), (0, 0, {'coin_value': 5.0}),
                        (0, 0, {'coin_value': 1.0}), (0, 0, {'coin_value': 0.500}), (0, 0, {'coin_value': 0.100}),
                        (0, 0, {'coin_value': 0.050}), (0, 0, {'coin_value': 0.025}), (0, 0, {'coin_value': 0.010}),
                        (0, 0, {'coin_value': 0.005}), ]
            # else:
            #     self.write({'x_cashbox_id': [(5, 0, 0)], 'amount': 0.0})

    @api.onchange('x_cashbox_id')
    def get_total_amount(self):
        for demonation in self:
            if len(demonation.x_cashbox_id) != 0:
                demonation.amount = sum(demonation.x_cashbox_id.mapped('subtotal'))
        # if self.amount == 0.0 and self._context.get('active_model') == "account.bank.statement" and self.env['account.bank.statement'].search([('id', '=', self._context.get('active_id'))]):
        #     self.x_deposit_amount = self.env['account.bank.statement'].search(
        #         [('id', '=', self._context.get('active_id'))]).x_amount_to_deposit

    # @api.onchange('amount', 'currency_id')
    # def onchange_get_journal_wizard(self):
    #     res = {}
    #     if self._context.get('default_payment_type') == 'transfer' and self.env['account.bank.statement'].search([('id', '=', self._context.get('active_id'))]):
    #        res['domain'] = {'destination_journal_id': [('journal_group_ids.id', '=', 3)]}
    #     return res

    def post_batch_line_transfer(self):
        statement_line_vals = []
        id = False
        statement = False
        for line in self:
            vals = {
                'payment_date': line.batch_payment_id.date,
                'journal_id': line.batch_payment_id.journal_id.id,
                'amount': line.amount,
                'communication': '%s, %s' % (line.batch_payment_id.name or '', line.cheque_number or ''),
                'payment_type': 'transfer',
                'destination_journal_id': line.batch_payment_id.x_deposit_to.id,
                'payment_method_id': line.batch_payment_id.payment_method_id.id,
                'x_batch_payment_id': line.batch_payment_id.id,
                'cheque_number': line.cheque_number,
                'cheque_date': line.cheque_date,
                'account_number': line.account_number,
                'bank_id': line.bank_id.id,
                'x_batch_line_id': line.id,
            }
            id = self.env['account.payment'].create([vals])
            line.x_is_tranfered = True
            id.post()

        if self.batch_payment_id.x_bank_statement_id:
            for lines in self:
                vals = {
                    'name': lines.name,
                    'statement_id': lines.batch_payment_id.x_bank_statement_id.id,
                    'journal_id': lines.journal_id.id,
                    'date': lines.batch_payment_id.date,
                    'amount': lines.amount,
                    'ref': lines.communication,
                    'x_batch_line_id': lines.id,

                }
                statement_line_vals.append((0, 0, vals))
                vals_min = {
                    'name': 'Transfer - %s' % lines.batch_payment_id.name,
                    'statement_id': lines.batch_payment_id.x_bank_statement_id.id,
                    'journal_id': lines.journal_id.id,
                    'date': lines.batch_payment_id.date,
                    'amount': -lines.amount,
                    'ref': lines.communication,
                    'x_batch_line_id': lines.id,
                    'x_batch_line_transfer_id': id.id,
                }
                statement_line_vals.append((0, 0, vals_min))
        self.batch_payment_id.x_bank_statement_id.write({'line_ids': statement_line_vals})

        b_statement = self.env['account.bank.statement.line']

        move_lines_transfer = id.move_line_ids.filtered(lambda x: x.account_id.id == 34)
        st_line_minus = b_statement.search([('x_batch_line_transfer_id', '=', id.id), ('amount', '<', 0)], limit=1)
        if st_line_minus:
            self.auto_cheque_reconsile(st_line_minus.ids, self.auto_cheque_reconcile_data(self.partner_id.id,  move_lines_transfer.ids))

        move_lines_cheque = self.move_line_ids.filtered(lambda x: x.account_id.id == 34)
        st_line_plus = b_statement.search([('x_batch_line_id', '=', self.id), ('amount', '>', 0)], limit=1)
        if st_line_plus:
            self.auto_cheque_reconsile(st_line_plus.ids, self.auto_cheque_reconcile_data(self.partner_id.id,  move_lines_cheque.ids))

    def auto_cheque_reconsile(self, st_line_ids, data):
        self.env['account.reconciliation.widget'].process_bank_statement_line(st_line_ids, data)

    def auto_cheque_reconcile_data(self, partner, payment_aml_ids):
        return  [{'partner_id': partner, 'counterpart_aml_dicts': [], 'payment_aml_ids': payment_aml_ids, 'new_aml_dicts': [],
          'to_check': False}]


    def unlink_from_batch(self):
        for line in self:
            statement = line.batch_payment_id.x_bank_statement_id.line_ids.search(
                [('x_batch_line_id', '=', line.id)])
            if statement:
                statement.button_cancel_reconciliation()
                statement.unlink()
                self.search([('x_batch_line_id', '=', line.id)], limit=1).cancel()
            line.x_return_payment_batch_id = line.batch_payment_id.id
            line.batch_payment_id = False
            # send_money = self.copy({'payment_type': 'outbound'})
            # send_money.post()
            line.x_is_check_return = True
            line.x_is_cancelled = True







class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    x_deposit_to = fields.Many2one('account.journal', string="Deposit To", domain=[('type', '=', 'bank'), ('x_bank_type', '=', False), ('journal_group_ids.name', '=', 'Banks')])
    transfer_count = fields.Integer(string="Internal Transfer", compute="_compute_transfer_count")
    x_bank_statement_id = fields.Many2one('account.bank.statement', string="Statement")
    x_amount_in_words = fields.Char(string='Amount in words', compute='amt_total')
    x_deposit_type = fields.Many2one('batch.deposit.types', string="Deposit Type")
    state = fields.Selection([('draft', 'New'), ('submit', 'Submitted'), ('sent', 'Sent'), ('reconciled', 'Reconciled')], readonly=True, default='draft', copy=False)
    x_count_check = fields.Integer(string="Returned Cheques", compute="_count_returned_cheque")


    @api.onchange('payment_ids', 'date')
    def get_line_limit(self):
        for batch in self:
            if len(batch.payment_ids) > 6:
                raise Warning(_('Cannot add more than 6 payments'))
            for line in self.payment_ids:
                if line.cheque_date and self.date:
                    if line.cheque_date > self.date:
                        raise Warning(_('Cannot add cheques payment (cheque date: %s)' %(line.cheque_date)))

    def _compute_transfer_count(self):
        for transfer in self:
            transfer.transfer_count = self.env['account.payment'].search_count(
                [('x_batch_payment_id', '=', transfer.id)])

    def post_internal_transfer(self):

        for batch in self:
            val = {
                'name': self.name,
                # 'name': '%s/%s' % (batch.journal_id.name, str(fields.Date.today())),
                'journal_type': 'bank',
                'journal_id': batch.journal_id.id,
                'date': fields.Date.today(),
                # 'statement_for_pabs': True,
                # 'balance_start': 0.0,
            }
            statement = batch.x_bank_statement_id = self.env[
                'account.bank.statement'].create(val)
            if statement:
                batch.x_bank_statement_id = statement.id

            for payment in self.payment_ids:
                if payment.x_is_cancelled:
                    payment.x_is_cancelled = False


    def action_view_cheque_statement(self):
        self.ensure_one()
        return {
            'name': _('Cheque Statement'),
            'res_model': 'account.bank.statement',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'res_id': self.x_bank_statement_id.id,
        }

    def action_view_internal_transfer(self):
        self.ensure_one()
        return {
            'name': _('Transfer'),
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_account_payment_tree').id, 'tree'),
                (self.env.ref('account.view_account_payment_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('x_batch_payment_id', '=', self.id)],
        }

    def amt_total(self):
        x_amount_total = 0
        for payments in self:
            for payment in payments.payment_ids:
                x_amount_total += payment.amount
        self.x_amount_in_words = self.currency_id.amount_to_text(x_amount_total)

    def action_to_draft(self):
        if self.state != 'draft':
            self.update({'state': 'draft'})

    def action_to_submit(self):
        if self.state == 'draft':
            self.update({'state': 'submit'})


    def validate_batch(self):
        records = self.filtered(lambda x: x.state == 'submit')
        for record in records:
            record.payment_ids.write({'state':'sent', 'payment_reference': record.name})
        records.write({'state': 'sent'})

        return self.filtered('file_generation_enabled').export_batch_payment()

    def action_view_returned_check(self):
        self.ensure_one()
        return {
            'name': _('Returned Cheque'),
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_account_payment_tree').id, 'tree'),
                (self.env.ref('account.view_account_payment_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('x_return_payment_batch_id', '=', self.id)],
        }

    def _count_returned_cheque(self):
        for batch in self:
            batch.x_count_check = self.env['account.payment'].search_count([('x_return_payment_batch_id', '=', self.id)])

class BatchDepositTypes(models.Model):
    _name = 'batch.deposit.types'
    _description = 'Batch Deposit Type'

    name = fields.Char(string="Type")



class SalesCashboxLine(models.Model):
    _name = 'sale.cashbox.line'
    _description = 'Sale CashBox Line'
    _rec_name = 'coin_value'
    _order = 'coin_value desc'

    @api.depends('coin_value', 'number')
    def _sub_total(self):
        """ Calculates Sub total"""
        for cashbox_line in self:
            cashbox_line.subtotal = cashbox_line.coin_value * cashbox_line.number

    coin_value = fields.Float(string='Coin/Bill Value', required=True, digits=(14, 3))
    number = fields.Integer(string='#Coins/Bills', help='Opening Unit Numbers')
    subtotal = fields.Float(compute='_sub_total', string='Subtotal', digits=(14, 3), readonly=True)
    cashbox_id = fields.Many2one('sale.statement.cashbox', string="Cashbox")
    currency_id = fields.Many2one('res.currency')
    payment_id = fields.Many2one('account.payment', string="Payment Ref")
    statement_id = fields.Many2one('account.user.statement', string="Session")


class AccountBankStmtCashWizard(models.Model):
    """
    Account Bank Statement popup that allows entering cash details.
    """
    _name = 'sale.statement.cashbox'
    _description = 'Sale Statement Cashbox'

    cashbox_lines_ids = fields.One2many('sale.cashbox.line', 'cashbox_id', string='Cashbox Lines')
    session_id = fields.Many2one('account.user.statement', string="Session")
    current_session_id = fields.Many2one('account.user.statement', string="Current session")
    terminal_id = fields.Many2one('sale.terminal', string="Terminal")
    total_openings = fields.Float(string="Total opening", digits=(14, 3))
    total = fields.Float(compute='_compute_total', digits=(14, 3))
    currency_id = fields.Many2one('res.currency')

    @api.depends('cashbox_lines_ids', 'cashbox_lines_ids.coin_value', 'cashbox_lines_ids.number')
    def _compute_total(self):
        for cashbox in self:
            cashbox.total = sum([line.subtotal for line in cashbox.cashbox_lines_ids])

    def name_get(self):
        result = []
        for cashbox in self:
            result.append((cashbox.id, _("%s") % (cashbox.total)))
        return result

    # @api.model_create_multi
    # def create(self, vals):
    #     cashboxes = super(AccountBankStmtCashWizard, self).create(vals)
    #     cashboxes.validate_cashbox()
    #     return cashboxes
    #
    # def write(self, vals):
    #     res = super(AccountBankStmtCashWizard, self).write(vals)
    #     self.validate_cashbox()
    #     return res

    def validate_cashbox(self):
        demonation = []
        # if self.total_openings != self.total:
        #     raise UserError(_('Total Domination Does Not Match The Total Opening'))
        user_statement = self.env['account.user.statement'].search(
            [('user_id', '=', self.env.uid), ('state', '=', 'open')], limit=1)
        if not self.current_session_id and not user_statement:
            user_statement = self.env['account.user.statement'].create({
                'user_id': self.env.uid,
                'name': '%s/%s/%s' % (self.terminal_id.allowed_team.x_short_name, self.terminal_id.short_name, self.terminal_id.sequence_id.next_by_id()),
                'start_at': fields.Datetime.now(),
                'terminal_id': self.terminal_id.id,
                'master_cashier': self.terminal_id.master_cashier.id,
                'bank_statement_id': self.terminal_id.cash_statement_id.id,
                'total_closing': self.total_openings,
                'is_receivable': self._context.get('is_receivable'),
            })
            print(self._context.get('is_receivable'))
            # self.env['ir.sequence'].next_by_code(
            #     self.env['ir.sequence'].search([('id', '=', self.terminal_id.sequence_id.id)]).code)

        self.session_id = user_statement.id

        # elif user_statement and not self.current_session_id:
        #     raise UserError(_("You cannot create two active sessions with the same responsible."))

        if self.session_id:
            if len(self.session_id.open_cash_ids) == 0:
                for value in self.mapped('cashbox_lines_ids'):
                    demonation.append((0, 0, {'coin_value': value.coin_value, 'number': value.number}))
            else:
                for value in self.mapped('cashbox_lines_ids'):
                    demonation.append((1, 0, {'coin_value': value.coin_value, 'number': value.number}))
            self.session_id.update({'balance_start': self.total_openings})
            self.session_id.write({'open_cash_ids': demonation, 'balance_start': self.total_openings})
        return self.session_id.terminal_id._open_session(self.session_id.id)

    @api.onchange('cashbox_lines_ids')
    def get_default_amount(self):
        self.ensure_one()
        if len(self.cashbox_lines_ids) == 0 and sum(self.cashbox_lines_ids.mapped('number')) == 0:
            self['cashbox_lines_ids'] = [
                (0, 0, {'coin_value': 20.0}), (0, 0, {'coin_value': 10.0}), (0, 0, {'coin_value': 5.0}),
                (0, 0, {'coin_value': 1.0}), (0, 0, {'coin_value': 0.500}), (0, 0, {'coin_value': 0.100}),
                (0, 0, {'coin_value': 0.050}), (0, 0, {'coin_value': 0.025}), (0, 0, {'coin_value': 0.010}),
                (0, 0, {'coin_value': 0.005}),
            ]


class SalesCashboxCloseLine(models.Model):
    _name = 'sale.cashbox.close.line'
    _description = 'Sale CashBox Close Line'
    _rec_name = 'coin_value'
    _order = 'coin_value desc'

    @api.depends('coin_value', 'number')
    def _sub_total(self):
        """ Calculates Sub total"""
        for cashbox_line in self:
            cashbox_line.subtotal = cashbox_line.coin_value * cashbox_line.number

    coin_value = fields.Float(string='Coin/Bill Value', required=True, digits=(14, 3))
    number = fields.Integer(string='#Coins/Bills', help='Opening Unit Numbers')
    subtotal = fields.Float(compute='_sub_total', string='Subtotal', digits=(14, 3), readonly=True)
    cashbox_id = fields.Many2one('sale.statement.cashbox.close', string="Cashbox")
    currency_id = fields.Many2one('res.currency')
    payment_id = fields.Many2one('account.payment', string="Payment Ref")
    statement_id = fields.Many2one('account.user.statement', string="Session")



class AccountBankStmtCashCloseWizard(models.Model):
    """
    Account Bank Statement popup that allows entering cash details.
    """
    _name = 'sale.statement.cashbox.close'
    _description = 'Sale Statement Cashbox close'

    cashbox_close_line_ids = fields.One2many('sale.cashbox.close.line', 'cashbox_id', string='Cashbox Close Lines')
    session_id = fields.Many2one('account.user.statement', string="Session")
    session_state = fields.Selection(related="session_id.state")
    total = fields.Float(compute='_compute_total', digits=(14, 3))
    currency_id = fields.Many2one('res.currency')
    to_validate = fields.Boolean(string="to validate?", default=False)
    total_openings = fields.Float(string="Total opening", digits=(14, 3))
    difference = fields.Float(string="Difference", digits=(14, 3), compute="get_closing_difference", store=True)


    @api.depends('total', 'cashbox_close_line_ids')
    def get_closing_difference(self):
        for cashbox in self:
            cashbox.difference = cashbox.total - cashbox.session_id.balance_end

    @api.depends('cashbox_close_line_ids', 'cashbox_close_line_ids.coin_value', 'cashbox_close_line_ids.number')
    def _compute_total(self):
        for cashbox in self:
            cashbox.total = sum([line.subtotal for line in cashbox.cashbox_close_line_ids])

    def name_get(self):
        result = []
        for cashbox in self:
            result.append((cashbox.id, _("%s") % (cashbox.total)))
        return result

    # @api.model_create_multi
    # def create(self, vals):
    #     cashboxes = super(AccountBankStmtCashCloseWizard, self).create(vals)
    #     cashboxes.validate_close_cashbox()
    #     return cashboxes

    # def write(self, vals):
    #     res = super(AccountBankStmtCashCloseWizard, self).write(vals)
    #     self.validate_close_cashbox()
    #     return res

    def save_draft(self):
        demonation = []
        # if self.difference != 0.0:
        #     raise UserError(_("You have differences"))
        if self.session_id:
            if len(self.session_id.close_cash_ids) == 0:
                for value in self.mapped('cashbox_close_line_ids'):
                    demonation.append((0, 0, {'coin_value': value.coin_value, 'number': value.number}))
            else:
                for value in self.mapped('cashbox_close_line_ids'):
                    demonation.append((1, 0, {'coin_value': value.coin_value, 'number': value.number}))
            self.session_id.write({'close_cash_ids': demonation})
        if self.session_id and self.to_validate:
           self.session_id.write({'state': 'to_validate', 'stop_at': fields.Datetime.now()})

    def validate_close_cashbox(self):
        if self.session_id and self.to_validate:
            self.session_id.action_to_validate()
            self.session_id.action_post_entries()



    @api.onchange('cashbox_close_line_ids')
    def get_default_close_amount(self):
        self.ensure_one()
        if len(self.cashbox_close_line_ids) == 0 and sum(self.cashbox_close_line_ids.mapped('number')) == 0:
            self['cashbox_close_line_ids'] = [
                (0, 0, {'coin_value': 20.0}), (0, 0, {'coin_value': 10.0}), (0, 0, {'coin_value': 5.0}),
                (0, 0, {'coin_value': 1.0}), (0, 0, {'coin_value': 0.500}), (0, 0, {'coin_value': 0.100}),
                (0, 0, {'coin_value': 0.050}), (0, 0, {'coin_value': 0.025}), (0, 0, {'coin_value': 0.010}),
                (0, 0, {'coin_value': 0.005}),
            ]

class AccountCashboxLine(models.Model):
    _inherit = 'account.cashbox.line'


    x_team_id = fields.Many2one('crm.team', string="Team")
    x_user_id = fields.Many2one('res.users', string="Responsible")
    x_terminal_id = fields.Many2one('sale.terminal', string="Terminal")
    x_member_ids = fields.One2many(related="x_terminal_id.allowed_team.member_ids")
    x_current_session_state = fields.Char(related="x_terminal_id.current_session_state")
    x_master_cashier = fields.Many2one('res.users', string="Master Cashier")


    @api.onchange('x_team_id')
    def _domain_terminal_id(self):
        res = {}
        res['domain'] = {'x_terminal_id': [('allowed_team', '=', self.x_team_id.id)]}
        return res

    @api.onchange('x_user_id')
    def _onchange_resonsible_id(self):
        for line in self:
            line.number = 1
            if line.x_user_id:
                line.x_master_cashier = self.env.user.id
            else:
                line.x_master_cashier = False












#
# class AccountPaymentRegisterCustom(models.TransientModel):
#     _inherit = 'account.payment.register.custom'
#
#     @api.model
#     def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
#         result = super(AccountPaymentRegisterCustom, self).fields_view_get(view_id=view_id, view_type=view_type,
#                                                                            toolbar=toolbar, submenu=submenu)
#         result['arch'] = self._apply_payment_method_buttons(result['arch'])
#         return result
#
#     @api.model
#     def _apply_payment_method_buttons(self, view_arch):
#         doc = etree.XML(view_arch)
#         payment_method = self.env['statement.payment.method'].search([])
#         buttons = [E.h4(**{'class': 'text-center w-100'})]
#         button_attrs = {
#             'class': 'oe_highlight my-3 mx-1 col',
#             'type': 'object',
#             'name': 'action_add_payment_method_line',
#             'style': 'display:none;'
#         }
#
#         div_attrs = {'class': 'alert alert-info row ml-1'}
#         for payment in payment_method:
#             button_attrs['style'] = ''
#
#             buttons.append(
#                 E.button(
#                     context="{'receivable_account_id': '%s'}" % (payment.receivable_account_id.id),
#                     string=payment.name,
#                     **button_attrs
#                 )
#             )
#         div = E.div(
#             *(buttons),
#             **div_attrs
#         )
#         for node in doc.xpath("//group[@id='group_payment_method_buttons']"):
#             node.append(div)
#         return etree.tostring(doc, encoding='unicode')
#
#     def action_add_payment_method_line(self):
#         self.ensure_one()
#         all_move_vals = []
#         receivable_account_id = self.env.context.get('receivable_account_id')
#         # print(receivable_account_id)
#         if not receivable_account_id or not self.invoice_ids:
#             return True
#
#         # journal = self.env['account.journal'].browse(int(journal_id))
#         domain = [('payment_type', '=', 'outbound')]
#         if self.invoice_ids[0].is_inbound():
#             domain = [('payment_type', '=', 'inbound')]
#         payment_method_id = self.env['account.payment.method'].search(domain, limit=1).id
#
#         self.write({
#             'line_ids': [(0, 0, {
#                 # 'journal_id': 3,
#                 'payment_date': fields.Date.context_today(self),
#                 'invoice_ids': [(6, 0, self.invoice_ids.ids)],
#                 'payment_method_id': payment_method_id,
#                 'amount': self.due_amount,
#                 'currency_id': self.invoice_ids[0].currency_id.id,
#                 'communication': self.invoice_ids[0].ref or self.invoice_ids[0].name,
#             })]
#         })
#
#         transfer_move_vals = {
#             # 'date': payment.payment_date,
#             'ref': self.invoice_ids[0].ref or self.invoice_ids[0].name,
#             'partner_id': self.invoice_ids[0].partner_id.id,
#             'journal_id': self.invoice_ids[0].journal_id.id,
#             'type': 'entry',
#             'line_ids': [
#                 (0, 0, {
#                     'name': self.invoice_ids[0].name,
#                     'amount_currency': 1,
#                     'currency_id': self.invoice_ids[0].currency_id.id,
#                     'debit': self.invoice_ids[0].amount_total > 0.0 and self.invoice_ids[0].amount_total or 0.0,
#                     'credit': self.invoice_ids[0].amount_total < 0.0 and -self.invoice_ids[0].amount_total or 0.0,
#                     # 'date_maturity': payment.payment_date,
#                     'partner_id': self.invoice_ids[0].partner_id.id,
#                     'account_id': receivable_account_id,
#                     # 'payment_id': payment.id,
#                 }),
#                 (0, 0, {
#                     'name': self.invoice_ids[0].name,
#                     'amount_currency': 1,
#                     'currency_id': self.invoice_ids[0].currency_id.id,
#                     'debit': self.invoice_ids[0].amount_total < 0.0 and -self.invoice_ids[0].amount_total or 0.0,
#                     'credit': self.invoice_ids[0].amount_total > 0.0 and self.invoice_ids[0].amount_total or 0.0,
#                     # 'date_maturity': payment.payment_date,
#                     'partner_id': self.invoice_ids[0].partner_id.id,
#                     'account_id': self.invoice_ids[0].partner_id.property_account_receivable_id.id,
#                     # 'payment_id': payment.id,
#                 }),
#             ],
#         }
#         # all_move_vals.append(transfer_move_vals)
#         # move = self.env['account.move'].create(transfer_move_vals)
#         # print(move)
#
#         return {
#             'context': self.env.context,
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': self._name,
#             'res_id': self.id,
#             'view_id': False,
#             'type': 'ir.actions.act_window',
#             'target': 'new',
#         }
