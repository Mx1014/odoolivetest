# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from lxml import etree
from lxml.builder import E

from odoo import api, fields, models, _
from odoo.addons.account.models.account_payment import MAP_INVOICE_TYPE_PARTNER_TYPE
from odoo.exceptions import Warning, UserError
import re


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_register_payment_custom(self):
        context = dict(self._context or {})
        context.update(active_ids=self.ids, active_model='account.move', active_id=self.id)
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register.custom',
            'view_mode': 'form',
            'view_id': self.env.ref('pabs_sale.view_account_payment_register_custom_form').id,
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_register_batch_payment_custom(self):
        context = dict(self._context or {})
        active_ids = self._context.get('active_ids')
        if active_ids:
            inv = self.search([('id', 'in', active_ids)])
            if any(invoice.type not in ['out_invoice', 'out_refund'] for invoice in inv):
                raise UserError(_('You can register payment for invoices and credit note only'))
            if any(invoice.state != 'posted' or invoice.invoice_payment_state in ['paid', 'in_payment'] for invoice in
                   inv):
                raise UserError(_('Please select invoices having state "Posted or not paid"'))
            if len(set(inv.mapped('partner_id'))) != 1:
                raise UserError(_("Please select invoices having the same customer!"))
        context.update(active_ids=active_ids, active_model='account.move', active_id=self.id)
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register.custom',
            'view_mode': 'form',
            'view_id': self.env.ref('pabs_sale.view_account_payment_register_custom_form').id,
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    cheque_date = fields.Date(string='Cheque Date', states={'draft': [('readonly', False)]}, tracking=1)
    cheque_number = fields.Char(string='Cheque Number', states={'draft': [('readonly', False)]}, tracking=1)
    bank_id = fields.Many2one('res.bank', string='Bank Account', states={'draft': [('readonly', False)]}, tracking=1)
    account_number = fields.Char(string='Bank Account Number', states={'draft': [('readonly', False)]}, tracking=1)
    x_payment_methods = fields.Many2one("statement.payment.methods", string="Payment Method")
    x_benefit_ref = fields.Char(string="BenefitPay Ref")
    x_cheque_type = fields.Selection([('pdc', 'PDC'), ('cdc', 'CDC')], string="Cheque Type",
                                     states={'draft': [('readonly', False)]}, compute="get_posted_date_check")
    x_cheque_related_type = fields.Selection([('pdc', 'PDC'), ('cdc', 'CDC')], string="Cheque Type",
                                     states={'draft': [('readonly', False)]})
    x_payment_method_name = fields.Char(related="payment_method_id.name")
    x_bank_voucher_statement_id = fields.Many2one('account.bank.statement', string="Bank Statement")
    x_is_check_return = fields.Boolean(string="Is cheque return", default=False, copy=False)

    def get_posted_date_check(self):
        for cheque in self:
            if cheque.x_bank_type == 'cheque' and cheque.cheque_date:
                date_different = cheque.cheque_date - fields.Date.today()
                if date_different.days <= 3:
                    cheque.x_cheque_type = 'cdc'
                    cheque.x_cheque_related_type = 'cdc'
                else:
                    cheque.x_cheque_type = 'pdc'
                    cheque.x_cheque_related_type = 'pdc'
            else:
                cheque.x_cheque_type = False

    @api.onchange('amount', 'currency_id', 'payment_type')
    def domain_journal(self):
        res = {}
        jour = []
        if self._context.get('active_model') == 'account.move':
            if not self.id:
                i = 0
                if i != 0:
                    self.journal_id = False
                    i = 1
            res['domain'] = {'journal_id': [
                ('id', '=', self.env['account.journal'].search([('x_bill_journal', '!=', False)]).ids)]}

        if self._context.get('active_model') == 'account.user.statement' and self.x_session_id:
            # if not self.id:
            #     self.journal_id = self.statement_id.voucher_journal.id
            for journals in self.statement_id.terminal_id.allowed_payment_method.search([]):
                jour.append(journals.journal_account_id.id)
            res['domain'] = {'journal_id': [('id', 'in', jour)]}

        elif self._context.get('active_model') == 'account.user.statement' and not self.x_session_id:

            # if not self.id:
            #     self.journal_id = self.statement_id.voucher_journal.id
            for journals in self.statement_id.terminal_id.allowed_payment_method.search(
                    [('journal_type', '=', 'cash')]):
                jour.append(journals.journal_account_id.id)
            res['domain'] = {'journal_id': [('id', 'in', jour)]}

        return res

    def action_register_payment(self):
        res = super(AccountPayment, self).action_register_payment()
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            inv = self.env['account.move'].search([('id', 'in', active_ids)])
            if any(invoice.type not in ['in_invoice', 'in_refund'] for invoice in inv):
                raise UserError(_('You can register payment for Bills and Refunds only'))
        return res

    def action_return_cheque(self):
        statement_line_vals = []
        for payment in self:
            statement = payment.batch_payment_id.x_bank_statement_id.line_ids.search([('x_batch_line_id', '=', payment.id)])
            print(statement, 'statement')
            if statement:
                statement.button_cancel_reconciliation()
                statement.unlink()
                self.search([('x_batch_line_id', '=', payment.id)], limit=1).cancel()
            payment.batch_payment_id = False
            user_statement_id = False
            terminal = False
            sessions = self.env['account.user.statement'].search(
                [('user_id', '=', self.env.user.id), ('state', '=', 'open'), ('date', '=', fields.Date.today())])

            team = self.env['crm.team'].search(
                [('member_ids', 'in', self.env.user.id)]).id
            if team:
                terminal = self.env['sale.terminal'].search([('allowed_team', '=', team)])
            if terminal:
                user_statement_id = sessions

            if not user_statement_id and terminal:
                raise UserError(
                    _("Please start a Session via Sale Terminal as you can't create payment without a session opened."))

            if user_statement_id:
                value = self.env['account.user.statement.line'].search([('payment_id', '=', payment.id)])
                value.payment_id = False
                statement_line_vals.append((0, 0, self._create_statement_line_values_for_return_check()))
                user_statement_id.write({'user_statement_line_ids': statement_line_vals})

                #if check or card or benefit
                split_string = re.split(',|:|', payment.communication) #payment.communication.split(",", 1)
                if payment.cheque_number:
                    payment.communication = split_string[0] + ', ' + user_statement_id.name + ', ' + payment.cheque_number
                elif payment.x_auth:
                   payment.communication = split_string[0] + ', ' + user_statement_id.name + ', ' + payment.x_auth
                elif payment.x_benefit_ref:
                    payment.communication = split_string[0] + ', ' + user_statement_id.name + ', ' + payment.x_benefit_ref
                #invoices = payment.move_line_ids
                payment.move_line_ids.remove_move_reconcile()
                payment.action_draft()
                #payment.move_line_ids = invoices
                payment.post()
                payment.message_post(
                    body='The Cheque Was Replaced', subject="SMS Sent",
                    message_type="comment")

            # send_money = self.copy({'payment_type': 'outbound'})
            # send_money.post()
            # payment.move_line_ids.remove_move_reconcile()
            # payment.x_is_check_return = True

    def _create_statement_line_values_for_return_check(self):
        values = {
            'name': self.communication,
            'statement_id': self.env['account.user.statement'].search(
                [('user_id', '=', self.env.user.id), ('state', '=', 'open')]).id,
            'journal_id': self.journal_id.id,
            'date': self.payment_date,
            # 'user_id': self.env.user.id,
            'amount': self.amount,
            'partner_id': self.partner_id.id,
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
            # 'statement_user_id': self.env['account.user.statement'].search([('user_id', '=', self.env.user.id), ('state', '=', 'open')]).id
        }
        # print(vals['invoice_ids'][0])
        if self.payment_type == 'outbound':
            self.amount = -self.amount
        return values

    def action_update_check(self):
        return {
            'name': _('Replace Cheque'),
            'res_model': 'update.cheque',
            'view_mode': 'form',
            'views': [
                (self.env.ref('pabs_sale.update_cheque_form_view').id, 'form'),
            ],
            'target': 'new',
            'context': {'default_name': self.id},
            'type': 'ir.actions.act_window',
        }


