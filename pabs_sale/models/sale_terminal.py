# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleTerminal(models.Model):
    _name = 'sale.terminal'
    _description = "Sale Terminal Configuration"


    name = fields.Char(string='Sale Terminal', index=True, required=True, copy=False,
                        help="An internal identification of the sale terminal.")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', compute='_compute_currency', string="Currency")
    session_ids = fields.One2many('account.user.statement', 'terminal_id', string='Sessions')
    current_session_id = fields.Many2one('account.user.statement', compute='_compute_current_session', string="Current Session")
    current_session_state = fields.Char(string="Current Session State", compute='_compute_current_session')
    last_session_closing_date = fields.Date(string="Last Session Closing Date")
    sale_session_username = fields.Char(compute='_compute_current_session_user')
    sale_session_state = fields.Char(compute='_compute_current_session_user')
    current_user_id = fields.Many2one(
        'res.users', string='Current Session Responsible', compute='_compute_current_session_user', store=True)
    user_statement_count = fields.Integer('User Statement', compute='_compute_user_statement_count')
    cash_statement_id = fields.Many2one('account.bank.statement', string="Cash Statement")
    current_cash_opening = fields.Float(string="Current Opening")
    master_cashier = fields.Many2one('res.users', string="Master Cashier")

    # def _get_cash_open_statement(self):
    #     has_cash = False
    #     for terminal in self:
    #         for journal in terminal.allowed_payment_method:
    #             if journal.journal_account_id.type == 'cash':
    #                 has_cash = True
    #                 if self.env['account.bank.statement'].search(
    #                         [('date', '=', fields.Date.today()), ('journal_id', '=', journal.journal_account_id.id), ('statement_for_pabs', '=', True)]):
    #                     terminal.cash_statement_id = self.env['account.bank.statement'].search([('date', '=', fields.Date.today()), ('journal_id', '=', journal.journal_account_id.id), ('statement_for_pabs','=', True)], limit=1).id
    #                 else:
    #                     terminal.cash_statement_id = False
    #         if not has_cash:
    #             terminal.cash_statement_id = False
    #



    def set_opining(self):
        self.ensure_one()
        has_cash = False
        if not self.allowed_payment_method:
            raise UserError(_('No Payment Method in terminal Configuration'))
        for journal in self.allowed_payment_method:
            if journal.journal_account_id.type == 'cash':
                has_cash = True
                return {
                    'name': _('Opining'),
                    'res_model': 'account.bank.statement',
                    'view_mode': 'form',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context': {
                        'default_name': '%s/%s' % (journal.journal_account_id.name, str(fields.Date.today())),
                        'default_journal_type': 'cash',
                        'default_journal_id': journal.journal_account_id.id,
                        'default_date': fields.Date.today(),
                        'default_statement_for_pabs': True,
                        'default_balance_start': 700,
                    }
                }
        if not has_cash:
            raise UserError(_('Add Payment Method has type (Cash) in terminal Configuration'))
                # if not self.env['account.bank.statement'].search(
                #         [('date', '=', fields.Date.today()), ('journal_id', '=', journal.journal_account_id.id)]):
                #     val = {
                #         # 'name': '%s/%s' %(self.name, user_statement.name),
                #         'name': '%s/%s' % (journal.journal_account_id.name, str(fields.Date.today())),
                #         'journal_type': 'cash',
                #         'journal_id': journal.journal_account_id.id,
                #         'date': fields.Date.today(),
                #         'statement_for_pabs': True,
                #         'balance_start': 0.0,
                #     }
                #     self.session_ids[len(self.session_ids) - 1].bank_statement_id = self.env[
                #         'account.bank.statement'].create(val)
                # else:
                #     jou = self.env['account.bank.statement'].search(
                #         [('date', '=', fields.Date.today()), ('journal_id', '=', journal.journal_account_id.id)])
                #     self.session_ids[len(self.session_ids) - 1].bank_statement_id = jou.id



    def open_session_cb(self):
        """ new session button
        create new account.user.statement if an open one not found
        """
        self.ensure_one()
        user_statement = self.env['account.user.statement'].search(
            [('user_id', '=', self.env.uid), ('state', '=', 'open')], limit=1)

        cashbox_id = self.env['account.bank.statement.cashbox'].search([('start_bank_stmt_ids', '=', self.cash_statement_id.id)], limit=1)
        cashbox_line = self.env['account.cashbox.line'].search([('x_user_id', '=', self.env.uid), ('cashbox_id', 'in', cashbox_id.ids)], limit=1)

        if user_statement and not self.current_session_id:
            raise UserError(_("You cannot create two active sessions with the same responsible."))

        if not self.cash_statement_id.date or not self.will_session_start_username or not cashbox_line:
            if not self._context.get('is_receivable'):
                raise UserError(_("Please Collect The Opening Cash From Master Cashier"))

        if not self._context.get('is_receivable'):
            if self.cash_statement_id.date.strftime('%Y-%m-%d') != datetime.today().strftime('%Y-%m-%d'):
                raise UserError(_("Your cash statement is not valid: Statement Date: %s" %(self.cash_statement_id.date)))

        if cashbox_line.x_terminal_id.id != self.id:
            if not self._context.get('is_receivable'):
                raise UserError(_("You have been assigned to ( %s )") % cashbox_line.x_terminal_id.name)

        if self._context.get('is_receivable'):
            journal = self.allowed_payment_method.filtered(lambda x: x.journal_account_id.type == 'cash')
            print(journal.journal_account_id.name)
            bank_statement = self.env['account.bank.statement'].search(
                [('date', '=', fields.Date.today()), ('journal_id', '=', journal.journal_account_id.id)])
            if bank_statement:
                self.cash_statement_id = bank_statement.id
            else:
                raise UserError(
                    _("Your cash statement is not valid or no cash statement is open"))


        return self._opening_cash() #self._open_session(user_statement.id)

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


    def close_session(self):
        user_statement = self.env['account.user.statement'].search(
            [('user_id', '=', self.env.uid), ('state', '=', 'open')], limit=1)
        user_statement.stop_at = fields.Datetime.now()
        self.last_session_closing_date = fields.Datetime.now()
        user_statement.action_to_validate()
        user_statement.action_confirm()

    def open_existing_session_cb(self):
        """ view session button
        will redirect to current open account.user.statement
        """
        self.ensure_one()
        return self._open_session(self.current_session_id.id)

    def _open_session(self, user_statement_id):
        return {
            'name': _('Account User Statement'),
            'view_mode': 'form,tree',
            'res_model': 'account.user.statement',
            'res_id': user_statement_id,
            'view_id': False,
            'type': 'ir.actions.act_window',
        }

    def _opening_cash(self):
        return {
            'name': _('Cash Opening'),
            'res_model': 'sale.statement.cashbox',
            'view_mode': 'form',
            # 'views': [
            #     (self.env.ref('pabs_sale_extra.sale_statement_cashbox_view_form').id, 'form'),
            # ],
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            #'context': {'default_session_id': user_statement_id.id, 'default_cashbox_lines_ids': user_statement_id.open_cash_ids.ids},
            'context': {'default_current_session_id': self.current_session_id.id, 'default_terminal_id': self.id, 'default_total_openings': self.current_cash_opening},
        }

    @api.depends('company_id', 'company_id.currency_id')
    def _compute_currency(self):
        for sale_terminal in self:
            sale_terminal.currency_id = sale_terminal.company_id.currency_id.id


    def _compute_current_session(self):
        """If there is an open session, store it to current_session_id / current_session_State.
        """
        for sale_terminal in self:
            session = sale_terminal.session_ids.filtered(lambda s: s.user_id.id == self.env.uid and
                                                      s.state == 'open')
            # sessions ordered by id desc
            sale_terminal.current_session_id = session and session[0].id or False
            sale_terminal.current_session_state = session and session[0].state or False

    @api.depends('session_ids')
    def _compute_current_session_user(self):
        for sale_terminal in self:
            session = sale_terminal.session_ids.filtered(lambda s: s.state == 'open')
            if session:
                sale_terminal.sale_session_username = session[0].user_id.name
                sale_terminal.sale_session_state = session[0].state
                sale_terminal.current_user_id = session[0].user_id
            else:
                sale_terminal.sale_session_username = False
                sale_terminal.sale_session_state = False
                sale_terminal.current_user_id = False


    def action_view_all_realted_opened_session(self):
        self.ensure_one()
        return {
                'name': _('Sessions'),
                'res_model': 'account.user.statement',
                'view_mode': 'tree,form',
                'views': [
                    (self.env.ref('pabs_sale.account_user_statement_tree').id, 'tree'),
                    (self.env.ref('pabs_sale.account_user_statement_view_form').id, 'form'),
                ],
                'type': 'ir.actions.act_window',
                'domain': [('terminal_id', '=', self.id)],
        }

    def _compute_user_statement_count(self):
        for statement in self:
            statement.user_statement_count = self.env['account.user.statement'].search_count(
                [('terminal_id', '=', statement.id)])


