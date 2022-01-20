from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_pending_so_ids = fields.Many2many('sale.order', string="Open Sales Ordres", compute="_get_open_so")
    x_order_due = fields.Monetary(string="Order Due")
    x_total_balance = fields.Monetary(string="Total Balance", compute="_get_open_so")

    def _get_open_so(self):
        sales = self.env['sale.order'].search([('partner_id', '=', self.id), ('invoice_status', '!=', 'invoiced'), ('state', 'in', ['sale', 'done'])])
        # invoices = self.env['account.move'].search([('partner_id', '=', self.id), ('amount_residual', '!=', 0.0), ('state', '!=', 'cancel')])
        for sale in sales:
            if sale.x_amount_not_invoiced != 0.0:
                self.x_pending_so_ids = [(4, sale.id)]
        self.x_order_due = sum(self.x_pending_so_ids.mapped('x_amount_not_invoiced'))
        self.x_total_balance = self.total_balance_vals() + self.x_order_due




    def total_balance_vals(self):

        partner = self.env['res.partner'].browse(self.id) or False
        if not partner:
            return 0

        res = {}
        today = fields.Date.today()
        total_val = 0.0
        for l in partner.unreconciled_aml_ids.filtered(lambda l: l.company_id == self.env.company):
            if l.company_id == self.env.company:
                if self.env.context.get('print_mode') and l.blocked:
                    continue
                currency = l.currency_id or l.company_id.currency_id
                if currency not in res:
                    res[currency] = []
                res[currency].append(l)
        for currency, aml_recs in res.items():
            total = 0
            total_issued = 0
            for aml in aml_recs:
                amount = aml.amount_residual_currency if aml.currency_id else aml.amount_residual
                total += not aml.blocked and amount or 0
                # is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                # is_payment = aml.payment_id
                # if is_overdue or is_payment:
                #     total_issued += not aml.blocked and amount or 0
            total_val = total

        return total_val



