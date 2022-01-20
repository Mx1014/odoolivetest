from odoo import models, fields, api, _
from odoo.exceptions import Warning
from num2words import num2words
import datetime


class BankAccount(models.Model):
    _inherit = 'res.partner.bank'
    x_branch = fields.Char(string='Branch')
    x_iban = fields.Char(string='IBAN')


class TotalAmount(models.Model):
    _inherit = 'account.payment'
    x_amount_in_words = fields.Char(string='Amount in words', compute='amt_total')
    date_to_numbers = fields.Char(compute='_date_convert_to_number', required=True)
    remittance_details = fields.Char(string='Remittance Details')

    def amt_total(self):
        self.x_amount_in_words = self.currency_id.amount_to_text(self.amount)

    @api.depends('payment_date')
    def _date_convert_to_number(self):
        self.date_to_numbers = fields.Date.from_string(
            self.payment_date).strftime('%d%m%Y')

    # def _date(self):
    #     self.payment_date = datetime.datetime.strptime(self.payment_date.id, "%Y-%m-%d")