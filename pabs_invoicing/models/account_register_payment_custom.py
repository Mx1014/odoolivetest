# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError
from odoo.addons.account.models.account_payment import MAP_INVOICE_TYPE_PARTNER_TYPE
import js2py


class AccountPaymentRegisterCustom(models.TransientModel):
    _inherit = 'account.payment.register.custom'

    due_amount = fields.Monetary(compute='_compute_due_amount', string='Due Amount')
    change = fields.Monetary(compute='_compute_change', string='Change')

    @api.depends('line_ids', 'account_credit_note_ids')
    def _compute_change(self):
        for payment in self:
            paid_amount = sum(self.line_ids.mapped('amount'))
            payment.change = paid_amount - payment.amount if paid_amount - payment.amount > 0 else 0

    @api.depends('line_ids', 'account_credit_note_ids')
    def _compute_due_amount(self):
        for payment in self:
            credit = self.account_credit_note_ids.filtered(lambda x: x.x_selected_id == True)
            paid = sum(line.amount for line in payment.line_ids) + abs(sum(credit.mapped('x_amounts_apply')))
            payment.due_amount = payment.amount - paid

    @api.onchange('account_credit_note_ids')
    def onchange_amount_calculate_due(self):
        for payment in self:
            credit = self.account_credit_note_ids.filtered(lambda x: x.x_selected_id == True)
            for line in credit:
                if not line.x_amounts_applied:
                    if line.amount_residual <= payment.due_amount:
                        line.x_amounts_applied = abs(line.amount_residual)
                        line.x_amounts_apply = abs(line.amount_residual)
                    elif line.amount_residual > payment.due_amount:
                        print(payment.due_amount)
                        line.x_amounts_applied = abs(payment.due_amount)
                        line.x_amounts_apply = abs(payment.due_amount)
                    if payment.due_amount == 0.0:
                        line.x_selected_id = False
                        line.x_amounts_applied = 0.0
                        line.x_amounts_apply = 0.0
            payment._compute_due_amount()

                    #raise Warning('Cannot Select More Credit Notes')



    def _get_credit_note(self):
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        active_model = self._context.get('active_model')

        if active_model == 'sale.order':
            sale_order = self.env['sale.order'].search([('id', 'in', active_ids)])
            to_return = self.env['account.move'].search(
                [('partner_id', '=', sale_order.partner_invoice_id.id), ('type', '=', 'out_refund'),
                 ('amount_residual', '!=', 0.0), ('state', '=', 'posted'),
                 ('id', 'not in', sale_order.x_credit_note_ids.ids)])

            to_return.update({'x_selected_id': False})
            return to_return.ids
        elif active_model == 'account.move':
            move = self.env['account.move'].search([('id', 'in', active_ids)])
            to_return_move = self.env['account.move'].search(
                [('partner_id', '=', move.partner_id.id), ('type', '=', 'out_refund'),
                 ('amount_residual', '!=', 0.0), ('state', '=', 'posted'),
                 ('id', 'not in', move.x_sale_id.x_credit_note_ids.ids)])

            to_return_move.update({'x_selected_id': False})
            return to_return_move

    account_credit_note_ids = fields.Many2many('account.move', string="Credit Note", default=_get_credit_note)

    @api.model
    def default_get(self, default_fields):
        rec = super(AccountPaymentRegisterCustom, self).default_get(default_fields)
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        active_model = self._context.get('active_model')
        # Check for selected invoices ids
        if active_ids and active_model == 'sale.order':
            sale_order = self.env['sale.order'].browse(active_ids)
            rec.update({
                'amount': sale_order.x_amount_residual,
                # 'invoice_ids': [(6, 0, sale_order.invoice_ids.ids)],
            })
        return rec

    def action_add_payment_line(self):
        journal_id = self.env.context.get('journal_id')
        payment_methods = self.env.context.get('payment_methods')
        active_model = self._context.get('active_model')
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        if (not journal_id or not self.invoice_ids) and active_model == 'account.move':
            return True

        if not journal_id and active_model == 'sale.order':
            return True

        journal = self.env['account.journal'].browse(int(journal_id))
        domain = [('payment_type', '=', 'outbound')]
        if active_model == 'account.move' and self.invoice_ids[0].is_inbound():
            domain = [('payment_type', '=', 'inbound')]
        elif active_model == 'sale.order':
            domain = [('payment_type', '=', 'inbound')]
        payment_method_id = self.env['account.payment.method'].search(domain, limit=1).id
        payment_method = self.env['statement.payment.methods'].browse(int(payment_methods))

        user_statement_id = self.env['account.user.statement'].search(
            [('user_id', '=', self.env.user.id), ('state', '=', 'open')], limit=1).terminal_id
        tid = self.env['bank.card.reader.line'].search(
            [('terminal_id', '=', user_statement_id.id), ('payment_methods', '=', payment_method.id)])
        print(tid.tid_ids.ids)

        if active_model == 'account.move':
            self.write({
                'line_ids': [(0, 0, {
                    'journal_id': journal.id,
                    'team_id': self.env['crm.team'].search([('member_ids', '=', self.env.user.id)]).id,
                    'payment_date': fields.Date.context_today(self),
                    'invoice_ids': [(6, 0, self.invoice_ids.ids)],
                    'payment_method_id': payment_method_id,
                    # 'amount': self.due_amount,
                    'currency_id': journal.currency_id.id or self.invoice_ids[0].currency_id.id,
                    'communication': self.invoice_ids[0].ref or self.invoice_ids[0].name,
                    'bank_type': journal.x_bank_type,
                    'payment_methods': payment_method.id,
                    'domain_tid': [(6, 0, tid.tid_ids.ids)],
                })]
            })



        elif active_model == 'sale.order':
            sale_order = self.env['sale.order'].browse(active_ids)
            self.write({
                'line_ids': [(0, 0, {
                    'journal_id': journal.id,
                    'team_id': self.env['crm.team'].search([('member_ids', '=', self.env.user.id)]).id,
                    'payment_date': fields.Date.context_today(self),
                    # 'invoice_ids': [(6, 0, self.invoice_ids.ids)],
                    'payment_method_id': payment_method_id,
                    # 'amount': self.due_amount,
                    'currency_id': journal.currency_id.id or sale_order.currency_id.id,
                    'communication': '%s - %s' % (sale_order.name, sale_order.user_statement_id.name),
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

    def create_payments(self):
        res = super(AccountPaymentRegisterCustom, self).create_payments()
        if self.due_amount < 0:
            raise Warning("Cannot Pay More Than SO Due")
        active_model = self._context.get('active_model')
        lines = self.env['account.move'].search([('id', 'in', self.account_credit_note_ids.filtered(lambda x: x.x_selected_id == True).ids)])
        self.use_credit_note(lines)
        if active_model == 'account.move':
            return res
        elif active_model == 'sale.order':
            return {'type': 'ir.actions.act_window_close'}



    @api.model
    def use_credit_note(self, lines):
        #lines = self.env['account.move'].search([('id', 'in', ids)])
        for line in lines:
            active_id = self._context.get('active_id')
            active_model = self._context.get('active_model')
            amount = 0.0
            line.x_selected_id = False
            if active_id:
                if active_model == 'sale.order':
                    sale_order = self.env['sale.order'].browse(active_id)
                    sale_order.x_credit_note_ids = [(4, line.id)]
                    invoices = sale_order.invoice_ids.filtered(
                        lambda x: x.state == 'posted' and x.type == 'out_invoice' and x.amount_residual != 0.0)
                    # if invoices:
                    for invoices in invoices:
                        if line.x_amounts_applied <= invoices.amount_residual:
                            amount = line.x_amounts_apply
                        else:
                            amount = invoices.amount_residual
                        for invoice in invoices:
                            self.env['account.partial.reconcile'].create({
                                'debit_move_id': invoice.line_ids.filtered(lambda x: x.account_id.id == 6).id,
                                'credit_move_id': line.line_ids.filtered(lambda x: x.account_id.id == 6).id,
                                'amount': abs(amount),
                            })
                elif active_model == 'account.move':
                    move = self.env['account.move'].browse(active_id)
                    move.x_sale_id.x_credit_note_ids = [(4, line.id)]
                    if line.amount_residual <= move.amount_residual:
                        amount = line.amount_residual
                    else:
                        amount = move.amount_residual
                    for invoice in move:
                        self.env['account.partial.reconcile'].create({
                            'debit_move_id': invoice.line_ids.filtered(lambda x: x.account_id.id == 6).id,
                            'credit_move_id': line.line_ids.filtered(lambda x: x.account_id.id == 6).id,
                            'amount': abs(amount),
                        })
        return True

    def action_view_invoice_after_payment(self, id):
        self.ensure_one()
        move = self.env['account.move'].search([('id', '=', id)])
        if move:
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
        else:
            return False

    def cancel_payments(self):
        lines = self.account_credit_note_ids.filtered(lambda x: x.x_selected_id == True)
        lines.update({'x_selected_id': False})
        invoice = self.action_view_invoice_after_payment(self._context.get('active_id'))
        if invoice:
            return invoice
        else:
            return {'type': 'ir.actions.act_window_close'}



class AccountPaymentRegisterLine(models.TransientModel):
    _inherit = 'account.payment.register.line'

    def _prepare_payment_vals(self):
        '''Create the payment values.
        :return: The payment values as a dictionary.
        '''
        active_model = self._context.get('active_model')
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        user_statement_id = self.env['account.user.statement'].search(
            [('user_id', '=', self.env.user.id), ('state', '=', 'open')]).name
        if not user_statement_id:
            user_statement_id = ''
        sale_order = self.env['sale.order'].browse(active_ids)
        communication = " ".join(
            i.name for i in sale_order) + " , " + user_statement_id or ' ' if active_model == 'sale.order' else (
            " ".join(i.ref or i.name for i in
                     self.invoice_ids) + " , " + user_statement_id or ' ' if active_model == 'account.move' else False)
        values = {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': communication,
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
            'invoice_ids': False if active_model == 'sale.order' else (
                [(6, 0, self.invoice_ids.ids)] if active_model == 'account.move' else False),
            'payment_type': ('inbound' if self.amount > 0 else 'outbound'),
            'amount': abs(self.amount),
            'currency_id': self.currency_id.id,
            'partner_id': sale_order.partner_invoice_id.id if active_model == 'sale.order' else (
                self.invoice_ids[0].commercial_partner_id.id if active_model == 'account.move' else False),
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[self.invoice_ids[0].type] if active_model == 'account.move' else ('customer' if active_model == 'sale.order' else False),
            'partner_bank_account_id': self.invoice_ids[0].invoice_partner_bank_id.id if active_model == 'account.move' else False,
            'payment_difference': self.payment_resgiter_id.payment_difference,
            'payment_difference_handling': self.payment_resgiter_id.payment_difference_handling,
            'writeoff_account_id': self.payment_resgiter_id.writeoff_account_id.id,
            'writeoff_label': self.payment_resgiter_id.writeoff_label,
            'x_sale_id': sale_order.id if active_model == 'sale.order' else False,

        }
        if self.auth:
            values['communication'] = values['communication'] + " , " + self.auth
        return values
