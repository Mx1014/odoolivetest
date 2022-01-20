from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class InputLine(models.Model):
    _name = 'hr.input'

    x_settlement_id = fields.Many2one('hr.settlement', string='Settlement', ondelete='cascade', index=True)
    x_input_type_id = fields.Many2one('hr.payslip.input.type', string='Description')
    x_amount = fields.Float(string='Amount', help="It is used in computation. For e.g. A rule for sales having "
                               "1% commission of basic salary for per product can defined in expression "
                               "like result = inputs.SALEURO.amount * contract.wage*0.01.")