class UpdateCheck(models.TransientModel):
    _name = 'update.cheque'
    _description = 'Update Cheque'

    def domain_on_session_open(self):
        #print(self.env['sale.terminal'].search([('id', '=', default.id)]).allowed_payment_method, 'ddddddd')
        default = self.env['account.user.statement'].search(
            [('user_id', '=', self.env.user.id), ('state', '=', 'open'),
             ('date', '=', fields.Date.today())]).terminal_id
        if default:
        # payment = self.env['sale.terminal'].search([('id', '=', default.id)]).allowed_payment_method
           return [('id', 'in', default.allowed_payment_method.ids)]
        else:
            return [('id', 'in', [])]

    name = fields.Many2one('account.payment', string="Payment")
    journal_id = fields.Many2one('account.journal', related="payment_method.journal_account_id", string="journal")
    bank_id = fields.Many2one('res.bank', string="Bank Account")
    cheque_date = fields.Date(string='Cheque Date')
    cheque_number = fields.Char(string='Cheque Number')
    account_number = fields.Char(string='Bank Account Number')
    cheque_type = fields.Selection([('pdc', 'PDC'), ('cdc', 'CDC')], string="Cheque Type")
    auth = fields.Char(string="Auth Code")
    tid = fields.Many2one('bank.card.readers', string="TID")
    batch = fields.Char(string="Batch")
    benefit_ref = fields.Char(string="BenefitPay Ref")
    bank_type = fields.Selection(related="journal_id.x_bank_type")
    journal_type = fields.Selection(related="journal_id.type")
    payment_method = fields.Many2one('statement.payment.methods', string="Payment Method", domain=domain_on_session_open)

    def update_check(self):
        for vals in self:
            vals.name.update({
                'journal_id': self.journal_id.id,
                'bank_id': self.bank_id.id,
                'cheque_date': self.cheque_date,
                'cheque_number': self.cheque_number,
                'account_number': self.account_number,
                #'x_cheque_type': self.cheque_type,
                'x_auth': self.auth,
                'x_tid': self.tid.id,
                'x_batch': self.batch,
                'x_benefit_ref': self.benefit_ref,

            })
            vals.name.action_return_cheque()

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    user_allowed = fields.Many2many('res.users', string='Allowed Users')
    x_bank_type = fields.Selection([('cheque', 'Cheque'), ('card', 'Credit Card'), ('online', 'BenefitPay')],
                                   string="Bank Type")

    def view_action_batch_payment(self):
        self.ensure_one()
        return {
            'name': _('Batch Deposit'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.batch.payment',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account_batch_payment.view_batch_payment_tree').id, 'tree'),
                (self.env.ref('account_batch_payment.view_batch_payment_form').id, 'form'),
            ],
            'context': {'default_journal_id': self.id, 'default_batch_type': 'inbound',
                        'default_payment_method_id': self.env.ref('account.account_payment_method_manual_in').id},
            'domain': [('journal_id', '=', self.id)],
        }

    def open_action_batch_payment(self):
        ctx = self._context.copy()
        ctx.update({'journal_id': self.id, 'default_journal_id': self.id,
                    'default_payment_method_id': self.env.ref('account.account_payment_method_manual_in').id})
        return {
            'name': _('Create Batch Payment'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.batch.payment',
            'context': ctx,
        }


class AccountPaymentRegisterCustom(models.TransientModel):
    _name = 'account.payment.register.custom'
    _description = "Payment register custom wizard"

    line_ids = fields.One2many('account.payment.register.line', 'payment_resgiter_id', string="Payments Line")
    amount = fields.Monetary(string='Amount', required=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
                                  default=lambda self: self.env.company.currency_id)
    due_amount = fields.Monetary(compute='_compute_due_amount', string='Due Amount')
    change = fields.Monetary(compute='_compute_change', string='Change')
    invoice_ids = fields.Many2many('account.move', 'account_invoice_payment_register_custom_rel_transient',
                                   'payment_id', 'invoice_id', string="Invoices")
    payment_difference = fields.Monetary(compute='_compute_payment_difference', readonly=True)
    payment_difference_handling = fields.Selection([('open', 'Keep open')],
                                                   default='open', string="Payment Difference Handling", copy=False)
    writeoff_account_id = fields.Many2one('account.account', string="Difference Account",
                                          domain="[('deprecated', '=', False)]", copy=False)
    writeoff_label = fields.Char(
        string='Journal Item Label',
        help='Change label of the counterpart that will hold the payment difference',
        default='Write-Off')

    @api.depends('invoice_ids', 'amount', 'currency_id', 'line_ids')
    def _compute_payment_difference(self):
        draft_payments = self.filtered(lambda p: p.invoice_ids)
        for pay in draft_payments:
            payment_amount = pay.amount
            pay.payment_difference = sum(line.amount for line in pay.line_ids) - payment_amount
        (self - draft_payments).payment_difference = 0

    @api.depends('line_ids')
    def _compute_change(self):
        for payment in self:
            paid_amount = sum(self.line_ids.mapped('amount'))
            payment.change = paid_amount - payment.amount if paid_amount - payment.amount > 0 else 0

    @api.depends('line_ids')
    def _compute_due_amount(self):
        for payment in self:
            payment.due_amount = payment.amount - sum(line.amount for line in payment.line_ids)

    @api.model
    def default_get(self, default_fields):
        rec = super(AccountPaymentRegisterCustom, self).default_get(default_fields)
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        active_model = self._context.get('active_model')
        # Check for selected invoices ids
        if not active_ids or active_model != 'account.move':
            return rec
        invoices = self.env['account.move'].browse(active_ids).filtered(
            lambda move: move.is_invoice(include_receipts=True))
        amount = self.env['account.payment']._compute_payment_amount(invoices, invoices[0].currency_id,
                                                                     invoices[0].journal_id, fields.Date.today())

        rec.update({
            'amount': amount,
            'invoice_ids': [(6, 0, invoices.ids)],
        })
        return rec

    # def create_payments(self):
    #     payment_vals = []
    #     statement_line_vals = []
    #     vals = {}
    #     user_statement_id = False
    #     terminal = False
    #
    #     team = self.env['crm.team'].search(
    #         [('member_ids', 'in', self.env.user.id)]).id
    #     if team:
    #         terminal = self.env['sale.terminal'].search([('allowed_team', '=', team)])
    #         if terminal:
    #              user_statement_id = self.env['account.user.statement'].search([('user_id', '=', self.env.user.id), ('state', '=', 'open')]).id
    #
    #     if not user_statement_id and terminal:
    #         raise UserError(
    #             _("Please start a Session via Sale Terminal as you can't create payment without a session opened."))
    #
    #     active_ids = self._context.get('active_ids') or self._context.get('active_id')
    #     for line in self.line_ids: #.filtered(lambda l: l.amount != 0):
    #         vals = line._prepare_payment_vals()
    #         statement_line_vals.append((0, 0, self._create_statement_line_values(vals)))
    #         if self.change and line.journal_id.type == 'cash':
    #             vals['amount'] -= self.change
    #         payment_vals.append(vals)
    #
    #     if self.change:
    #         change_line = self._create_statement_line_values(vals)
    #         change_line['amount'] = -(self.change)
    #         statement_line_vals.append((0, 0, change_line))
    #
    #
    #     #self.env['account.bank.statement.line'].create(statement_line_vals)
    #     invoices = self.env['account.move'].browse(active_ids)
    #     statement_id = self.env['account.user.statement'].search([('user_id', '=', self.env.user.id), ('state', '=', 'open')])
    #     if invoices.type in ['out_invoice', 'out_refund']:
    #         statement_id.write({'user_statement_line_ids': statement_line_vals})
    #     payments = self.env['account.payment'].create(payment_vals)
    #     payments.post()
    #     return {'type': 'ir.actions.act_window_close'}

    def action_view_invoice_after_payment(self, id):
        self.ensure_one()
        return {
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'views': [
                (self.env.ref('account.view_move_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'res_id': id,
        }

    def cancel_payments(self):
        return self.action_view_invoice_after_payment(self._context.get('active_id'))

    def create_payments(self):
        payment_vals = []
        statement_line_vals = []
        vals = {}
        user_statement_id = False
        terminal = False
        sessions = self.env['account.user.statement'].search(
            [('user_id', '=', self.env.user.id), ('state', '=', 'open'), ('date', '=', fields.Date.today())])

        team = self.env['crm.team'].search(
            [('member_ids', 'in', self.env.user.id)]).id
        if team:
            terminal = self.env['sale.terminal'].search([('allowed_team', '=', team)])
        if terminal:
            user_statement_id = sessions

        if not user_statement_id and terminal:
            raise UserError(
                _("Please start a Session via Sale Terminal as you can't create payment without a session opened."))

        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        for line in self.line_ids:  # .filtered(lambda l: l.amount != 0):
            if line.bank_type == 'card':
                if not line.tid or not line.batch or not line.auth:
                    raise UserError(_("You have required Fields."))
            elif line.bank_type == 'cheque':
                if not line.cheque_date or not line.cheque_number or not line.bank_id or not line.account_number:
                    raise UserError(_("You have required Fields."))

            vals = line._prepare_payment_vals()
            if vals['amount'] == 0.0:
                raise UserError(_("Amount cannot be 0"))
            if self.change and line.journal_id.type == 'cash':
                vals['amount'] -= self.change
            # payment_vals.append(vals)
            payments = self.env['account.payment'].create([vals])
            payments.post()
            vals['id'] = payments.id
            statement_line_vals.append((0, 0, self._create_statement_line_values(vals)))

        # if self.change:
        #     change_line = self._create_statement_line_values(vals)
        #     change_line['amount'] = -(self.change)
        #     statement_line_vals.append((0, 0, change_line))

        # self.env['account.bank.statement.line'].create(statement_line_vals)
        # invoices = self.env['account.move'].browse(active_ids)
        invoices = self.env['account.move'].search([('id', 'in', active_ids)])
        # statement_id = self.env['account.user.statement'].search(
        #     [('user_id', '=', self.env.user.id), ('state', '=', 'open')])
        # if statement_id:
        #     #if invoices.type in ['out_invoice', 'out_refund']:
        #         statement_id.write({'user_statement_line_ids': statement_line_vals})

        # payments = self.env['account.payment'].create(payment_vals)
        print(sessions)
        if sessions:
            # if invoices.type in ['out_invoice', 'out_refund']:
            # for pay in statement_line_vals:
            #     for dic in pay:
            #         if isinstance(dic, dict):
            #             dic['payment_id'] = payments.id
            # ref_payment['payment_id'] = payments.id
            # statement_line_vals.append((0, 0, ref_payment))
            sessions.write({'user_statement_line_ids': statement_line_vals})
        # payments.post()
        return self.action_view_invoice_after_payment(self._context.get('active_id'))
        #return {'type': 'ir.actions.act_window_close'}

    def _create_statement_line_values(self, vals):
        values = {
            'name': vals['communication'],
            'statement_id': self.env['account.user.statement'].search(
                [('user_id', '=', self.env.user.id), ('state', '=', 'open')]).id,
            'journal_id': vals['journal_id'],
            'date': vals['payment_date'],
            # 'user_id': self.env.user.id,
            'amount': vals['amount'],
            'partner_id': vals['partner_id'],
            'cheque_date': vals['cheque_date'],
            'cheque_number': vals['cheque_number'],
            'bank_id': vals['bank_id'],
            'account_number': vals['account_number'],
            'cheque_type': vals['x_cheque_type'],
            'auth': vals['x_auth'],
            'tid': vals['x_tid'],
            'batch': vals['x_batch'],
            'benefit_ref': vals['x_benefit_ref'],
            'payment_id': vals['id'],
            # 'statement_user_id': self.env['account.user.statement'].search([('user_id', '=', self.env.user.id), ('state', '=', 'open')]).id
        }
        # print(vals['invoice_ids'][0])
        if vals['payment_type'] == 'outbound':
            values['amount'] = -vals['amount']
        return values

    @api.model
    def fields_view_get(self, view_id=None, view_type='tree,form', toolbar=False, submenu=False):
        result = super(AccountPaymentRegisterCustom, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                                           toolbar=toolbar, submenu=submenu)
        result['arch'] = self._apply_journal_buttons(result['arch'])
        return result

    @api.model
    def _apply_journal_buttons(self, view_arch):
        doc = etree.XML(view_arch)
        # sales_team = self.env['crm.team'].search([('member_ids', 'in', self.env.user.id)])
        # journals = self.env['account.journal'].search([('type', 'in', ('bank', 'cash')), ('x_allowed_sale_team','=', sales_team.id)]) #filter for the cuurent allowed sales team
        doc_type = self.env['account.move'].search([('id', '=', self.env.context.get('active_id'))])
        user_statement_id = self.env['account.user.statement'].search(
            [('user_id', '=', self.env.user.id), ('state', '=', 'open')]).id
        journals = self.env['sale.terminal'].search([('current_user_id', '=', self.env.user.id)])
        buttons = [E.h4('Payment Methods', **{'class': 'text-center w-100'})]
        button_attrs = {
            'class': 'oe_highlight my-3 mx-1 col',
            'type': 'object',
            'name': 'action_add_payment_line',
            'style': 'display:none;'
        }

        div_attrs = {'class': 'alert alert-info row ml-1'}
        # if doc_type.type in ['out_invoice', 'out_refund'] and user_statement_id:
        if user_statement_id:
            # for journal in journals.allowed_journal:
            for journal in journals.allowed_payment_method:
                button_attrs['style'] = ''

                buttons.append(
                    E.button(
                        context="{'journal_id': '%s', 'payment_methods': '%s'}" % (
                            journal.journal_account_id.id, journal.id),
                        string=journal.name,
                        **button_attrs
                    )
                )
        else:
            # journals = self.env['account.journal'].search([('type', 'in', ('bank', 'cash'))])
            journals = self.env['statement.payment.methods'].search([])
            for journal in journals:
                if journal.journal_account_id.type != 'cash':
                    button_attrs['style'] = ''

                    buttons.append(
                        E.button(
                            context="{'journal_id': '%s','payment_methods': '%s'}" % (
                                journal.journal_account_id.id, journal.id),
                            string=journal.name,
                            **button_attrs
                        )
                    )

        div = E.div(
            *(buttons),
            **div_attrs
        )
        for node in doc.xpath("//group[@id='group_journal_buttons']"):
            node.append(div)
        return etree.tostring(doc, encoding='unicode')

    def action_add_payment_line(self):
        self.ensure_one()
        journal_id = self.env.context.get('journal_id')
        payment_methods = self.env.context.get('payment_methods')
        if not journal_id or not self.invoice_ids:
            return True

        journal = self.env['account.journal'].browse(int(journal_id))
        domain = [('payment_type', '=', 'outbound')]
        if self.invoice_ids[0].is_inbound():
            domain = [('payment_type', '=', 'inbound')]
        payment_method_id = self.env['account.payment.method'].search(domain, limit=1).id
        payment_method = self.env['statement.payment.methods'].browse(int(payment_methods))

        user_statement_id = self.env['account.user.statement'].search(
            [('user_id', '=', self.env.user.id), ('state', '=', 'open')], limit=1).terminal_id
        tid = self.env['bank.card.reader.line'].search(
            [('terminal_id', '=', user_statement_id.id), ('payment_methods', '=', payment_method.id)])
        print(tid.tid_ids.ids)

        self.write({
            'line_ids': [(0, 0, {
                'journal_id': journal.id,
                'team_id': self.env['crm.team'].search([('member_ids', '=', self.env.user.id)]).id,
                'payment_date': fields.Date.context_today(self),
                'invoice_ids': [(6, 0, self.invoice_ids.ids)],
                'payment_method_id': payment_method_id,
                #'amount': self.due_amount,
                'currency_id': journal.currency_id.id or self.invoice_ids[0].currency_id.id,
                'communication': self.invoice_ids[0].ref or self.invoice_ids[0].name,
                'bank_type': journal.x_bank_type,
                'payment_methods': payment_method.id,
                'domain_tid': [(6, 0, tid.tid_ids.ids)],
            })]
        })

        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    statement_user_id = fields.Many2one('account.user.statement')
    user_statement_name = fields.Char(relared="statement_user_id.name", string="User Statement Name")
    x_batch_line_id = fields.Many2one('account.payment', string="Batch Payment", copy=False)
    x_batch_line_transfer_id = fields.Many2one('account.payment', string="Transfer Payment", copy=False)



class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    statement_for_pabs = fields.Boolean(string="Use for Pabs", default=False)
    x_amount_to_deposit = fields.Monetary(string="Amount to be Deposited", compute="compute_deposit_get", store=True)
    x_deposit_count = fields.Integer(compute="_get_deposit_count")
    x_voucher_count = fields.Integer(string="Voucher", compute="_compute_voucher_count")

    def _set_opening_balance(self, journal_id):
        res = super(AccountBankStatement, self)._set_opening_balance(journal_id)
        if self.env['account.journal'].search([('id', '=', journal_id)], limit=1).type == 'cash':
            self.balance_end_real = self._get_opening_balance(journal_id)
        return res

    @api.depends('line_ids')
    def _get_deposit_count(self):
        for statement in self:
            statement.x_deposit_count = self.env['account.payment'].search_count(
                [('x_bank_statement_id', '=', self.id)])


    def _compute_voucher_count(self):
        for statement in self:
            statement.x_voucher_count = self.env['account.payment'].search_count(
                [('x_bank_voucher_statement_id', '=', statement.id)])


    @api.depends('balance_end_real', 'balance_end')
    def compute_deposit_get(self):
        for statement in self:
            statement.x_amount_to_deposit = statement.balance_end - statement.balance_end_real

    def open_cashbox_id(self):
        self.ensure_one()
        context = dict(self.env.context or {})
        list = []
        terminal = self.env['sale.terminal'].search(
            [('allowed_payment_method.journal_account_id', '=', self.journal_id.id),
             ('allowed_payment_method', '!=', False)])

        for term in terminal:
            list.append((0, 0, {
                'number': 1,
                'x_terminal_id': term.id,
            }))

        # self.env['account.bank.statement.cashbox'].with_context(default_x_compatible_closing=False).compatibile_val_get(self.id)

        # context['default_cashbox_lines_ids'] = list)
        if context.get('balance'):
            context['statement_id'] = self.id
            if context['balance'] == 'start':
                cashbox_id = self.cashbox_start_id.id
            elif context['balance'] == 'close':
                cashbox_id = self.cashbox_end_id.id
            else:
                cashbox_id = False

            last_bnk_stmt = self.search([('journal_id', '=', self.journal_id.id)], limit=1)
            if not self.cashbox_start_id.cashbox_lines_ids:
                context['default_cashbox_lines_ids'] = list
                context['default_x_saved_opeining'] = self.balance_start

            if not self.cashbox_end_id.cashbox_lines_ids:
                # context['default_cashbox_lines_ids'] = list
                context['default_x_saved_opeining'] = self.balance_end_real
            if self.cashbox_end_id:
                self.cashbox_end_id.x_saved_opeining = self.balance_end_real  # last_bnk_stmt.balance_end
            if self.cashbox_start_id:
                self.cashbox_start_id.x_saved_opeining = self.balance_start
                for term in terminal:
                    if term.id not in self.cashbox_start_id.mapped('cashbox_lines_ids.x_terminal_id').ids:
                        self.cashbox_start_id.cashbox_lines_ids = [(0, 0, {'number': 1, 'x_terminal_id': term.id, 'coin_value': 0})]
            # context['default_x_saved_opeining'] = last_bnk_stmt.balance_end
            # if not context.get('end_bank_stmt_ids') and context['balance'] == 'close':
            #     context['end_bank_stmt_ids'] = [(6, 0, [self.id])]

            if terminal:
                context['default_x_is_False'] = 'True'

            action = {
                'name': _('Cash Control'),
                'view_mode': 'form',
                'res_model': 'account.bank.statement.cashbox',
                'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox_footer').id,
                'type': 'ir.actions.act_window',
                'res_id': cashbox_id,
                'context': context,
                'target': 'new'
            }

            return action

    @api.model
    def default_get(self, fields):
        vals = super(AccountBankStatement, self).default_get(fields)
        if 'journal_id' in vals and 'date' in vals:
            code = self.env['account.journal'].search([('id', '=', vals['journal_id'])])
            vals['name'] = '%s/%s' % (code.code, vals['date'].strftime("%d-%m-%Y"))
        return vals

    @api.onchange('date', 'journal_id')
    def onchange_to_name(self):
        self.name = '%s/%s' % (self.journal_id.code, self.date.strftime("%d-%m-%Y"))

    def check_all_session_closed(self):
        state = []
        terminal = self.env['account.user.statement'].search([('bank_statement_id', '=', self.id)])
        for session in terminal:
            if session.state == 'confirm':
                state.append(session.state)
        if len(terminal.ids) != len(state):
            raise UserError(_("There are sessions need to be validated. Please validate open sessions"))

    def action_create_cash_deposit(self):
        self.ensure_one()
        payment_methods = self.journal_id.outbound_payment_method_ids
        return {
            'name': _('Cash Deposit'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'views': [
                (self.env.ref('pabs_sale_extra.statement_cash_deposit_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'context': {
                        'default_payment_type': 'transfer',
                        'default_journal_id': self.journal_id.id,
                        'default_communication': self.name, 'default_amount': self.x_amount_to_deposit,
                        'default_x_bank_statement_id': self.id, 'default_x_deposit_amount': self.x_amount_to_deposit,
                        'default_payment_method_id': payment_methods and payment_methods[0].id or False
                       },
            'target': 'new',
        }

    # def action_create_cheque_deposit(self):
    #     self.ensure_one()
    #     self.check_all_session_closed()
    #     return {
    #         'name': _('Cheque Deposit'),
    #         'res_model': 'account.batch.payment',
    #         'view_mode': 'form',
    #         'views': [
    #             (self.env.ref('account_batch_payment.view_batch_payment_form').id, 'form'),
    #         ],
    #         'type': 'ir.actions.act_window',
    #         'context': {'default_x_bank_statement_id': self.id},
    #         'target': 'fullscreen',
    #     }

    def action_view_cash_deposit(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cash Deposit'),
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_account_payment_tree').id, 'tree'),
                (self.env.ref('account.view_account_payment_form').id, 'form'),
            ],

            'domain': [('x_bank_statement_id', '=', self.id)]
        }

    def unlink(self):
        state = []
        terminal_cash = self.env['account.user.statement'].search([('bank_statement_id', '=', self.id)])
        terminal_bank = self.env['account.batch.payment'].search([('x_bank_statement_id', '=', self.id)])
        if terminal_cash or terminal_bank:
            raise UserError(_("Cannot delete the statement!"))
        return super(AccountBankStatement, self).unlink()

    @api.model
    def create(self, vals):
        res = super(AccountBankStatement, self).create(vals)
        if self.search([('journal_id', '=', res.journal_id.id), ('journal_type', '=', 'cash'), ('date', '=', res.date), ('id', '!=', res.id)]):
            raise UserError(_('You have cash statement created for today'))
        return res

    def action_view_create_voucher(self):
        self.ensure_one()
        payment_methods = self.journal_id.outbound_payment_method_ids
        return {
            'name': _('Vouchers'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'views': [
                (self.env.ref('pabs_sale.statement_cash_voucher_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'context': {'default_payment_type': 'transfer',
                        'default_journal_id': self.journal_id.id,
                        'default_destination_journal_id': self.env['ir.default'].sudo().get('account.user.statement',
                                                                                            'x_voucher_journal'),
                        'default_communication': self.name, 'is_voucher': True,
                        'default_payment_method_id': payment_methods and payment_methods[0].id or False, 'default_x_bank_voucher_statement_id': self.id},
            'target': 'new',
        }

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
            'domain': [('x_bank_voucher_statement_id', '=', self.id)],
        }

    def check_confirm_bank(self):
        res = super(AccountBankStatement, self).check_confirm_bank()
        print(self.line_ids, 'ddd')
        if self.line_ids:
            batch = self.line_ids[0].x_batch_line_id.batch_payment_id
            print(batch, 'ddddddd')
            if batch:
                if batch.state == 'sent':
                    batch.state = 'reconciled'
        return res


class AccountUserStatement(models.Model):
    _name = 'account.user.statement'
    _description = "Account user statement"
    _order = 'date desc'

    name = fields.Char(string='Reference', copy=False, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', store=True, readonly=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency")
    date = fields.Date(required=True, readonly=True, index=True, copy=False, default=fields.Date.context_today)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, readonly=True)
    balance_start = fields.Monetary(string='Opening Balance', readonly=True)
    balance_end = fields.Monetary(string='Theoretical Closing Balance', states={
        'confirm': [('readonly', True)]}, compute='_compute_balance_end')
    # bank_statement_line_ids = fields.One2many('account.bank.statement.line', 'statement_user_id')
    state = fields.Selection([('open', 'Running'), ('to_validate', 'To Validate'), ('confirm', 'Validated')],
                             string='Status', required=True, readonly=True, copy=False, default='open')
    terminal_id = fields.Many2one('sale.terminal', string="Terminal")
    start_at = fields.Datetime(string='Opening Date', readonly=True)
    stop_at = fields.Datetime(string='Closing Date', readonly=True, copy=False)
    order_count = fields.Integer('Sale Orders', compute='_compute_order_count')
    quote_count = fields.Integer('Quotation', compute='_compute_qoutation_count')
    invoice_count = fields.Integer('Invoices', compute='_compute_invoice_count')
    credit_note_count = fields.Integer('Credit Note', compute='_compute_credit_note_count')
    bank_statement_id = fields.Many2one('account.bank.statement', string="Cash Statement", readonly=True)
    all_lines_reconciled = fields.Boolean(related="bank_statement_id.all_lines_reconciled")
    invoice_ids = fields.Many2many('account.move', string="Invoices")

    @api.depends('balance_start')
    def _compute_balance_end(self):
        for record in self:
            balance = record.balance_start
            for line in record.user_statement_line_ids:
                if line.journal_id.type == 'cash':
                    balance += line.amount
            record.balance_end = balance

    def _compute_order_count(self):
        for statement in self:
            statement.order_count = self.env['sale.order'].search_count(
                [('state', '=', 'sale'), ('user_statement_id', '=', statement.id)])

    def _compute_qoutation_count(self):
        for statement in self:
            statement.quote_count = self.env['sale.order'].search_count(
                [('state', 'in', ['draft', 'sent']), ('user_statement_id', '=', self.id)])

    def _compute_invoice_count(self):
        for statement in self:
            invoices = self.env['account.move']
            statement.invoice_count = invoices.search_count(
                [('user_statement_id', '=', statement.id), ('type', '=', 'out_invoice')])
            statement.invoice_ids = [(6, 0, invoices.search(
                [('user_statement_id', '=', statement.id), ('type', 'in', ['out_invoice', 'out_refund'])]).ids)]

    def _compute_credit_note_count(self):
        for statement in self:
            statement.credit_note_count = self.env['account.move'].search_count(
                [('user_statement_id', '=', statement.id), ('type', '=', 'out_refund')])

    def action_to_validate(self):
        # if self.end_difference < self.terminal_id.min_threshold:
        #     raise UserError(_("Your Closing difference less than the minimum threshold (%s)") % self.terminal_id.min_threshold)
        list = []
        # self.write({'state': 'to_validate', 'stop_at': fields.Datetime.now()})
        self.write({'state': 'confirm'})
        self.terminal_id.current_cash_opening = 0.0
        self.terminal_id.last_session_closing_date = fields.Datetime.now()
        user_opening = self.env['account.cashbox.line'].search(
            [('cashbox_id', '=', self.bank_statement_id.cashbox_start_id.id), ('x_user_id', '=', self.user_id.id)])
        user_opening.write({'x_user_id': False, 'number': 0, 'coin_value': 0.0})
        # user_closing = self.env['account.cashbox.line'].search(
        #     [('cashbox_id', '=', self.bank_statement_id.cashbox_end_id.id),
        #      ('x_terminal_id', '=', self.terminal_id.id)])
        self.terminal_id.will_session_start_username = False
        self.terminal_id.current_cash_opening = 0.0
        self.terminal_id.master_cashier = False
        # if not user_closing:
        #     print(user_closing)
        #     terminal = self.env['sale.terminal'].search(
        #         [('allowed_payment_method.journal_account_id', '=', self.bank_statement_id.journal_id.id)])
        #     for term in terminal:
        #         list.append((0, 0, {
        #             'coin_value': 0.0,
        #             'x_terminal_id': term.id,
        #         }))
        #     self.bank_statement_id.cashbox_end_id = self.env['account.bank.statement.cashbox'].create({
        #         'x_is_False': 'True',
        #         'cashbox_lines_ids': list,
        #     })
        #     closing = self.env['account.cashbox.line'].search(
        #         [('cashbox_id', '=', self.bank_statement_id.cashbox_end_id.id),
        #          ('x_terminal_id', '=', self.terminal_id.id)])
        #     closing.write({
        #         'coin_value': self.total_closing,
        #         'number': 1,
        #         'x_user_id': self.user_id.id
        #     })
        #     closing.cashbox_id._validate_cashbox()
        #     self.terminal_id.will_session_start_username = False
        # else:
        #     print('expected')
        #     user_closing.write({
        #         'coin_value': self.total_closing,
        #         'number': 1,
        #         'x_user_id': self.user_id.id
        #     })
        #     user_closing.cashbox_id._validate_cashbox()
        #     self.terminal_id.will_session_start_username = False

    def view_journal_statement(self):
        self.ensure_one()
        return {
            'name': _('Statement'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.bank.statement',
            'views': [
                (self.env.ref('account.view_bank_statement_form').id, 'form'),
            ],
            'res_id': self.bank_statement_id.id,
        }

    def action_confirm(self):
        if not self.all_lines_reconciled and len(self.user_statement_line_ids) != 0:
            raise UserError(_("You have unreconciled lines, Please reconcile first"))

        self.write({'state': 'confirm'})

    def action_view_order(self):
        self.ensure_one()
        return {
            'name': _('Orders'),
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('sale.view_order_tree').id, 'tree'),
                (self.env.ref('sale.view_order_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('state', '=', 'sale'), ('user_statement_id', '=', self.id)],
        }

    def action_view_quotation(self):
        self.ensure_one()
        return {
            'name': _('Quotation'),
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('sale.view_order_tree').id, 'tree'),
                (self.env.ref('sale.view_order_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('team_id', '=', self.user_id.sale_team_id)],
        }

    def action_view_invoice(self):
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
            'domain': [('user_statement_id', '=', self.id), ('type', '=', 'out_invoice')],
        }

    def action_view_credit_note(self):
        self.ensure_one()
        return {
            'name': _('Credit Note'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_invoice_tree').id, 'tree'),
                (self.env.ref('account.view_move_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('user_statement_id', '=', self.id), ('type', '=', 'out_refund')],
        }

    def unlink(self):
        # statement = self.mapped('user_statement_line_ids')
        # if statement:
        raise UserError(_('You cannot delete the statement'))
        return super(AccountUserStatement, self).unlink()


class AccountPaymentRegisterLine(models.TransientModel):
    """
        This model will allow to split the payment accross multiple payment method, just like we have in point of sale
    """
    _name = 'account.payment.register.line'
    _description = "Payment register custom wizard line"

    payment_resgiter_id = fields.Many2one('account.payment.register.custom')
    payment_date = fields.Date(
        required=True, default=fields.Date.context_today)
    journal_id = fields.Many2one('account.journal', domain=[
        ('type', 'in', ('bank', 'cash'))], required=True, readonly=True)
    type = fields.Selection(related='journal_id.type')
    bank_type = fields.Char(string="Bank Type")
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method Type', required=True,
                                        help="Manual: Get paid by cash, check or any other method outside of Odoo.\n"
                                             "Electronic: Get paid automatically through a payment acquirer by requesting a transaction on a card saved by the customer when buying or subscribing online (payment token).\n"
                                             "Check: Pay bill by check and print it from Odoo.\n"
                                             "Batch Deposit: Encase several customer checks at once by generating a batch deposit to submit to your bank. When encoding the bank statement in Odoo, you are suggested to reconcile the transaction with the batch deposit.To enable batch deposit, module account_batch_payment must be installed.\n"
                                             "SEPA Credit Transfer: Pay bill from a SEPA Credit Transfer file you submit to your bank. To enable sepa credit transfer, module account_sepa must be installed ")
    amount = fields.Monetary(string='Amount')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, required=True,
                                  default=lambda self: self.env.company.currency_id)
    communication = fields.Char(string='Memo')
    invoice_ids = fields.Many2many('account.move', 'account_invoice_payment_register_rel_transient', 'payment_id',
                                   'invoice_id', string="Invoices")
    cheque_date = fields.Date(string='Cheque Date')
    cheque_number = fields.Char(string='Cheque Number')
    bank_id = fields.Many2one('res.bank', string='Bank Account')
    account_number = fields.Char(string='Bank Account Number')
    cheque_type = fields.Selection([('pdc', 'PDC'), ('cdc', 'CDC')], string="Cheque Type")
    auth = fields.Char(string="Auth Code")
    tid = fields.Many2one('bank.card.readers', string="TID")
    batch = fields.Char(string="Batch")
    team_id = fields.Many2one('crm.team', string="Team")
    payment_methods = fields.Many2one("statement.payment.methods",
                                      string="Payment Method")  # ,domain="[('bank_type', '=', 'card')]"
    domain_tid = fields.Many2many('bank.card.readers', string="TID domain")
    benefit_ref = fields.Char(string="BenefitPay Ref")

    _sql_constraints = [
        ('unique_benefit', 'UNIQUE(benefit_ref)', 'BenefitPay reference cannot be duplicated'),
    ]

    def _prepare_payment_vals(self):
        '''Create the payment values.
        :return: The payment values as a dictionary.
        '''
        user_statement_id = self.env['account.user.statement'].search(
            [('user_id', '=', self.env.user.id), ('state', '=', 'open')]).name
        if not user_statement_id:
            user_statement_id = ''
        values = {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': " ".join(i.ref or i.name for i in self.invoice_ids) + " , " + user_statement_id or ' ',
            'cheque_date': self.cheque_date,
            'cheque_number': self.cheque_number,
            'bank_id': self.bank_id.id if self.bank_id else False,
            'account_number': self.account_number,
            'x_payment_methods': self.payment_methods.id,
            'x_cheque_type': self.cheque_type,
            'x_auth': self.auth,
            'x_tid': self.tid.id,
            'x_batch': self.batch,
            'x_benefit_ref': self.benefit_ref,
            'invoice_ids': [(6, 0, self.invoice_ids.ids)],
            'payment_type': ('inbound' if self.amount > 0 else 'outbound'),
            'amount': abs(self.amount),
            'currency_id': self.currency_id.id,
            'partner_id': self.invoice_ids[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[self.invoice_ids[0].type],
            'partner_bank_account_id': self.invoice_ids[0].invoice_partner_bank_id.id,
            'payment_difference': self.payment_resgiter_id.payment_difference,
            'payment_difference_handling': self.payment_resgiter_id.payment_difference_handling,
            'writeoff_account_id': self.payment_resgiter_id.writeoff_account_id.id,
            'writeoff_label': self.payment_resgiter_id.writeoff_label,

        }
        if self.auth:
            values['communication'] = values['communication'] + " , " + self.auth
        return values

    @api.onchange('journal_id', 'tid', 'id', 'batch')
    def tid_get_domain(self):
        res = {}
        user_statement_id = self.env['account.user.statement'].search(
            [('user_id', '=', self.env.user.id), ('state', '=', 'open')], limit=1).terminal_id
        tid = self.env['bank.card.reader.line'].search(
            [('terminal_id', '=', user_statement_id.id), ('payment_methods', '=', self.payment_methods.id)])
        res['domain'] = {'tid': [
            ('id', 'in', tid.tid_ids.ids)]}
        return res


class BankCardReader(models.Model):
    _name = 'bank.card.readers'
    _description = 'TID Card Device'

    name = fields.Char(string="TID Number", required=1)
    payment_methods = fields.Many2one("statement.payment.methods", string="Payment Method",
                                      domain="[('bank_type', '=', 'card')]")
    holder_id = fields.Many2one('res.partner', string='Holder')
    terminal_ids = fields.Many2many('sale.terminal', string="Terminal", store=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'TID Number Must Be Unique!')
    ]

    # @api.constrains('name')
    # def _check_number(self):
    #     number = self.name
    #     if number and len(number) < 8:
    #         raise UserError(_('TID number must be 8'))


class BankCardReaderLine(models.Model):
    _name = 'bank.card.reader.line'
    _description = 'TID Card line Device'

    payment_methods = fields.Many2one("statement.payment.methods", string="Payment Method")
    tid_ids = fields.Many2many('bank.card.readers', string="TID", compute="_compute_get_tid",
                               inverse="_inverse_tid_terminal")
    terminal_id = fields.Many2one('sale.terminal', string="Terminal")

    @api.depends('payment_methods')
    def _get_domain_payment(self):
        for domain in self:
            domain.payment_method_ids = [(4, domain.payment_methods.id)]

    # @api.onchange('payment_methods', 'tid_ids')
    # def domain_onchange_payment_method(self):
    #     res = {}
    #     res['domain'] = {'tid_ids': [('id', 'in', self.env['bank.card.readers'].search(
    #         [('payment_methods', '=', self.payment_methods.id)]).ids)]}
    #     return res

    # @api.depends('payment_methods')
    def _compute_get_tid(self):
        for line in self:
            tid = self.env['bank.card.readers'].search(
                [('payment_methods', '=', line.payment_methods.id), ('terminal_ids', 'in', line.terminal_id.id)]).ids
            line.tid_ids = tid

    def _inverse_tid_terminal(self):

        for line in self:
            vals = []
            for tid in line.tid_ids:
                for terminal in line.terminal_id:
                    tid.terminal_ids = [(4, terminal.id)]
                vals.append(tid.id)

            for tid_main in self.env['bank.card.readers'].search(
                    [('payment_methods', '=', line.payment_methods.id), ('terminal_ids', 'in', line.terminal_id.id)]):
                for term in tid_main.terminal_ids:
                    if term.id == line.terminal_id.id and tid_main.id not in vals:
                        print(tid_main.name)
                        tid_main.terminal_ids = [(3, term.id)]

    def unlink(self):
        for payment in self:
            payment.terminal_id.allowed_payment_method = [(3, payment.payment_methods.id)]
        return super(BankCardReaderLine, self).unlink()
