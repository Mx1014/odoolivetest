# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def refund_undelivered(self, selected_ids, id, qty):
        res = super(HelpdeskTicket, self).refund_undelivered(selected_ids, id, qty)
        orderline_sudo = self.env['sale.order.line'].sudo()
        order_lines = orderline_sudo.browse(selected_ids)
        cancelled_payment = False
        for line in order_lines:
            order = line.order_id
        # module = self.env['ir.module.module'].search([('name', '=', 'pabs_invoicing')])
        # if module and module.state == 'installed':
        if order.x_payment_count and not cancelled_payment:
            paid = self.env['account.payment'].search([('x_sale_id', '=', order.id), ('state', '!=', 'cancelled')])
            user_statement_id = self.env['account.user.statement'].search(
                [('user_id', '=', self.env.user.id), ('state', '=', 'open')]).id
            due = order.amount_total - sum(paid.mapped('amount'))
            if due != 0:
                # to_return = sum(order.order_line.mapped('price_total')) - abs(due)
                payment_sent = paid[0].copy(
                    {'payment_type': 'outbound', 'amount': abs(due), 'x_session_id': user_statement_id})
                payment_sent.post()
                reconcile_amount = abs(paid[0].amount) - abs(payment_sent.amount)
                test = self.env['account.partial.reconcile'].create({
                    'credit_move_id': paid[0].move_line_ids.filtered(lambda x: x.credit != 0.0).id,
                    'debit_move_id': payment_sent.move_line_ids.filtered(lambda x: x.debit != 0.0).id,
                    'amount': abs(due),

                })
                payment_sent.move_reconciled = True
                cancelled_payment = True
        return res
