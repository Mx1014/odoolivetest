# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import email_split, float_is_zero
from datetime import datetime

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    x_created_expense = fields.Boolean(default=False, compute="get_true_created_from_expense", store=True)
    x_attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    x_is_expense = fields.Boolean(default=False)
    x_total_expense = fields.Float()
    x_payment_type = fields.Selection([('cash', 'Cash'), ('bank', 'Bank')], string="Paid By")
    x_expense_state = fields.Selection([('pending', 'Pending'), ('reported', 'Reported')], string="Expense State", compute="depends_expense_state")
    x_expense_sheet_id = fields.Many2one('hr.expense.sheet', string="Expense")
    x_cheque_date = fields.Date(string='Cheque Date')
    x_cheque_number = fields.Char(string='Cheque Number')
    x_bank_id = fields.Many2one('res.bank', string='Bank Account')
    x_account_number = fields.Char(string='Bank Account Number')

    # @api.depends('amount')
    # def get_amountd(self):
    #     if self.amount == 0.0 and self.x_total_expense != 0.0:
    #         self.amount = self.x_total_expense
    #         self.x_total_expense = self.amount

    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([
            ('res_model', '=', 'account.payment'),
            ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for doc in self:
            doc.x_attachment_number = attachment.get(doc.id, 0)

    # @api.depends("partner_id")
    # def get_true_created_from_expense(self):
    #     active_model = self._context.get('active_model')
    #     print(self._name)
    #     for payment in self:
    #         if active_model == 'hr.expense' and payment.id:
    #             payment.x_created_expense = True

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'account.payment'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'account.payment', 'default_res_id': self.id}
        return res

    def action_submit_expenses(self):
        # if any(expense.state != 'draft' or expense.sheet_id for expense in self):
        #     raise UserError(_("You cannot report twice the same line!"))
        # if len(self.mapped('employee_id')) != 1:
        #     raise UserError(_("You cannot report expenses for different employees in the same report."))
        # if any(not expense.product_id for expense in self):
        #     raise UserError(_("You can not create report without product."))
        date = []

        todo = self.filtered(lambda x: x.partner_type == 'supplier')
        if self.env['hr.expense.sheet'].search([('x_payment_ids', 'in', todo.ids)]):
            raise UserError(_("You cannot report twice the same payment!"))
        for pay in todo:
            date.append(pay.payment_date)

        print(datetime.strftime(min(date), '%m/%d/%Y'))
        return {
            'name': _('New Expense Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'context': {
                'default_x_payment_ids': todo.ids,
                'default_company_id': self.company_id.id,
                #'default_employee_id': self[0].employee_id.id,
                'default_name': 'Expense Report- From %s To %s' % (datetime.strftime(min(date), '%m/%d'), datetime.strftime(max(date), '%m/%d')),
            }
        }

    
    def depends_expense_state(self):
        for payment in self:
            if payment.env['hr.expense.sheet'].search([('x_payment_ids', 'in', payment.id)]):
               payment.x_expense_state = 'reported'
            else:
               payment.x_expense_state = 'pending'

    def post(self):
        res = super(AccountPayment, self).post()
        statement_line_val = []
        statement_id = False
        if self.x_total_expense != 0.0:


            for payment in self.x_expense_sheet_id.mapped('x_payment_ids'):
                statement_line_vals = []
                print(self.env['ir.default'].sudo().get('hr.expense.sheet', 'x_ownwer_journal'))
                if not self.env['account.bank.statement'].search([('journal_id', '=', self.env['ir.default'].sudo().get('hr.expense.sheet', 'x_ownwer_journal'))]):
                    val = {
                        # 'name': '%s/%s' %(self.name, user_statement.name),
                        'name': self.x_expense_sheet_id.name,
                        'journal_type': 'bank',
                        'journal_id': self.env['ir.default'].sudo().get('hr.expense.sheet', 'x_ownwer_journal'),
                        'date': fields.Date.today(),
                        # 'statement_for_pabs': True,
                        'balance_start': 0.0,
                    }
                    statement_id = self.env['account.bank.statement'].create(val)
                else:
                    statement_id = self.env['account.bank.statement'].search([('journal_id', '=', self.env['ir.default'].sudo().get('hr.expense.sheet', 'x_ownwer_journal'))], limit=1, order="id desc")

                if statement_id:
                    vals = {
                        'name': payment.journal_id.name,
                        'statement_id': statement_id.id,
                        'journal_id': payment.journal_id.id,
                        'date': payment.payment_date,
                        'amount': -payment.amount,
                        # 'note': '',
                        # 'transaction_type': '',
                        'ref': payment.name,
                        #'user_id': self.env.user.id,
                    }
                    statement_line_vals.append((0, 0, vals))
                    statement_id.write({'line_ids': statement_line_vals})
                    self.x_expense_sheet_id.x_bank_statement_id = statement_id.id

            statement = self.env['account.bank.statement'].search([('journal_id', '=', self.destination_journal_id.id), ('state', '=', 'open')], limit=1, order="id desc")
            if statement:
                vals = {
                    'name': 'Payment Transfer',
                    'statement_id': statement.id,
                    'journal_id': self.destination_journal_id.id,
                    'date': self.payment_date,
                    'amount': self.amount,
                    # 'note': '',
                    # 'transaction_type': '',
                    'ref': self.name,
                    'user_id': self.env.user.id,
                }
                statement_line_val.append((0, 0, vals))
                statement.write({'line_ids': statement_line_val})
                self.x_expense_sheet_id.state = 'done'
                if self.move_line_ids:
                    self.x_expense_sheet_id.account_move_id = self.move_line_ids[0].move_id.id

        return res

    @api.model
    def default_get(self, default_fields):
        rec = super(AccountPayment, self).default_get(default_fields)
        if self._context.get('default_x_is_expense') and self._context.get('default_payment_type') == 'outbound':
            rec.update({
               'journal_id': self.env['ir.default'].sudo().get('hr.expense.sheet', 'x_ownwer_journal'),
            })
        return rec













class HrExpenseLine(models.Model):
    _name = 'hr.expense.line'
    _description = 'Hr Expense Line'

    @api.model
    def _default_account_id(self):
        return self.env['ir.property'].get('property_account_expense_categ_id', 'product.category')

    name = fields.Char(string='Label')
    expense_name = fields.Char(string='Number', related='expense_id.name', store=True, index=True)
    expense_id = fields.Many2one('hr.expense', string="Expenses")
    # move_id = fields.Many2one('account.move', string='Journal Entry',
    #                           index=True, required=True, readonly=True, auto_join=True, ondelete="cascade",
    #                           help="The move of this entry line.")
    # date = fields.Date(related='move_id.date', store=True, readonly=True, index=True, copy=False, group_operator='min')
    # ref = fields.Char(related='move_id.ref', store=True, copy=False, index=True, readonly=False)
    # parent_state = fields.Selection(related='move_id.state', store=True, readonly=True)
    # journal_id = fields.Many2one(related='move_id.journal_id', store=True, index=True, copy=False)
    company_id = fields.Many2one(related='expense_id.company_id', store=True, readonly=True)
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
                                          readonly=True, store=True,
                                          help='Utility field to express amount currency')
    country_id = fields.Many2one(comodel_name='res.country', related='company_id.country_id')
    account_id = fields.Many2one('account.account', string='Account', default=_default_account_id,
                                 index=True, ondelete="cascade",
                                 domain=[('deprecated', '=', False)])
    account_internal_type = fields.Selection(related='account_id.user_type_id.type', string="Internal Type", store=True,
                                             readonly=True)
    account_root_id = fields.Many2one(related='account_id.root_id', string="Account Root", store=True, readonly=True)
    sequence = fields.Integer(default=10)
    quantity = fields.Float(string='Quantity',
                            default=1.0, digits='Product Unit of Measure',
                            help="The optional quantity expressed by this line, eg: number of product sold. "
                                 "The quantity is not a legal requirement but is very useful for some reports.")
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    debit = fields.Monetary(string='Debit', default=0.0, currency_field='company_currency_id')
    credit = fields.Monetary(string='Credit', default=0.0, currency_field='company_currency_id')
    balance = fields.Monetary(string='Balance', store=True,
                              currency_field='company_currency_id',
                              compute='_compute_balance',
                              help="Technical field holding the debit - credit in order to open meaningful graph views from reports")
    amount_currency = fields.Monetary(string='Amount in Currency', store=True, copy=True,
                                      help="The amount expressed in an optional other currency if it is a multi-currency entry.")
    price_subtotal = fields.Monetary(string='Subtotal', store=True, readonly=True,
                                     currency_field='always_set_currency_id', compute="_compute_amount")
    price_total = fields.Monetary(string='Total', store=True, readonly=True,
                                  currency_field='always_set_currency_id', compute="_compute_amount")
    #reconciled = fields.Boolean(compute='_amount_residual', store=True)
    #blocked = fields.Boolean(string='No Follow-up', default=False,help="You can check this box to mark this journal item as a litigation with the associated partner")
    # date_maturity = fields.Date(string='Due Date', index=True,
    #                             help="This field is used for payable and receivable journal entries. You can put the limit date for the payment of this line.")
    currency_id = fields.Many2one('res.currency', string='Currency')
    partner_id = fields.Many2one('res.partner', string='Partner', ondelete='restrict')
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    product_id = fields.Many2one('product.product', string='Product')

    # ==== Origin fields ====
    # reconcile_model_id = fields.Many2one('account.reconcile.model', string="Reconciliation Model", copy=False,
    #                                      readonly=True)
    # payment_id = fields.Many2one('account.payment', string="Originator Payment", copy=False,
    #                              help="Payment that created this entry")
    # statement_line_id = fields.Many2one('account.bank.statement.line',
    #                                     string='Bank statement line reconciled with this entry',
    #                                     index=True, copy=False, readonly=True)
    # statement_id = fields.Many2one(related='statement_line_id.statement_id', store=True, index=True, copy=False,
    #                                help="The bank statement used for bank reconciliation")

    # ==== Tax fields ====
    tax_ids = fields.Many2many('account.tax', string='Taxes', help="Taxes that apply on the base amount")
    tax_line_id = fields.Many2one('account.tax', string='Originator Tax', ondelete='restrict', store=True,
                                  help="Indicates that this journal item is a tax line")
    tax_group_id = fields.Many2one(related='tax_line_id.tax_group_id', string='Originator tax group',
                                   readonly=True, store=True,
                                   help='technical field for widget tax-group-custom-field')
    tax_base_amount = fields.Monetary(string="Base Amount", store=True, readonly=True,
                                      currency_field='company_currency_id')
    tax_exigible = fields.Boolean(string='Appears in VAT report', default=True, readonly=True,
                                  help="Technical field used to mark a tax line as exigible in the vat report or not (only exigible journal items"
                                       " are displayed). By default all new journal items are directly exigible, but with the feature cash_basis"
                                       " on taxes, some will become exigible only when the payment is recorded.")
    tax_repartition_line_id = fields.Many2one(comodel_name='account.tax.repartition.line',
                                              string="Originator Tax Repartition Line", ondelete='restrict',
                                              readonly=True,
                                              help="Tax repartition line that caused the creation of this move line, if any")
    tag_ids = fields.Many2many(string="Tags", comodel_name='account.account.tag', ondelete='restrict',
                               help="Tags assigned to this line by the tax creating it, if any. It determines its impact on financial reports.")
    # tax_audit = fields.Char(string="Tax Audit String", compute="_compute_tax_audit", store=True,
    #                         help="Computed field, listing the tax grids impacted by this line, and the amount it applies to each of them.")

    # ==== Reconciliation fields ====
    # amount_residual = fields.Monetary(string='Residual Amount', store=True,
    #                                   currency_field='company_currency_id',
    #                                   compute='_amount_residual',
    #                                   help="The residual amount on a journal item expressed in the company currency.")
    # amount_residual_currency = fields.Monetary(string='Residual Amount in Currency', store=True,
    #                                            compute='_amount_residual',
    #                                            help="The residual amount on a journal item expressed in its currency (possibly not the company currency).")
    # full_reconcile_id = fields.Many2one('account.full.reconcile', string="Matching #", copy=False, index=True,
    #                                     readonly=True)
    # matched_debit_ids = fields.One2many('account.partial.reconcile', 'credit_move_id', string='Matched Debits',
    #                                     help='Debit journal items that are matched with this journal item.',
    #                                     readonly=True)
    # matched_credit_ids = fields.One2many('account.partial.reconcile', 'debit_move_id', string='Matched Credits',
    #                                      help='Credit journal items that are matched with this journal item.',
    #                                      readonly=True)

    # ==== Analytic fields ====
    # analytic_line_ids = fields.One2many('account.analytic.line', 'move_id', string='Analytic lines')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    # ==== Onchange / display purpose fields ====
    recompute_tax_line = fields.Boolean(store=False, readonly=True,
                                        help="Technical field used to know on which lines the taxes must be recomputed.")
    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note'),
    ], default=False, help="Technical field for UX purpose.")
    # is_rounding_line = fields.Boolean(help="Technical field used to retrieve the cash rounding line.")
    # exclude_from_invoice_tab = fields.Boolean(
    #     help="Technical field used to exclude some lines from the invoice_line_ids tab in the form view.")
    always_set_currency_id = fields.Many2one('res.currency', string='Foreign Currency',
                                             compute='_compute_always_set_currency_id',
                                             help="Technical field used to compute the monetary field. As currency_id is not a required field, we need to use either the foreign currency, either the company one.")

    @api.depends('currency_id')
    def _compute_always_set_currency_id(self):
        for line in self:
            line.always_set_currency_id = line.currency_id or line.company_currency_id

    @api.onchange('product_id', 'company_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.name:
                self.name = self.product_id.display_name or ''
            self.price_unit = self.product_id.price_compute('standard_price')[self.product_id.id]
            self.product_uom_id = self.product_id.uom_id
            self.tax_ids = self.product_id.supplier_taxes_id.filtered(
                lambda tax: tax.company_id == self.company_id)  # taxes only from the same company
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if account:
                self.account_id = account

    @api.depends('quantity', 'price_unit', 'price_subtotal', 'tax_ids')
    def _compute_amount(self):
        for expense in self:

            taxes = expense.tax_ids.compute_all(expense.price_unit, expense.currency_id, expense.quantity,
                                                expense.product_id, expense.expense_id.x_partner_id)

            expense.price_subtotal = expense.price_unit * expense.quantity
            expense.price_total = taxes.get('total_included')