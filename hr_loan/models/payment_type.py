from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import date
from datetime import timedelta
from datetime import datetime
import dateutil


class PaymentType(models.Model):
    _name = 'payment.type'

    name = fields.Char(string='Description', track_visibility='onchange')
    x_account = fields.Many2one('account.account', string='Account', track_visibility='onchange')
    x_payslip_input_type = fields.Many2one('hr.payslip.input.type', string='Payslip Input Type', track_visibility='onchange')
    x_sequence_id = fields.Many2one('ir.sequence', string='Reference Sequence', track_visibility='onchange')
    is_bill = fields.Boolean()
    is_invoice = fields.Boolean()
    bill_invoice_selection = fields.Selection([('bill', 'Bill'), ('invoice', 'Invoice')],
                                              string='type of doc')
    loan_exemption_account = fields.Many2one('account.journal', string='Exemption Account',
                                             track_visibility='onchange')
