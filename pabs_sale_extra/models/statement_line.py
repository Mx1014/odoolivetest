
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, Warning



class AccountBankStatementLine(models.Model):
    _name = "account.user.statement.line"
    _description = "User Statement Line"
    #_order = "statement_id desc, date, sequence, id desc"

    name = fields.Char(string='Label', required=True)
    date = fields.Date(required=True, default=lambda self: self._context.get('date', fields.Date.context_today(self)))
    amount = fields.Monetary(currency_field='journal_currency_id')
    journal_currency_id = fields.Many2one('res.currency', string="Journal's Currency", related='statement_id.currency_id',
        help='Utility field to express amount currency', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    account_number = fields.Char(string='Bank Account Number', help="Technical field used to store the bank account number before its creation, upon the line's processing")
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account', help="Bank account that was used in this transaction.")
    account_id = fields.Many2one('account.account', string='Counterpart Account', domain=[('deprecated', '=', False)],
        help="This technical field can be used at the statement line creation/import time in order to avoid the reconciliation"
             " process on it later on. The statement line will simply create a counterpart on this account")
    statement_id = fields.Many2one('account.user.statement', string='Statement', index=True, ondelete='cascade')
    journal_id = fields.Many2one('account.journal', string='Journal', store=True, readonly=True) # related field
    bank_type = fields.Selection(related="journal_id.x_bank_type")
    partner_name = fields.Char(help="This field is used to record the third party name when importing bank statement in electronic format,"
             " when the partner doesn't exist yet in the database (or cannot be found).")
    ref = fields.Char(string='Reference')
    note = fields.Text(string='Notes')
    transaction_type = fields.Char(string='Transaction Type')
    sequence = fields.Integer(index=True, help="Gives the sequence order when displaying a list of bank statement lines.", default=1)
    company_id = fields.Many2one('res.company', related='statement_id.company_id', string='Company', store=True, readonly=True)
    journal_entry_ids = fields.One2many('account.move.line', 'statement_line_id', 'Journal Items', copy=False, readonly=True)
    amount_currency = fields.Monetary(help="The amount expressed in an optional other currency if it is a multi-currency entry.")
    currency_id = fields.Many2one('res.currency', string='Currency', help="The optional other currency if it is a multi-currency entry.")
    state = fields.Selection(related='statement_id.state', string='Status', readonly=True)
    move_name = fields.Char(string='Journal Entry Name', readonly=True,
        default=False, copy=False,
        help="Technical field holding the number given to the journal entry, automatically set when the statement line is reconciled then stored to set the same number again if the line is cancelled, set to draft and re-processed again.")

    cheque_date = fields.Date(string='Cheque Date')
    cheque_number = fields.Char(string='Cheque Number')
    bank_id = fields.Many2one('res.bank', string='Bank Account')
    account_number = fields.Char(string='Bank Account Number')
    cheque_type = fields.Selection(related='payment_id.x_cheque_related_type', string="Cheque Type")
    auth = fields.Char(string="Auth Code")
    tid = fields.Many2one('bank.card.readers', string="TID")
    batch = fields.Char(string="Batch")
    voucher_payment_id = fields.Many2one('account.payment', string="Voucher Payment")
    benefit_ref = fields.Char(string="BenefitPay Ref")
    payment_id = fields.Many2one('account.payment', string="Payment Ref")

    # @api.constrains('amount')
    # def _check_amount(self):
    #     for line in self:
    #         # Allow to enter bank statement line with an amount of 0,
    #         # so that user can enter/import the exact bank statement they have received from their bank in Odoo
    #         currency = line.currency_id or line.journal_currency_id
    #         if line.journal_id.type != 'bank' and currency.is_zero(line.amount):
    #             raise ValidationError(_('The amount of a cash transaction cannot be 0.'))
    #
    # @api.constrains('amount', 'amount_currency')
    # def _check_amount_currency(self):
    #     for line in self:
    #         if line.amount_currency != 0 and line.amount == 0:
    #             raise ValidationError(_('If "Amount Currency" is specified, then "Amount" must be as well.'))
    #
    # @api.constrains('currency_id', 'journal_id')
    # def _check_currency_id(self):
    #     for line in self:
    #         if not line.currency_id:
    #             continue
    #
    #         statement_currency = line.journal_id.currency_id or line.company_id.currency_id
    #         if line.currency_id == statement_currency:
    #             raise ValidationError(_('The currency of the bank statement line must be different than the statement currency.'))