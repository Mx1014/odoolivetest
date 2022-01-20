from odoo import models, fields, api, _


class SalesTerminal(models.Model):
    _inherit = 'account.user.statement'

    is_receivable = fields.Boolean(string="Is Receivable", default=False)

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def post(self):
        res = super(AccountPayment, self).post()
        receivable_session_id = self.env['account.user.statement'].search(
            [('user_id', '=', self.env.user.id), ('state', '=', 'open'), ('is_receivable', '!=', False), ('date', '=', fields.Date.today())])
        invoice = self.env['account.move'].search([('id', '=', self._context.get('active_id'))])
        if receivable_session_id and invoice.type in ['in_invoice', 'in_refund']:
            vals = {
                'name': invoice.name + "," + receivable_session_id.name,
                'statement_id': receivable_session_id.id,
                'journal_id': self.journal_id.id,
                'date': self.payment_date,
                'amount': self.amount,
                'transaction_type': self.payment_type,
                'partner_id': self.partner_id.id,
                'note': self.communication,
                'cheque_date': self.cheque_date,
                'cheque_number': self.cheque_number,
                'bank_id': self.bank_id.id,
                'account_number': self.account_number,
                'cheque_type': self.x_cheque_type,
                'auth': self.x_auth,
                'tid': self.x_tid.id,
                'batch': self.x_batch,
                'benefit_ref': self.x_benefit_ref,
                'payment_id': self.id,
            }
            if self.payment_type == 'outbound':
                vals['amount'] = -vals['amount']

            receivable_session_id.write({'user_statement_line_ids': [(0, 0, vals)]})

        return res

class AccountUserStatement(models.Model):
    _inherit = 'account.user.statement'

    bills_count = fields.Integer('Invoices', compute='_compute_bills_count')
    refund_count = fields.Integer('Refund', compute='_compute_refund_count')


    def _compute_bills_count(self):
        for statement in self:
            statement.bills_count = self.env['account.move'].search_count([('user_statement_id', '=', statement.id), ('type', '=', 'in_invoice')])

    def _compute_refund_count(self):
        for statement in self:
            statement.refund_count = self.env['account.move'].search_count(
                [('user_statement_id', '=', statement.id), ('type', '=', 'in_refund')])

    def action_view_bills(self):
        self.ensure_one()
        return {
            'name': _('Bills'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_invoice_tree').id, 'tree'),
                (self.env.ref('account.view_move_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('user_statement_id', '=', self.id), ('type', '=', 'in_invoice')],
        }

    def action_view_vendor_credit(self):
        self.ensure_one()
        return {
            'name': _('Refund'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_invoice_tree').id, 'tree'),
                (self.env.ref('account.view_move_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('user_statement_id', '=', self.id), ('type', '=', 'in_refund')],
        }