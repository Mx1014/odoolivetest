# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_invoice_state = fields.Selection(related="sale_id.invoice_status", store=True)
    x_create_invoice = fields.Boolean(string="Create Invoice?", compute="_is_create_invoice", store=True)
    x_show_invoice_id = fields.Many2one('account.move', string="Invoices")

    @api.depends('x_invoice_state', 'sale_id.order_line', 'state', 'sale_id.state')
    def _is_create_invoice(self):
        for picking in self:
            flag = 0
            for line in picking.move_ids_without_package.mapped('sale_line_id'):
                if line.qty_invoiced < line.product_uom_qty and line.qty_delivered:
                    flag = 1
            if flag:
                picking.x_create_invoice = True
            else:
                picking.x_create_invoice = False

    def action_create_invoice(self):
        for picking in self:
            #print(picking.move_ids_without_package.mapped('sale_line_id'))
            sale_order = picking.sale_id
            if picking.state == 'done' and sale_order and picking:
                invoice = sale_order._create_invoices()
                picking.x_show_invoice_id = invoice.id
                if invoice:
                    invoice.x_picking_id = picking.id
                    invoice.post()
                    payments = self.env['account.payment'].search([('x_sale_id', '=', sale_order.id)])
                    print(payments, 'sssssss')
                    for payment in payments:
                        if not payment.reconciled_invoice_ids:
                            payment.action_draft()
                            payment.invoice_ids = [(4, invoice.id)]
                            payment.post()
                #invoice.action_post()
                #invoice.action_register_payment_custom()
                self.link_credit_note_selected(invoice)
                return invoice

    def link_credit_note_selected(self, invoice):
        for stock in self:
            amount = 0.0
            credit_move_id = False
            if stock.sale_id.x_credit_note_ids:
                credit_equal = stock.sale_id.x_credit_note_ids.filtered(lambda x: x.x_amounts_apply == invoice.amount_residual)
                credit_greater = stock.sale_id.x_credit_note_ids.filtered(lambda x: x.x_amounts_apply > invoice.amount_residual)
                credit_smaller = stock.sale_id.x_credit_note_ids.filtered(lambda x: x.x_amounts_apply < invoice.amount_residual)
                if credit_equal:
                    amount = credit_equal[0].x_amounts_apply
                    credit_move_id = credit_equal[0]
                elif credit_greater:
                    amount = invoice.amount_residual
                    credit_move_id = credit_greater[0]

                if not credit_equal and not credit_greater and sum(credit_smaller.mapped('x_amounts_apply')) <= invoice.amount_residual:
                       credit_move_id = credit_smaller
                       for move in credit_move_id:
                           self.env['account.partial.reconcile'].create({
                               'debit_move_id': invoice.line_ids.filtered(lambda x: x.account_id.id == 6).id,
                               'credit_move_id': move.line_ids.filtered(lambda x: x.account_id.id == 6).id,
                               'amount': abs(move.x_amounts_apply),
                           })
                else:
                    for move in credit_move_id:
                        self.env['account.partial.reconcile'].create({
                            'debit_move_id': invoice.line_ids.filtered(lambda x: x.account_id.id == 6).id,
                            'credit_move_id': move.line_ids.filtered(lambda x: x.account_id.id == 6).id,
                            'amount': abs(amount),
                        })

    def action_view_invoice_for_done_dn(self, invoice):
        self.ensure_one()
        return {
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'views': [
                (self.env.ref('account.view_move_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'res_id': invoice.id,
              # [('id', 'in', sales.mapped('invoice_ids.id'))]
        }

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'views': [
                (self.env.ref('account.view_move_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'res_id': self.x_show_invoice_id.id,
        }


    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if self.code == 'outgoing':
            self.action_create_invoice()

        return res
