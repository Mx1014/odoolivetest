from collections import defaultdict
from datetime import datetime, date, time
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        res = super(HrPayslipEmployees, self).compute_sheet()
        slips = self.env['hr.payslip.run'].search([('id', '=', self.id)])
        for rec in slips.slip_ids:
            for line in rec:
                print(line, "line")
        return res
