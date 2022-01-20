# -*- coding: utf-8 -*-

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PayslipRegisterPayment(models.TransientModel):
    _name = "payslip.register.payment"
    _description = "Register Payment in Payslip"

    name = fields.Char()
    journal_id = fields.Many2one('account.journal', string="Journal")

    def action_register_single_payment(self):
        total_amount = 0.0
        active_id = self._context.get('active_id', False) or self._context.get('active_ids', False)
        for move in self.env['account.move'].search([('id', '=', active_id)]):
            single = move.x_single_payslip_id
            true = self.env['hr.salary.rule'].search([('name', '=', 'Net Salary'), ('struct_id', '=', single.struct_id.id)]).x_use_employee
            if single:
                #payment_methods = batch.x_bank_journal_id.outbound_payment_method_ids if total_amount < 0 else batch.x_bank_journal_id.inbound_payment_method_ids
                payment_methods = single.journal_id.outbound_payment_method_ids if total_amount < 0 else single.journal_id.inbound_payment_method_ids
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': 'outbound',
                    'partner_id': single.employee_id.address_id.id,
                    'partner_type': 'supplier',
                    'journal_id': self.journal_id.id,
                    'payment_date': single.date_to,
                    # 'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
                    'amount': single.net_wage,
                    'communication': move.ref,
                })
                print(payment)
                move.x_single_payment = payment
                # batch.x_payment_id.post()