class AccountBankStmtCashWizard(models.Model):
    _inherit = 'account.bank.statement.cashbox'

    x_is_False = fields.Char(string="is Fasle")
    x_previuos_opeining = fields.Monetary(string='Remaining', compute="compute_remaining_get")
    x_saved_opeining = fields.Monetary(string='Starting Balance')
    x_user_domain = fields.Many2many('res.users', compute="exist_user_id")

    @api.onchange('cashbox_lines_ids')
    def onchange_line_ids(self):
        self.exist_user_id()
        for line in self:
            line.x_previuos_opeining = line.x_saved_opeining - sum(line.cashbox_lines_ids.mapped('subtotal'))

    def exist_user_id(self):
        self.x_user_domain = None
        for line in self.cashbox_lines_ids:
            if line.x_user_id:
                self.x_user_domain = [(4, line.x_user_id.id)]

    @api.depends('total', 'cashbox_lines_ids')
    def compute_remaining_get(self):
        for cashbox in self:
            cashbox.x_previuos_opeining = cashbox.x_saved_opeining - cashbox.total




    def _validate_cashbox(self):
        #res = super(AccountBankStmtCashWizard, self)._validate_cashbox()
        active_id = self.env.context.get('params')
        # if active_id:
        #     if 'id' in active_id:
        #        cashbox_start = self.env['account.bank.statement'].search([('id', '=', active_id['id'])], limit=1).cashbox_start_id
        if self.total > self.x_saved_opeining and self._context.get('balance') == 'start':
            raise UserError(_("The total should not exceed the starting balance"))
        if self.start_bank_stmt_ids and self.start_bank_stmt_ids[0].balance_start == 0.0:
            self.start_bank_stmt_ids.write({'balance_start': self.total})
        if self.end_bank_stmt_ids and self.end_bank_stmt_ids[0].journal_id.type != 'cash':
            self.end_bank_stmt_ids.write({'balance_end_real': self.total})
        if self._context.get('balance') == 'start':
            # if  self.start_bank_stmt_ids and self.start_bank_stmt_ids[0].x_deposit_count != 0:
            #     raise UserError(_("Cannot assign cash opening since the cash is deposited"))
            for line in self.cashbox_lines_ids:
                line.x_terminal_id.current_cash_opening = line.subtotal
                line.x_terminal_id.cash_statement_id = self._context.get('statement_id')
                line.x_terminal_id.will_session_start_username = line.x_user_id.name
                line.x_terminal_id.master_cashier = line.x_master_cashier.id
        # if self._context.get('balance') == 'close':
        #     for line in self.cashbox_lines_ids:
        #         line.x_terminal_id.current_cash_opening = 0.0
        #         line.x_terminal_id.will_session_start_username = False
                # here you need to remove the delete line of opening balance
                # if active_id and cashbox_start:
                #         user_opening = self.env['account.cashbox.line'].search(
                #             [('cashbox_id', '=', cashbox_start.id), ('x_user_id', '=', line.x_user_id.id)])
                #         user_opening.write({'x_user_id': False, 'number': 0, 'coin_value': 0.0})

        #return res

    # def _validate_cashbox(self):
    #     for cashbox in self:
    #         if self.start_bank_stmt_ids:
    #             self.start_bank_stmt_ids.write({'balance_start': self.total})
    #         if self.end_bank_stmt_ids:
    #             self.end_bank_stmt_ids.write({'balance_end_real': self.total})




