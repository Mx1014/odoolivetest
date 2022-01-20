from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class ReviewLoans(models.TransientModel):
    _name = 'review.loan'
    x_employee_name = fields.Many2one('hr.employee', string='Employee', track_visibility='onchange')
    x_loan_ids = fields.Many2many('hr.loan', string="Loans", tracking=True, store=True)
    x_id = fields.Integer(string="ID", store=True)

    def action_done(self):
        state = self.env['hr.settlement'].search(
            [('id', '=', self.x_id), ('employee_name', '=', self.x_employee_name.id)])
        for rec in self:
            if rec.x_loan_ids:
                for line in rec.x_loan_ids:
                    for records in line.payment_ids:
                        records.installment_date = fields.Date.today()
                        vals = {'state': 'final_slip'}
                        state.write(vals)
            if not rec.x_loan_ids:
                print("ffffs")
                vals = {'state': 'final_slip'}
                state.write(vals)

