from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
from datetime import datetime, timedelta
from functools import partial
from itertools import groupby


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # x_invoice_payment = fields.Many2many('account.payment', string='Payment', compute="get_invoice_payment")
    # x_payment_due = fields.Monetary(string="Balance", compute="due_get")
    # x_payment_paid = fields.Monetary(string="Total Paid", compute="due_get")
    x_so_line = fields.Many2many('sale.order.line')
    x_invoice_date = fields.Date()
    x_amount_residual = fields.Monetary(string="Amount Due", compute="_get_amount_residual")
    x_downpayment_amount = fields.Monetary(string="Down Payment")

    # order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines', compute="filter_order_line", states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)

    # def filter_order_line(self):
    #     for order in self:
    #         res = self.env['sale.order.line'].search([('order_id', '=', order.id), ('is_downpayment', '=', False)])
    #         order.order_line = res

    def get_amount_downpayment(self):
        for order in self:
            order.x_downpayment_amount = order.amount_total
            lines = order.order_line.filtered(lambda x: x.is_downpayment)
            minus = sum(lines.invoice_lines.filtered(lambda x: x.debit != 0.0 and x.move_id.type == 'out_refund').mapped('price_total'))
            plus = sum(lines.invoice_lines.filtered(lambda x: x.credit != 0.0 and x.move_id.type == 'out_invoice').mapped('price_total'))
            total = plus - minus
            order.x_downpayment_amount -= total

   # @api.depends('invoice_status')
    def _get_amount_residual(self):
        for order in self:
            paid = 0.0
            order.get_amount_downpayment()
            order.x_amount_residual = order.amount_total
            all_invoices = order.invoice_ids.filtered(lambda x: x.type == 'out_invoice' and x.state == 'posted')
            all_credit_notes = order.invoice_ids.filtered(lambda x: x.type == 'out_refund' and x.state == 'posted')
            for invoice in order.invoice_ids:
                if invoice.state == 'posted' and invoice.amount_residual == 0.0 and invoice.type == 'out_invoice':
                    order.x_amount_residual -= invoice.amount_total
                elif invoice.state == 'posted' and invoice.amount_residual != 0.0 and invoice.amount_residual != invoice.amount_total and invoice.type == 'out_invoice':
                    paid = paid + (invoice.amount_total - invoice.amount_residual)
                    order.x_amount_residual = order.amount_total - paid
            if order.invoice_ids.filtered(lambda x: x.type == 'out_refund' and x.state == 'posted').mapped('amount_residual') != []:
                total_invoice = order.amount_total - sum(all_invoices.mapped('amount_total')) + sum(all_invoices.mapped('amount_residual'))
                print(total_invoice)
                order.x_amount_residual = total_invoice + abs(sum(all_credit_notes.mapped('amount_total'))) - abs(sum(all_credit_notes.mapped('amount_residual')))


    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['journal_id'] = self.env['ir.default'].sudo().get('account.move',
                                                              'x_completion_journal'),  # self.env['account.journal'].search([('name','=', 'Completion Certificate')]).id
        res['invoice_date'] = self.x_invoice_date
        res['x_sale_id'] = self.id
        return res

    def _create_invoices(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Create invoices.
        invoice_vals_list = []
        down_payment = []

        for order in self:
            pending_section = None

            # Invoice values.
            invoice_vals = order._prepare_invoice()

            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final):
                    if not line.is_downpayment:
                        down_payment.append(line.id)
                    if pending_section:
                        invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_invoice_line()))
                        pending_section = None

                    if len(order.order_line.filtered(lambda x: x.is_downpayment).ids) == len(order.order_line.filtered(lambda x: not x.is_downpayment).ids) and order.sale_order_type != 'service':
                        if line.is_downpayment:
                            if line.x_lineid in down_payment:
                                qty_to_update = line._prepare_invoice_line()
                                if line.x_qty != 0.0:
                                    qty_to_update['quantity'] = -self.env['sale.order.line'].browse(
                                        int(line.x_lineid)).qty_to_invoice
                                invoice_vals['invoice_line_ids'].append((0, 0, qty_to_update))
                            else:
                                if line.x_qty == 0.0:
                            #     for so_line in order.x_so_line:
                                  invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_invoice_line()))
                        if not line.is_downpayment:
                            invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_invoice_line()))
                    else:
                        invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_invoice_line()))

            if not invoice_vals['invoice_line_ids']:
                raise UserError(_(
                    'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_(
                'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            for grouping_keys, invoices in groupby(invoice_vals_list,
                                                   key=lambda x: (x.get('partner_id'), x.get('currency_id'))):

                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['invoice_payment_ref'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs),
                    'invoice_origin': ', '.join(origins),
                    'invoice_payment_ref': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

            # 3) Manage 'final' parameter: transform out_invoice to out_refund if negative.
            out_invoice_vals_list = []
            refund_invoice_vals_list = []
            if final:
                for invoice_vals in invoice_vals_list:
                    if sum(l[2]['quantity'] * l[2]['price_unit'] for l in invoice_vals['invoice_line_ids']) < 0:
                        for l in invoice_vals['invoice_line_ids']:
                            l[2]['quantity'] = -l[2]['quantity']
                        invoice_vals['type'] = 'out_refund'
                        refund_invoice_vals_list.append(invoice_vals)
                    else:
                        out_invoice_vals_list.append(invoice_vals)
            else:
                out_invoice_vals_list = invoice_vals_list

            # Create invoices.
            moves = self.env['account.move'].with_context(default_type='out_invoice').create(out_invoice_vals_list)
            moves += self.env['account.move'].with_context(default_type='out_refund').create(refund_invoice_vals_list)
            for move in moves:
                move.message_post_with_view('mail.message_origin_link',
                                            values={'self': move,
                                                    'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                                            subtype_id=self.env.ref('mail.mt_note').id
                                            )
            return moves


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # x_completion_date = fields.Date(related='task_id.x_complete_date')
    x_lineid = fields.Integer(string="Advance Ref", store=True, copy=False)
    x_down_payment_amount = fields.Monetary(string='Down Payment', copy=False)
    x_qty = fields.Float(string="qty")

    # def _prepare_invoice_line(self):
    #     value = super(SaleOrderLine, self)._prepare_invoice_line()
    #     value['x_so_line'] = self.task_id.sale_line_id.id
    #     return value
