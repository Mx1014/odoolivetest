from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class PayLoanLines(models.Model):
    _name = 'pay.loan.lines'

    def domain_loan_lines(self):
        context_loan = self._context.get('active_id')
        loan_lines = self.env['loan.payment.line'].search(
            [('payment_line_id', '=', context_loan), ('state', '!=', 'paid')]).ids
        return [('id', 'in', loan_lines)]

    x_loan_id = fields.Many2one('hr.loan', string="Loan", tracking=True)
    x_loan_line_ids = fields.Many2many('loan.payment.line', string="Installment", domain=domain_loan_lines,
                                       tracking=True)
    x_amount = fields.Monetary(string="Amount")
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency")
    company_id = fields.Many2one('res.company', string='Company', store=True, readonly=True,
                                 default=lambda self: self.env.company)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, tracking=True)

    @api.onchange('x_loan_line_ids')
    def _onchnage_x_loan_line_ids(self):
        if self.x_loan_line_ids:
            self.x_amount = sum(self.x_loan_line_ids.mapped('installment_unpaid'))

    def create_journal_entry(self):
        debit_vals = {
            'name': self.x_loan_id.name,
            'debit': abs(self.x_amount),
            'credit': 0.0,
            'account_id': self.journal_id.default_debit_account_id.id,
        }
        credit_vals = {
            'name': self.x_loan_id.name,
            'debit': 0.0,
            'credit': abs(self.x_amount),
            'account_id': self.journal_id.default_credit_account_id.id,
        }
        vals = {
            'date': self.x_loan_id.date,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'ref': self.x_loan_id.name,
            'type': 'entry',
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
        }
        move = self.env['account.move'].create(vals)
        move.post()
        for rec in self:
            rec.x_loan_id.discounted_loan_line_ids = [
                (0, 0, {'discounted_line_id': rec.id, 'zero_loan_lines_move_id': move.id})]
        # self.x_loan_id.zero_loan_lines_move_id = move
        payment_amount = self.x_amount
        for loan in self.mapped('x_loan_line_ids'):
            if payment_amount >= loan.installment_unpaid:
                payment_amount = payment_amount - loan.installment_unpaid
                loan.installment_unpaid = 0
                loan.state = 'paid'
            else:
                loan.installment_unpaid = loan.installment_unpaid - payment_amount
                payment_amount = 0
                loan.state = 'partial'


class DiscountedLoanLines(models.Model):
    _name = 'discounted.loan.lines'
    discounted_line_id = fields.Many2one('hr.loan', 'ID', track_visibility='onchange')
    zero_loan_lines_move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)
