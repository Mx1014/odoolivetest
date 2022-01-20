from odoo import models, fields, api, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    settlement_id = fields.Many2one('hr.settlement', string='Settlement', store=True)

    def compute_sheet(self):
        # self.restrict_payslip()
        res = super(HrPayslip, self).compute_sheet()
        for rec in self:
            if rec.settlement_id:
                rec.settlement_id.x_employee_slips = rec.id
                print(rec.settlement_id)
                rec.settlement_id.write({'state': 'final_review'})
        self.set_hour_and_days()

        return res