from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def domain_loan_lines(self):
        context_loan = self._context.get('active_id')
        loan_lines = self.env['loan.payment.line'].search(
            [('payment_line_id', '=', context_loan), ('state', '!=', 'paid')]).ids
        return [('id', 'in', loan_lines)]

    x_loan_id = fields.Many2one('hr.loan', string="Loan")
    x_loan_line_ids = fields.Many2many('loan.payment.line', string="Installment", domain=domain_loan_lines)

    @api.onchange('x_loan_line_ids')
    def _onchnage_x_loan_line_ids(self):
        if self.x_loan_line_ids:
            self.amount = sum(self.x_loan_line_ids.mapped('installment_unpaid'))

    def installment_payment_register(self):
        receivable_session_id = self.env['account.user.statement'].search(
            [('user_id', '=', self.env.user.id), ('state', '=', 'open'), ('is_receivable', '!=', False),
             ('date', '=', fields.Date.today())])
        if not receivable_session_id:
            raise UserError(
                _("Please start a Session via Receivable Terminal as you can't create payment without a session opened."))
        #loan = self.env['account.move'].search([('id', '=', self._context.get('active_id'))])
        if receivable_session_id:
            self.update({
                'payment_method_id': self.payment_method_id.id,
                'communication': self.x_loan_id.name + "," + receivable_session_id.name,
                'payment_type': 'inbound',
                'amount': abs(self.amount),
                'currency_id': self.currency_id.id,
                'partner_id': self._context.get('employee'),
                'partner_type': 'customer',
            })
            vals = {
                'name': self.x_loan_id.name + "," + receivable_session_id.name,
                'statement_id': receivable_session_id.id,
                'journal_id': self.journal_id.id,
                'date': self.payment_date,
                'amount': self.amount,
                'transaction_type': self.payment_type,
                'partner_id': self.partner_id.id,
                'note': self.communication,
                # 'cheque_date': self.cheque_date,
                # 'cheque_number': self.cheque_number,
                # 'bank_id': self.bank_id.id,
                # 'account_number': self.account_number,
                # 'cheque_type': self.x_cheque_type,
                # 'auth': self.x_auth,
                # 'tid': self.x_tid.id,
                # 'batch': self.x_batch,
                # 'benefit_ref': self.x_benefit_ref,
                'payment_id': self.id,
            }
            receivable_session_id.write({'user_statement_line_ids': [(0, 0, vals)]})
            payment_amount = self.amount
            for loan in self.mapped('x_loan_line_ids'):
                if payment_amount >= loan.installment_unpaid:
                    payment_amount = payment_amount - loan.installment_unpaid
                    loan.installment_unpaid = 0
                    loan.state = 'paid'
                else:
                    loan.installment_unpaid = loan.installment_unpaid - payment_amount
                    payment_amount = 0
                    loan.state = 'partial'
