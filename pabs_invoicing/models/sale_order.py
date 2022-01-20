# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SalesOrder(models.Model):
    _inherit = 'sale.order'

    #x_payment_count = fields.Integer(string="Payments", compute="_count_payment_registered")
    #x_payment_amount = fields.Boolean(string="Fully Paid?", compute="_count_payment_registered")
    #x_amount_residual = fields.Monetary(string="Amount Due", compute="_get_amount_residual")
    #x_credit_note_ids = fields.Many2many('account.move', string="Credit Note Applied", copy=False)
    x_amount_not_invoiced = fields.Monetary(string="Amount Due", compute="_get_amount_not_invoiced")
    x_deliver_to = fields.Char(string="Delivery Address")

    def action_confirm(self):
        res = super(SalesOrder, self).action_confirm()
        self.x_deliver_to = """
                            %s, Rd %s, B %s
                            %s
                         """ % (self.partner_shipping_id.street_number, self.partner_shipping_id.x_address_road.name, self.partner_shipping_id.x_address_block.name, self.partner_shipping_id.city_id.name)
        return res

    def action_for_server_action(self):
        self.x_deliver_to = """
                            %s, Rd %s, B %s
                            %s
                         """ % (self.partner_shipping_id.street_number, self.partner_shipping_id.x_address_road.name, self.partner_shipping_id.x_address_block.name, self.partner_shipping_id.city_id.name)


    # def _get_amount_residual(self):
    #     for order in self:
    #         paid = 0.0
    #         order.get_amount_downpayment()
    #         order.x_amount_residual = order.amount_total
    #         payments = self.env['account.payment'].search([('x_sale_id', '=', order.id)])
    #         for payment in payments:
    #             if not payment.reconciled_invoice_ids:
    #                 order.x_amount_residual -= payment.amount
    #             else:
    #                 if order.invoice_ids.filtered(lambda x: x.id in payment.reconciled_invoice_ids.ids):
    #                     order.x_amount_residual -= payment.amount
    #         print('////////////////////')
    #         all_invoices = order.invoice_ids.filtered(lambda x: x.type == 'out_invoice' and x.state == 'posted')
    #         all_credit_notes = order.invoice_ids.filtered(lambda x: x.type == 'out_refund' and x.state == 'posted')
    #         if order.invoice_ids.filtered(lambda x: x.type == 'out_refund' and x.state == 'posted').mapped('amount_residual') != []:
    #             total_invoice = order.amount_total - sum(all_invoices.mapped('amount_total')) + sum(all_invoices.mapped('amount_residual'))
    #             order.x_amount_residual = total_invoice + abs(sum(all_credit_notes.mapped('amount_total'))) - abs(sum(all_credit_notes.mapped('amount_residual')))

    # def _get_amount_residual(self):
    #     for order in self:
    #         paid = 0.0
    #         i = 0
    #         order.get_amount_downpayment()
    #         order.x_amount_residual = order.amount_total
    #         all_invoices = order.invoice_ids.filtered(lambda x: x.type == 'out_invoice' and x.state == 'posted')
    #         all_credit_notes = order.invoice_ids.filtered(lambda x: x.type == 'out_refund' and x.state == 'posted')
    #
    #         for invoice in order.invoice_ids:
    #             if invoice.state == 'posted' and invoice.amount_residual == 0.0 and invoice.type == 'out_invoice':
    #                 order.x_amount_residual -= invoice.amount_total
    #             elif invoice.state == 'posted' and invoice.amount_residual != 0.0 and invoice.amount_residual != invoice.amount_total and invoice.type == 'out_invoice':
    #                 paid = paid + (invoice.amount_total - invoice.amount_residual)
    #                 order.x_amount_residual = order.amount_total - paid
    #
    #         payments = self.env['account.payment'].search([('x_sale_id', '=', order.id)])
    #         for payment in payments:
    #             if not payment.reconciled_invoice_ids:
    #                 order.x_amount_residual -= payment.amount
    #             else:
    #                 if order.invoice_ids.filtered(lambda x: x.id in payment.reconciled_invoice_ids.ids):
    #                     # order.x_amount_residual = order.amount_total
    #                     order.x_amount_residual -= payment.amount
    #
    #
    #         if sum(order.x_credit_note_ids.mapped('x_amounts_apply')) > order.x_amount_residual and i == 0:
    #             order.x_amount_residual = 0.0
    #         else:
    #             order.x_amount_residual -= sum(order.x_credit_note_ids.mapped('x_amounts_apply'))
    #         i += 1
    #
    #         if order.invoice_ids.filtered(lambda x: x.type == 'out_refund' and x.state == 'posted').mapped('amount_residual') != []:
    #             total_invoice = order.amount_total - sum(all_invoices.mapped('amount_total')) + sum(all_invoices.mapped('amount_residual'))
    #             order.x_amount_residual = total_invoice + abs(sum(all_credit_notes.mapped('amount_total'))) - abs(sum(all_credit_notes.mapped('amount_residual')))

    def _get_amount_not_invoiced(self):
        for order in self:
            order_line = order.order_line
            invoice = order_line.invoice_lines.filtered(lambda x: x.move_id.type == 'out_invoice')
            credit = order_line.invoice_lines.filtered(lambda x: x.move_id.type == 'out_refund')
            order.x_amount_not_invoiced = order.amount_total - (sum(invoice.mapped('price_total'))) + sum(credit.mapped('price_total'))




    # def _count_payment_registered(self):
    #     for payment in self:
    #         paid = self.env['account.payment'].search([('x_sale_id', '=', payment.id)])
    #         # if payment.amount_total == sum(paid.mapped('amount')):
    #         #     payment.x_payment_amount = True
    #         # else:
    #         #     payment.x_payment_amount = False
    #         if payment.x_amount_residual == 0.0:
    #             payment.x_payment_amount = True
    #         else:
    #             payment.x_payment_amount = False
    #         payment.x_payment_count = len(paid.ids)


    # def action_register_payment_custom(self):
    #     context = dict(self._context or {})
    #     context.update(active_ids=self.ids, active_model='sale.order', active_id=self.id)
    #     return {
    #         'name': _('Register Payment'),
    #         'res_model': 'account.payment.register.custom',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('pabs_sale.view_account_payment_register_custom_form').id,
    #         'context': context,
    #         'target': 'new',
    #         'type': 'ir.actions.act_window',
    #     }

    # def action_view_payment_register_payment(self):
    #     return {
    #         'name': _('Payments'),
    #         'res_model': 'account.payment',
    #         'view_mode': 'tree,form',
    #         'views': [
    #             (self.env.ref('account.view_account_payment_tree').id, 'tree'),
    #             (self.env.ref('account.view_account_payment_form').id, 'form'),
    #         ],
    #         'type': 'ir.actions.act_window',
    #         'domain': [('x_sale_id', '=', self.id)],
    #
    #     }
    #
    # def action_view_paid_by_customer_credit(self):
    #     self.ensure_one()
    #     return {
    #         'name': _('Credit Notes'),
    #         'res_model': 'account.move',
    #         'view_mode': 'tree,form',
    #         'views': [
    #             (self.env.ref('account.view_invoice_tree').id, 'tree'),
    #             (self.env.ref('account.view_move_form').id, 'form'),
    #         ],
    #         'type': 'ir.actions.act_window',
    #         'domain': [('id', 'in', self.x_credit_note_ids.ids)],
    #     }


    def action_view_sale_order(self):
        return {
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'views': [
                (self.env.ref('sale.view_order_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'res_id': self.id,

        }
