from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import date
from datetime import timedelta
from datetime import datetime
import dateutil


class hr_loan_lines(models.Model):
    _name = 'hr.loan.lines'
    _description = 'Employees Loan Lines'

    payslip_id = fields.Many2one('hr.payslip', string='Payslip')
    date = fields.Date(string='Date')
    amount = fields.Float(string='Amount', digits=dp.get_precision('Payroll'))
    loan_id = fields.Many2one('hr.loan', 'Loan')
    loan_installment_id = fields.Many2one('loan.payment.line', 'Installment Payment Date')
