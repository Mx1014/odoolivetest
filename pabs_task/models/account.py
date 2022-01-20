from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.tools.float_utils import float_compare


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_so_line = fields.Many2one('sale.order.line', string='Sales Order Item',
                                domain="[('is_expense', '=', False),('state', 'in', ['sale', 'done'])]")
    x_customer_id = fields.Many2one('res.partner', string="Customer")
    x_dn_amount_due = fields.Monetary(string="Amount Due", related="purchase_line_id.x_delivery_order.x_total_amount")
    #x_bill_complete_date = fields.Date(related='purchase_line_id.x_task_id.x_complete_date')
    #x_invoice_complete_date = fields.Date(related='x_so_line.x_completion_date')

    @api.onchange('x_customer_id')
    def _so_line_domain_by_customer(self):
        res = {}
        so_line = 0

        task = self.env['project.task']
        for line in self:
            so_line = task.search(
                [('sale_line_id', '!=', False), ('partner_id', '=', line.x_customer_id.id)]).sale_line_id.ids
            if line.move_id.type not in ['out_invoice', 'out_refund']:
                res['domain'] = {'x_so_line': [('id', 'in', so_line)]}
        return res

    @api.onchange('product_id', 'x_so_line')
    def _so_line_domain(self):
        res = {}
        so_line = 0

        task = self.env['project.task']
        for line in self:
            so_line = task.search(
                [('sale_line_id', '!=', False), ('partner_id', '=', line.move_id.partner_id.id)]).sale_line_id.ids
            if line.move_id.type not in ['in_invoice', 'in_refund']:
                res['domain'] = {'x_so_line': [('id', 'in', so_line)]}
        return res

    # def _prepare_analytic_line(self):
    #     res = super(AccountMoveLine, self)._prepare_analytic_line()
    #     i = 0
    #     for line in res:
    #         line['so_line'] = self[i].x_so_line.id or False
    #         i = i + 1
    #
    #     return res
    #
    # def _prepare_analytic_distribution_line(self, distribution):
    #     res = super(AccountMoveLine, self)._prepare_analytic_distribution_line(distribution)
    #     i = 0
    #     for line in res:
    #         if self.x_so_line.id:
    #           line['so_line'] = self[i].x_so_line.id or False
    #           i = i + 1
    #     return res


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_dn_delivered = fields.Many2many('purchase.order.line', string="Auto-Complete Line")
    done_dn = fields.Many2many('stock.picking', string="Auto-Complete GRN")
    partner_account_move_lines = fields.Many2many('account.move.line')

    @api.onchange('partner_id', 'x_dn_delivered', 'invoice_line_ids')
    def x_dn_delivered_domain(self):
        res = {}
        # res['domain'] = {'x_dn_delivered': [('partner_id', '=', self.partner_id.id), ('x_delivery_order', '!=', False), ('id', 'not in', self.invoice_line_ids.mapped('purchase_line_id').ids),('order_id.state', 'not in', ['cancel', 'draft'])]}
        if not self.partner_id.x_is_subcontractor:
            res['domain'] = {'x_dn_delivered': [('partner_id', '=', self.partner_id.id), ('x_delivery_order', '!=', False), ('id', 'not in', self.invoice_line_ids.mapped('purchase_line_id').ids)]}
        else:
            res['domain'] = {'x_dn_delivered': [('partner_id', '=', self.partner_id.id), ('id', 'not in', self.invoice_line_ids.mapped('purchase_line_id').ids)]}
    """
    @api.onchange('partner_id')
    def x_account_lines_domain(self):
        #res = {}
      if self.partner_id: 
        ids = self.env['account.move.line'].search([('partner_id', '=', self.partner_id.id), ('exclude_from_invoice_tab', '=', False), ('move_id.type', 'in', ['in_invoice', 'in_refund']), ('parent_state', '!=', 'cancel')])
        self.partner_account_move_lines = ids
        #return res
                """

    @api.onchange('partner_id', 'done_dn', 'invoice_line_ids')
    def x_done_dn_domain(self):
        res = {}
        if self.type == 'in_invoice':
            res['domain'] = {
                'done_dn': [('partner_id', '=', self.partner_id.id), ('state', '=', 'done'), ('code', '=', 'incoming'),
                            ('name', 'not in', self.invoice_line_ids.mapped('delivery_note_name')),
                            ('name', 'not in', self.partner_account_move_lines.mapped('delivery_note_name'))]}
        elif self.type == 'in_refund':
            res['domain'] = {
                'done_dn': [('partner_id', '=', self.partner_id.id), ('state', '=', 'done'), ('code', '=', 'outgoing'),
                            ('name', 'not in', self.invoice_line_ids.mapped('delivery_note_name')),
                            ('name', 'not in', self.partner_account_move_lines.mapped('delivery_note_name'))]}
        return res

    @api.onchange('partner_id')
    def purchase_vendor_bill_id_domain(self):
        res = {}
        purchase_order = self.env['purchase.order'].search(
            [('partner_id', '=', self.partner_id.id),
             ('invoice_status', '!=', 'invoiced')]).ids
        bill = self.env['account.move'].search(
            [('partner_id', '=', self.partner_id.id), ('type', '=', 'in_invoice')]).ids
        union = self.env['purchase.bill.union'].search(
            ['|', ('purchase_order_id', 'in', purchase_order), ('vendor_bill_id', 'in', bill)]).ids
        res['domain'] = {'purchase_vendor_bill_id': [('id', 'in', union)]}
        return res

    @api.onchange('x_dn_delivered')
    def _onchange_purchase_auto_complete_custom(self):
        po_lines = self.env['purchase.order.line'].search([('id', 'in', self.x_dn_delivered.ids)])
        new_lines = self.env['account.move.line']
        for line in po_lines.filtered(lambda l: not l.display_type):
            new_line = new_lines.new(line._prepare_account_move_line(self))
            new_line.account_id = new_line._get_computed_account()
            new_line._onchange_price_subtotal()
            print(new_line.move_id)
            new_line.move_id._onchange_invoice_line_ids()
            new_lines += new_line
            new_line._onchange_mark_recompute_taxes()
            new_line._onchange_currency()
            new_line.move_id._onchange_currency()

        # Compute invoice_origin.
        origins = set(self.line_ids.mapped('purchase_line_id.order_id.name'))
        self.invoice_origin = ','.join(list(origins))

        # Compute ref.
        refs = set(self.line_ids.mapped('purchase_line_id.order_id.partner_ref'))
        refs = [ref for ref in refs if ref]
        self.ref = ','.join(refs)

        # Compute _invoice_payment_ref.
        if len(refs) == 1:
            self._invoice_payment_ref = refs[0]

        self.x_dn_delivered = False


    @api.onchange('done_dn')
    def _onchange_done_dn_auto_complete_custom(self):
        move = self.env['stock.move.line'].search(
            [('picking_id', 'in', self.done_dn.ids)])

        po_lines = self.env['purchase.order.line'].search(
            [('id', 'in', move.move_id.purchase_line_id.ids)])

        # ('id', 'not in', self.invoice_line_ids.mapped('purchase_line_id').ids)

        new_lines = self.env['account.move.line']

        for line in po_lines:
            new_line = new_lines.new(line._prepare_account_move_line_edit(self, self.done_dn.mapped('name')))
            new_line.account_id = new_line._get_computed_account()
            new_line._onchange_price_subtotal()
            new_line.move_id._onchange_invoice_line_ids()
            new_lines += new_line
            new_line._onchange_mark_recompute_taxes()
            new_line._onchange_currency()
            new_line.move_id._onchange_currency()

        # Compute invoice_origin.
        origins = set(self.line_ids.mapped('purchase_line_id.order_id.name'))
        self.invoice_origin = ','.join(list(origins))

        # Compute ref.
        refs = set(self.line_ids.mapped('purchase_line_id.order_id.partner_ref'))
        refs = [ref for ref in refs if ref]
        self.ref = ','.join(refs)

        # Compute _invoice_payment_ref.
        if len(refs) == 1:
            self._invoice_payment_ref = refs[0]

        self.done_dn = False


#
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


class PurchaseBillUnion(models.Model):
    _inherit = 'purchase.bill.union'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        print(name)
        if name:
            domain = ['|', '|', ('name', operator, name), ('reference', operator, name), ('purchase_order_id.x_batch_ids', operator, name)]
        purchase_vendor_bill_id = self._search(expression.AND([domain, args]), limit=limit,
                                               access_rights_uid=name_get_uid)
        return self.browse(purchase_vendor_bill_id).name_get()


class inoviceLineIdEdit(models.Model):
    _inherit = 'account.move.line'

    delivery_note_name = fields.Char(string='D.N')
