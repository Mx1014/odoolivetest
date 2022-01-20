from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date, parse_date

class BankStatementLineWidget(models.AbstractModel):
    _inherit = 'account.reconciliation.widget'

    @api.model
    def get_move_lines_for_bank_statement_line(self, st_line_id, partner_id=None, auth_code=None, benefit_pay=None,excluded_ids=None, search_str=False,offset=0, limit=None, mode=None):
        st_line = self.env['account.bank.statement.line'].browse(st_line_id)

        # Blue lines = payment on bank account not assigned to a statement yet
        aml_accounts = [
            st_line.journal_id.default_credit_account_id.id,
            st_line.journal_id.default_debit_account_id.id
            ]

        if partner_id is None:
            partner_id = st_line.partner_id.id

        print(excluded_ids, 'sssssssssssssssssssssss')
        domain = self._domain_move_lines_for_reconciliation(st_line, aml_accounts, partner_id,
                                                            excluded_ids=excluded_ids, search_str=search_str, mode=mode)
        recs_count = self.env['account.move.line'].search_count(domain)

        from_clause, where_clause, where_clause_params = self.env['account.move.line']._where_calc(domain).get_sql()
        if auth_code:
            where_clause += " and account_move_line.payment_id = (select id from account_payment where x_auth='"+auth_code+"') "
            recs_count = 1
        elif benefit_pay:
            where_clause += " and account_move_line.payment_id = (select id from account_payment where x_benefit_ref='" + benefit_pay + "') "
            recs_count = 1
        #limit = None
        query_str = '''
                SELECT "account_move_line".id FROM {from_clause}
                {where_str}
                ORDER BY ("account_move_line".debit - "account_move_line".credit) = {amount} DESC,
                    "account_move_line".date_maturity ASC,
                    "account_move_line".id ASC
                {limit_str}
            '''.format(
            from_clause=from_clause,
            where_str=where_clause and (" WHERE %s" % where_clause) or '',
            amount=st_line.amount,
            limit_str=limit and ' LIMIT %s' or '',
            )
        params = where_clause_params + (limit and [limit] or [])
        self.env['account.move'].flush()
        self.env['account.move.line'].flush()
        self.env['account.bank.statement'].flush()
        self._cr.execute(query_str, params)
        res = self._cr.fetchall()

        aml_recs = self.env['account.move.line'].browse([i[0] for i in res])
        target_currency = st_line.currency_id or st_line.journal_id.currency_id or st_line.journal_id.company_id.currency_id
        return self._prepare_move_lines(aml_recs, target_currency=target_currency, target_date=st_line.date, auth_code=auth_code, benefit_pay=benefit_pay, recs_count=recs_count)

    @api.model
    def _prepare_move_lines(self, move_lines, target_currency=False, target_date=False, auth_code=None, benefit_pay=None, recs_count=0):
        res = super(BankStatementLineWidget, self)._prepare_move_lines(move_lines, target_currency, target_date, recs_count)
        for i in range(len(res)):
            res[i]['x_auth'] = (move_lines[i].payment_id.x_auth if move_lines[i].payment_id else '')
            res[i]['x_benefit_ref'] = (move_lines[i].payment_id.x_benefit_ref if move_lines[i].payment_id else '')
        return res

    @api.model
    def _get_statement_line(self, st_line):
        partner_id = False
        partner_name = False
        if not st_line.partner_id:
            if st_line.x_auth:
                payment = self.env['account.payment'].search(
                    [('x_auth', '=', st_line.x_auth), ('state', 'not in', ['draft', 'reconciled'])], limit=1)
                if payment:
                    partner_id = payment.partner_id.id
                    partner_name = payment.partner_id.name
            elif st_line.x_benefit_pay_ref:
                payment = self.env['account.payment'].search(
                    [('x_benefit_ref', '=', st_line.x_benefit_pay_ref), ('state', 'not in', ['draft', 'cancelled'])],limit=1)
                if payment:
                    partner_id = payment.partner_id.id
                    partner_name = payment.partner_id.name
        else:
            partner_id = st_line.partner_id.id
            partner_name = st_line.partner_id.name

        res = super(BankStatementLineWidget, self)._get_statement_line(st_line)
        res['partner_id'] = partner_id
        res['partner_name'] = partner_name
        res['x_auth'] = st_line.x_auth
        res['x_benefit_pay_ref'] = st_line.x_benefit_pay_ref
        return res

class ReconcileModel(models.Model):
    _inherit = 'account.reconcile.model'

    match_auth_code = fields.Boolean(string='Auth Code Is Set',
                                     help='The reconciliation model will only be applied when a customer/vendor is set.')
    match_auth_codes = fields.Char(string='Restrict Auth Code to',
                                   help='The reconciliation model will only be applied to the selected customers/vendors.')

    match_benefit_pay_ref = fields.Boolean(string='BenefitPAy Ref. Is Set',
                                           help='The reconciliation model will only be applied when a customer/vendor is set.')
    match_benefit_pay_refs = fields.Char(string='Restrict BenefitPAy Ref. to',
                                         help='The reconciliation model will only be applied to the selected customers/vendors.')

class BankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    x_auth = fields.Char(string="Auth Code")
    x_benefit_pay_ref = fields.Char(string="BenefitPay Ref")

class AuthReconcileAccountPayment(models.Model):
    _inherit = "account.payment"

    def get_partnerid_by_auth(self):
        payment = self.env['account.payment'].search([('x_auth', '=', self.id), ('state', 'not in', ['draft','cancelled'])],limit=1)
        if payment:
            return {
                'partner_id': {
                    'id': payment.partner_id.id,
                    'display_name': payment.partner_id.display_name,
                    },
                'property_account_payable_id': payment.partner_id.property_account_payable_id.id,
                'property_account_receivable_id': payment.partner_id.property_account_receivable_id.id
                }
        else:
            return "Not Found"

    def get_partnerid_by_benefit(self):
        payment = self.env['account.payment'].search([('x_benefit_ref', '=', self.id), ('state', 'not in', ['draft','cancelled'])],limit=1)
        if payment:
            return {
                'partner_id': {
                    'id': payment.partner_id.id,
                    'display_name': payment.partner_id.display_name,
                    },
                'property_account_payable_id': payment.partner_id.property_account_payable_id.id,
                'property_account_receivable_id': payment.partner_id.property_account_receivable_id.id
                }
        else:
            return "Not Found"