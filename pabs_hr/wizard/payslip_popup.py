import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class PayslipPopup(models.TransientModel):
    _name = 'payslip.popup'
    x_payslip = fields.Many2one('hr.payslip', string="Payslip")

    def action_payslip_done(self):
        self.x_payslip.get_anual_provision()
        self.x_payslip.get_indemnity_provision()
        return self.x_payslip.action_payslip_done()
