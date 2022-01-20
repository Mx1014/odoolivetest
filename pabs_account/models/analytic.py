from odoo import models, fields, api, _


class AccountAnaltic(models.Model):
    _inherit = 'account.analytic.default'

    x_sale_team = fields.Many2one('crm.team', string="Sales Team")
    x_vehicle = fields.Many2one('fleet.vehicle', string="Vehicle")

    @api.model
    def account_get(self, product_id=None, partner_id=None, account_id=None, user_id=None, date=None, company_id=None,
                    x_vehicle=None, x_sale_team=None):
        domain = []
        if product_id:
            domain += ['|', ('product_id', '=', product_id)]
        domain += [('product_id', '=', False)]
        if partner_id:
            domain += ['|', ('partner_id', '=', partner_id)]
        domain += [('partner_id', '=', False)]
        if account_id:
            domain += ['|', ('account_id', '=', account_id)]
        domain += [('account_id', '=', False)]
        if company_id:
            domain += ['|', ('company_id', '=', company_id)]
        domain += [('company_id', '=', False)]
        if user_id:
            domain += ['|', ('user_id', '=', user_id)]
        domain += [('user_id', '=', False)]
        if x_vehicle:
            domain += ['|', ('x_vehicle', '=', x_vehicle)]
        domain += [('x_vehicle', '=', False)]
        if x_sale_team:
            domain += ['|', ('x_sale_team', '=', x_sale_team)]
        domain += [('x_sale_team', '=', False)]
        if date:
            domain += ['|', ('date_start', '<=', date), ('date_start', '=', False)]
            domain += ['|', ('date_stop', '>=', date), ('date_stop', '=', False)]
        best_index = -1
        res = self.env['account.analytic.default']
        for rec in self.search(domain):
            index = 0
            if rec.product_id: index += 1
            if rec.partner_id: index += 1
            if rec.account_id: index += 1
            if rec.company_id: index += 1
            if rec.user_id: index += 1
            if rec.x_vehicle: index += 1 
            if rec.x_sale_team: index += 1
            if rec.date_start: index += 1
            if rec.date_stop: index += 1
            if index > best_index:
                res = rec
                best_index = index
        return res

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    x_analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    x_total_payments = fields.Many2many('account.move', string="Total Payments")
    x_voucher_no = fields.Char(string="Voucher", readonly=True)

    # def _prepare_payment_moves(self):
    #     res = super(AccountPayment, self)._prepare_payment_moves()
    #     for res in res:
    #         if self.payment_type == 'outbound':
    #             for vals in res['line_ids']:
    #                 if vals[len(vals) - 1]['account_id'] in [self.journal_id.default_credit_account_id.id, self.journal_id.default_debit_account_id.id]:
    #                     vals[len(vals) - 1]['analytic_account_id'] = self.x_analytic_account_id.id
    #     return res
    @api.onchange('x_total_payments')
    def onchange_total_amount(self):
        if self.x_total_payments:
            self.amount = abs(sum(self.x_total_payments.mapped('amount_total_signed')))

    def generate_voucher_no(self):
        self.x_voucher_no = self.env['ir.sequence'].next_by_code('payment.voucher')
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.depends('product_id', 'account_id', 'partner_id', 'date_maturity', 'x_vehicle_id', 'move_id.team_id')
    def _compute_analytic_account(self):
        for record in self:
            rec = self.env['account.analytic.default'].account_get(
                product_id=record.product_id.id,
                partner_id=record.partner_id.commercial_partner_id.id or record.move_id.partner_id.commercial_partner_id.id,
                account_id=record.account_id.id,
                user_id=record.env.uid,
                date=record.date_maturity,
                company_id=record.move_id.company_id.id,
                x_vehicle=record.x_vehicle_id.id,
		x_sale_team=record.move_id.team_id.id,
            )
            record.analytic_account_id = (record._origin or record).analytic_account_id or rec.analytic_id
            record.analytic_tag_ids = (record._origin or record).analytic_tag_ids or rec.analytic_tag_ids
