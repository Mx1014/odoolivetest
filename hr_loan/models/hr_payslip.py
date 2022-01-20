from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import date
from datetime import timedelta
from datetime import datetime
import dateutil


class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    loan_link = fields.Many2many('loan.payment.line', string='Loan Link')

    def action_payslip_done(self):
        res = super(hr_payslip, self).action_payslip_done()
        for payslip in self:
            for line in payslip.line_ids:
                if line.code == 'NET' and line.amount < 0:
                    raise UserError('Slip Came By Minus %s' % payslip.name)
            for rec in payslip.loan_link:
                unpaid = rec.installment_unpaid
                to_pay = sum(payslip.input_line_ids.filtered(
                    lambda x: x.input_type_id.id == rec.payment_line_id.payment_type.x_payslip_input_type.id).mapped('amount'))
                rec.installment_unpaid -= to_pay
                if rec.installment_unpaid != 0.0 and rec.installment_unpaid != unpaid:
                    rec.state = 'partial'
                    rec.payment_line_id.loan_ids = [
                        (0, 0, {'payslip_id': payslip.id, 'loan_installment_id': rec.id, 'date': payslip.date_to,
                                'amount': to_pay})]
                elif rec.installment_unpaid == 0.0:
                    rec.state = 'paid'
                    rec.payment_line_id.loan_ids = [
                        (0, 0, {'payslip_id': payslip.id, 'loan_installment_id': rec.id, 'date': payslip.date_to,
                                'amount': to_pay})]
        return res

    # def action_payslip_done(self):
    #     for payslip in self:
    #         amount = 0
    #         for line in payslip.line_ids:
    #             if line.code == 'LORP':
    #                 amount += line.amount
    #     loans = self.env['hr.loan'].search(
    #         [('employee_id', '=', self.employee_id.id), ('installment', '>', 0), ('balance', '>', 0),
    #          ('state', '=', 'open')])
    #     for loan in loans:
    #         if loan.installment >= (amount * -1):
    #             if loan.balance >= loan.installment:
    #                 loan.loan_ids = [(0, 0, {'payslip_id': self.id, 'date': self.date_to, 'amount': amount * -1})]
    #                 amount = 0
    #             elif loan.balance < loan.installment and loan.balance >= (amount * -1):
    #                 loan.loan_ids = [(0, 0, {'payslip_id': self.id, 'date': self.date_to, 'amount': amount * -1})]
    #                 amount = 0
    #             else:
    #                 amount += loan.balance
    #                 loan.loan_ids = [(0, 0, {'payslip_id': self.id, 'date': self.date_to, 'amount': loan.balance})]
    #         elif loan.installment < (amount * -1):
    #             if loan.balance <= loan.installment:
    #                 loan.loan_ids = [(0, 0, {'payslip_id': self.id, 'date': self.date_to, 'amount': loan.balance})]
    #                 amount += loan.balance
    #             elif loan.balance > loan.installment:
    #                 loan.loan_ids = [(0, 0, {'payslip_id': self.id, 'date': self.date_to, 'amount': loan.installment})]
    #                 amount += loan.installment
    #     return super(hr_payslip, self).action_payslip_done()

    def get_inputs(self, contracts, date_from, date_to):
        res = super(hr_payslip, self).get_inputs(contracts, date_from, date_to)
        # loans = self.env['hr.loan'].search(
        #     [('employee_id', '=', self.employee_id.id), ('installment', '>', 0), ('balance', '>', 0),
        #      ('state', '=', 'open')])
        loans_lines = self.env['loan.payment.line'].search(
            [('payment_line_id.employee_id', '=', self.employee_id.id), ('payment_line_id.state', '=', 'open'),
             ('installment_unpaid', '>', 0), ('installment_unpaid', '=', self.date_from)])
        loan = 0
        for l in loans_lines:
            loan += l.installment_unpaid
        res += [{'name': 'Loan', 'code': 'Loan', 'contract_id': self.contract_id.id, 'amount': loan * -1}]
        return res

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_loan(self):
        for record in self:
            for input in record.input_line_ids:
                if input.x_is_true:
                    record.input_line_ids = [(2, input.id)]
            record.loan_link = False
            x = record.env['hr.loan'].search([('employee_id', '=', record.employee_id.id), ('state', '=', 'open')])
            y = record.env['loan.payment.line'].search(
                [('installment_date', '>=', record.date_from), ('installment_date', '<=', record.date_to)])
            currnet_installments_ids = []
            if x:
                for rec in x:
                    for line in record.env['loan.payment.line'].search(
                            [('payment_line_id', '=', rec.id), ('state', '!=', 'paid'),
                             ('installment_date', '>=', record.date_from),
                             ('installment_date', '<=', record.date_to)]):
                        currnet_installments_ids.append(line.id)
            record.loan_link = currnet_installments_ids
            # if record.input_line_ids.x_is_true:
            #     if record.input_line_ids:
            #         record.input_line_ids = [(2, inputs.id)]
                # if record.input_line_ids:
                    # record.input_line_ids = [(2, inputs.id)]
            if x:
                loan_total = 0

                for line in record.loan_link:
                    loan_total += line.installment_amount
                record.input_line_ids = [(0, 0, {
                        'input_type_id': rec.payment_type.x_payslip_input_type.id, #line.payment_line_id.payment_type.x_payslip_input_type.id,
                        'amount': loan_total, #line.installment_unpaid,
                        'x_is_true': True
                })]
            # <<<<<<< HEAD
            #             for inputs in record:
            #                 if record.input_line_ids.x_is_true:
            #                     record.input_line_ids = [(3, inputs.id, 0)]
            #         record.loan_link = False
            #         x = record.env['hr.loan'].search([('employee_id', '=', record.employee_id.id), ('state', '=', 'open')])
            #         y = record.env['loan.payment.line'].search(
            #             [('installment_date', '>=', record.date_from), ('installment_date', '<=', record.date_to)])
            #         currnet_installments_ids = []
            #         if x:
            #             for rec in x:
            #                 for line in record.env['loan.payment.line'].search(
            #                         [('payment_line_id', '=', rec.id), ('state', '=', 'pending'),
            #                          ('installment_date', '>=', record.date_from), ('installment_date', '<=', record.date_to)]):
            #                     currnet_installments_ids.append(line.id)
            #         record.loan_link = currnet_installments_ids
            #         if record.input_line_ids.x_is_true:
            #             if record.input_line_ids:
            #                 record.input_line_ids = [(3, inputs.id, 0)]
            #         if x:
            #             loan_total = 0
            #             for line in record.loan_link:
            #                 record.input_line_ids = [(0, 0, {
            #                     'input_type_id': line.payment_line_id.payment_type.x_payslip_input_type.id,
            #                     'amount': line.installment_amount,
            #                     'x_is_true': True

            # for line in record.loan_link:
            #     loan_total += line.installment_amount
            # record.input_line_ids = [(0, 0, {
            #     'input_type_id': rec.payment_type.x_payslip_input_type.id,
            #     'amount': loan_total
            # =======

            # for line in record.loan_link:
            #     loan_total += line.installment_amount
            # record.input_line_ids = [(0, 0, {
            #     'input_type_id': rec.payment_type.x_payslip_input_type.id,
            #     'amount': loan_total
            # >>>>>>> master

            # 'input_type_id': self.env['hr.payslip.input.type'].search([('code', '=', 'LORP')]).id,
            # for loan in x:
            #     loan_total += loan.installment
            # self.input_line_ids = [(0, 0, {
            #     'input_type_id': self.env['hr.payslip.input.type'].search([('code', '=', 'LORP')]).id,
            #     'amount': loan_total

            # def recompute_loan_amount(self):
            #     self.onchange_loan()
            #     x = self.env['hr.loan'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'open')])
            #     # currnet_installments_ids = []
            #     # if x:
            #     #     for rec in x:
            #     #         currnet_installments_ids.append(
            #     #             self.env['loan.payment.line'].search([('payment_line_id', '=', rec.id), ('state', '=', 'pending')],
            #     #                                                  limit=1, order='installment_date asc').id)
            #     # self.loan_link = currnet_installments_ids
            #     if self.input_line_ids:
            #         inputs = self.env['hr.payslip.input'].search(
            #             [('payslip_id', '=', self.id), ('input_type_id.code', '=', 'LORP')])
            #         for input in inputs:
            #             self.input_line_ids = [(3, input.id, 0)]
            #     if x:
            #         loan_total = 0
            #         for loan in x:
            #             loan_total += loan.installment
            #         self.input_line_ids = [(0, 0, {
            #             'input_type_id': self.env['hr.payslip.input.type'].search([('code', '=', 'LORP')]).id,
            #             'amount': loan_total
            #         })]
            #

    def compute_sheet(self):
        self.onchange_loan()
        res = super(hr_payslip, self).compute_sheet()
        return res


class HrPayslipInputInherit(models.Model):
    _inherit = 'hr.payslip.input'
    x_is_true = fields.Boolean(string="Is True")
