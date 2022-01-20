from odoo import models, fields, api, _
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class HrPayslipLineInherit(models.Model):
    _inherit = 'hr.payslip.line'
    hour = fields.Float(string='Hours')
    day = fields.Float(string='Days')
    x_refunded = fields.Boolean(string='Refunded', default=False, readonly=True, related='slip_id.refunded')
    x_credit_note = fields.Boolean(string='Credit Note', readonly=True, default=False, related='slip_id.credit_note')