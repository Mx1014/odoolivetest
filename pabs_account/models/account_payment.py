from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from datetime import datetime


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    x_payment_due_amount = fields.Monetary(string='Payment Due Amount', compute='compute_amount', store=True)
    

    _sql_constraints = [
        ('unique_benefit', 'UNIQUE(benefit_ref)', 'BenefitPay reference cannot be duplicated'),
    ]
    #
    #     def _compute_invoice_ids(self):
    #         invoice = self.env['account.move'].search([('id', '=', self._context.get('active_id'))])
    #         print(invoice, "INNN")
    #         for line in self:
    #             for rec in invoices:
    #                 info = rec._get_reconciled_info_JSON_values()
    #                 for payment in info:
    #                     line.x_due_amount = payment['amount']
    #
    #             # for line in rec.reconciled_invoice_ids:
    #             #     rec.x_due_amount += abs(line.amount_total_signed - rec.amount)
    #         # else:
    #         #     rec.x_due_amount = 0.0

    # def compute_amount(self):
    #     for rec in self:
    #         rec.x_payment_due_amount = 0.0
    #         for line in self.reconciled_invoice_ids:
    #             info = line._get_reconciled_info_JSON_values()
    #             for payment in info:
    #                 print(payment, "Pay")
    #                 print(info, "Pay")
    #                 if self.id == payment['account_payment_id']:
    #                     print(self.id, "00000")
    #                     print(payment['account_payment_id'], "account_payment_id")
    #                     rec.x_payment_due_amount += payment['amount']
    #                     print(payment['amount'], "AMMMMM")
    #                     rec.x_payment_due_amount = rec.x_payment_due_amount - rec.amount
    #                 elif not self.id == payment['account_payment_id']:
    #                     rec.x_payment_due_amount = rec.amount
    #                     print(rec.x_payment_due_amount, "DDDDDDDD")
    # return  rec.x_payment_due_amount

    @api.depends('invoice_ids', 'reconciled_invoice_ids', 'amount')
    def compute_amount(self):
        for rec in self:
            a = 0.0
            rec.x_payment_due_amount = 0.0
            if not rec.has_invoices:
                if rec.payment_type == 'outbound':
                    rec.x_payment_due_amount = rec.amount
                else:
                    rec.x_payment_due_amount = -rec.amount
            if rec.has_invoices:
                for line in rec.reconciled_invoice_ids:
                    info = line._get_reconciled_info_JSON_values()
                    for payment in info:
                        # due = rec.x_payment_due_amount
                        if rec.id == payment['account_payment_id']:
                            a += payment['amount']
                            print(info)
                            val = rec.amount - a
                            rec.x_payment_due_amount = -val

                        # a = payment['amount']
                        # print(a, "aaaa")
                        # val = a - rec.amount
                        # print(val, "val 11111")
                        #
                        # due -= rec.amount - abs(val)
                        # print(due, "dueee")
                        # rec.x_payment_due_amount = -due

                # if rec.id == payment['account_payment_id']:
                #     # payment_done = sum(line.amount_total_signed for line in rec.reconciled_invoice_ids) - sum(
                #     #     line.amount_residual_signed for line in rec.reconciled_invoice_ids)
                #     payment_done = sum(rec.reconciled_invoice_ids.mapped('amount_total_signed')) - sum(
                #         rec.reconciled_invoice_ids.mapped('amount_residual_signed'))
                #     rec.x_payment_due_amount = -(rec.amount - payment_done)
