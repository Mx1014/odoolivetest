from odoo import models, fields, api, _
from odoo.osv import expression

# class AccountMoveLine(models.Model):
#     _inherit = 'account.move.line'
#
#     x_so_line = fields.Many2one('sale.order.line', string='Sales Order Item',
#                                 domain="[('is_expense', '=', False),('state', 'in', ['sale', 'done'])]")
#     x_customer_id = fields.Many2one('res.partner', string="Customer")
#     x_bill_complete_date = fields.Date(related='purchase_line_id.x_task_id.x_complete_date')
#     x_invoice_complete_date = fields.Date(related='x_so_line.x_completion_date')
#
#     @api.onchange('x_customer_id')
#     def _so_line_domain_by_customer(self):
#         res = {}
#         so_line = 0
#
#         task = self.env['project.task']
#         for line in self:
#             so_line = task.search(
#                 [('sale_line_id', '!=', False), ('partner_id', '=', line.x_customer_id.id)]).sale_line_id.ids
#             if line.move_id.type not in ['out_invoice', 'out_refund']:
#                 res['domain'] = {'x_so_line': [('id', 'in', so_line)]}
#         return res
#
#
#
#     @api.onchange('product_id', 'x_so_line')
#     def _so_line_domain(self):
#         res = {}
#         so_line = 0
#
#         task = self.env['project.task']
#         for line in self:
#            so_line = task.search(
#                 [('sale_line_id', '!=', False), ('partner_id', '=', line.move_id.partner_id.id)]).sale_line_id.ids
#            if line.move_id.type not in ['in_invoice', 'in_refund']:
#               res['domain'] = {'x_so_line': [('id', 'in', so_line)]}
#         return res
#
#     def _prepare_analytic_line(self):
#         res = super(AccountMoveLine, self)._prepare_analytic_line()
#         i = 0
#         for line in res:
#             line['so_line'] = self[i].x_so_line.id or False
#             i = i + 1
#
#         return res
#
#     def _prepare_analytic_distribution_line(self, distribution):
#         res = super(AccountMoveLine, self)._prepare_analytic_distribution_line(distribution)
#         i = 0
#         for line in res:
#             if self.x_so_line.id:
#               line['so_line'] = self[i].x_so_line.id or False
#               i = i + 1
#         return res
#

class AccountMove(models.Model):
    _inherit = 'account.move'

    # x_total_paid = fields.Monetary(string='Paid', compute="paid_get")
    x_completion_journal = fields.Many2one('account.journal', string="Completion Certificate")
    x_down_payment_journal = fields.Many2one('account.journal', string="Advance Payment")
    x_receivable = fields.Boolean()
    x_payable = fields.Boolean()
    x_sale_id = fields.Many2one('sale.order', srting="Sales")

    # def paid_get(self):
    #     for move in self:
    #         move.x_total_paid = move.amount_total_signed - move.amount_residual_signed

    # @api.onchange('partner_id')
    # def purchase_vendor_bill_id_domain(self):
    #     res = {}
    #     purchase_order = self.env['purchase.order'].search(
    #         [('partner_id', '=', self.partner_id.id), ('x_done_task', '!=', False), ('invoice_status', '!=', 'invoiced')]).ids
    #     bill = self.env['account.move'].search(
    #         [('partner_id', '=', self.partner_id.id), ('type', '=', 'in_invoice')]).ids
    #     union = self.env['purchase.bill.union'].search(['|',('purchase_order_id', 'in', purchase_order), ('vendor_bill_id', 'in', bill)]).ids
    #     res['domain'] = {'purchase_vendor_bill_id': [('id', 'in', union)]}
    #     return res






# class AccountPayment(models.Model):
#     _inherit = 'account.payment'
#     # _order = 'payment_date asc'
#
#     x_quote_total = fields.Monetary(string='Quote Total')
#     x_balance_total = fields.Monetary(string='Balance')
#     x_amount_in_sale = fields.Monetary(string="Amount Paid")

    # def total_quote_get(self):
    #     for payment in self:
    #         for invoice in payment.invoice_ids:
    #             print(invoice.name)
    #         order = self.env['sale.order'].search([('invoice_ids', '=', self.invoice_ids)])
    #         print(order.ids)
    #         for order in order:
    #             self.x_quote_total = order.amount_total


# class AccountAnalyticLine(models.Model):
#     _inherit = 'account.analytic.line'
#
#     @api.onchange('partner_id')
#     def onchange_filter_project(self):
#         res = {}
#
#         project = self.env['project.task'].search([('partner_id','=', self.partner_id.id)]).mapped('project_id')
#         res['domain'] = {'project_id': [('id','in', project.ids)]}
#         return res
#
#     @api.onchange('project_id')
#     def onchange_project_id(self):
#         res = {}
#         task_project = self.env['project.task'].search([('partner_id','=', self.partner_id.id), ('project_id', '=', self.project_id.id)])
#         res['domain'] = {'task_id': [('id', 'in', task_project.ids)]}
#         return res
#
#
# class PurchaseBillUnion(models.Model):
#     _inherit = 'purchase.bill.union'
#
#     @api.model
#     def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
#         args = args or []
#         domain = []
#         print(name)
#         if name:
#             domain = ['|', ('name', operator, name), ('reference', operator, name)]
#         purchase_vendor_bill_id = self._search(expression.AND([domain, args]), limit=limit,
#                                                access_rights_uid=name_get_uid)
#         return self.browse(purchase_vendor_bill_id).name_get()

