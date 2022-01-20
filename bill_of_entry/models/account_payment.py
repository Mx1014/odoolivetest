# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.http import request
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    x_manual_exchange = fields.Boolean(string="Apply Manual Exchange Rate")
    x_rate = fields.Float(string="Exchange Rate")
    x_amount_rate = fields.Float(string="Base Amount", digits=(16, 3))


    def _prepare_payment_moves(self):
        res = super(AccountPayment, self)._prepare_payment_moves()
        if self.x_manual_exchange:
            amount = self.amount * (1 / self.x_rate)
            for res in res:
                for vals in res['line_ids']:
                    if vals[len(vals)-1]['credit'] != 0.0:
                        vals[len(vals)-1]['credit'] = amount
                    if vals[len(vals)-1]['debit'] != 0.0:
                        vals[len(vals)-1]['debit'] = amount
        return res

    @api.onchange('x_amount_rate')
    def onchange_currency_exchange_amount(self):
        if self.amount != 0.0 and self.x_amount_rate != 0.0:
           self.x_rate = self.amount / self.x_amount_rate

    @api.onchange('x_rate')
    def onchange_currency_exchange_rate(self):
        if self.amount != 0.0 and self.x_rate != 0.0:
            amount = self.amount * (1 / self.x_rate)
            self.x_amount_rate = amount
