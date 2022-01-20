from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import date
from datetime import timedelta
from datetime import datetime
import dateutil


class PaymentIdLines(models.Model):
    _name = 'loan.payment.line'
    _rec_name = "installment_date"

    installment_date = fields.Date(string='Installment Date')
    installment_amount = fields.Monetary(string='Installment Amount')
    state = fields.Selection(
        [('paid', 'Paid'), ('pending', 'Pending'), ('partial', 'Paid Partial')],
        string='State', default='pending', readonly=True, track_visibility='onchange', copy=False)
    payment_line_id = fields.Many2one('hr.loan', 'Payment')
    company_id = fields.Many2one('res.company', string='Company', store=True, readonly=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency")
    installment_unpaid = fields.Monetary(string="Amount Unpaid")

    # @api.depends('installment_amount')
    # def payment_status(self):
    #     for rec in self:
    #         if rec.installment_amount == 0:
    #             self.state = 'paid'
    #         else:
    #             self.state = 'pending'


