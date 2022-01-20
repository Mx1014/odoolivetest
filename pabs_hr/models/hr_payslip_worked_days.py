from odoo import models, fields, api, _
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class HrWorkingDays(models.Model):
    _inherit = "hr.payslip.worked_days"

    x_date_from = fields.Date(string="From")
    x_date_to = fields.Date(string="To")
    employee_id = fields.Many2one('hr.employee', string='Employee', store=True)
    x_department = fields.Many2one('hr.department', string='Department', store=True,
                                   related='employee_id.department_id')
    x_contract = fields.Many2one('hr.contract', string='Contract', store=True,
                                 related='employee_id.contract_id')

    def write(self, vals):
        res = super(HrWorkingDays, self).write(vals)
        self._update_line()
        return res

    def _update_line(self):
        worked_days = self.mapped('payslip_id')
        print(worked_days, "nnv")
        for work in worked_days:
            work_lines = self.filtered(lambda x: x.payslip_id == work)
            msg = "<b>" + _("Work Days updated.") + "</b><ul>"
            print(work_lines, "aaasdddf")
            for line in work_lines:
                msg += _("Type") + ": %s <br/>" % (line.work_entry_type_id.name,)
                msg += _("Number of Days") + ": %s <br/>" % (line.number_of_days,)
                msg += _("Number of Hours") + ": %s <br/>" % (line.number_of_hours,)
                msg += _("Amount") + ": %s <br/>" % (line.amount,)
            msg += "</ul>"
            work.message_post(body=msg)