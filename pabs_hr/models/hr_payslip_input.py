from odoo import models, fields, api, _
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class Hrinput(models.Model):
    _inherit = 'hr.payslip.input'

    def write(self, vals):
        res = super(Hrinput, self).write(vals)
        self._update_line()
        return res

    def _update_line(self):
        inputs = self.mapped('payslip_id')
        for input in inputs:
            input_lines = self.filtered(lambda x: x.payslip_id == input)
            msg = "<b>" + _("Other Inputs Updated.") + "</b><ul>"
            for line in input_lines:
                msg += _("Description") + ": %s <br/>" % (line.input_type_id.name,)
                msg += _("Amount") + ": %s <br/>" % (line.amount,)
            msg += "</ul>"
            input.message_post(body=msg)
