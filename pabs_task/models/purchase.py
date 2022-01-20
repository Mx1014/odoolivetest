from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_so_line = fields.Many2one('sale.order.line', 'Sales Order Item',
                                domain="[('is_expense', '=', False),('state', 'in', ['sale', 'done'])]", copy=False)
    x_customer_id = fields.Many2one('res.partner', string="Customer")
    x_task_id = fields.Many2one('project.task', string='Task')
    x_task_stage = fields.Char(compute='depends_task_id')
    x_complete_date = fields.Date(related='x_task_id.x_complete_date')
    x_reference_order = fields.Char(related="x_task_id.sale_line_id.order_id.name")
    x_dn_amount_due = fields.Monetary(string="Amount Due", related="x_delivery_order.x_total_amount")


    @api.onchange('x_customer_id')
    def _so_line_domain(self):
        res = {}
        so_line = 0
        task = self.env['project.task']
        for line in self:
            so_line = task.search(
                [('sale_line_id', '!=', False), ('partner_id', '=', line.x_customer_id.id)]).sale_line_id.ids

        res['domain'] = {'x_so_line': [('id', 'in', so_line)]}
        return res

    @api.onchange('x_so_line')
    def _x_task_id_domain(self):
        res = {}
        domain = 0
        for line in self:
            domain = line.x_so_line.task_id.id
            line.x_task_id = line.x_so_line.task_id.id
        res['domain'] = {'x_so_line': [('id', '=', domain)]}
        return res

    @api.depends('x_task_id')
    def depends_task_id(self):
        for task in self:
            task.x_task_stage = task.x_task_id.stage_id.name
            if task.x_task_id.stage_id.name == 'Completed':
                task.qty_received = task.product_qty

    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        res['x_so_line'] = self.x_so_line.id
        res['x_customer_id'] = self.x_customer_id.id
        res['delivery_note_name'] = self.x_delivery_order.name
        print(res)
        return res

    def _prepare_account_move_line_edit(self, move, name):
        #self.ensure_one()
        if self.product_id.purchase_method == 'purchase':
            qty = self.product_qty - self.qty_invoiced
        else:
            qty = self.qty_received - self.qty_invoiced
        if float_compare(qty, 0.0, precision_rounding=self.product_uom.rounding) <= 0:
            qty = 0.0

        if self.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id
        for l in self.move_ids:
            if l.picking_id.name in name:
                return {
                    'name': '%s: %s' % (self.order_id.name, self.name),
                    'move_id': move.id,
                    'currency_id': currency and currency.id or False,
                    'purchase_line_id': self.id,
                    'date_maturity': move.invoice_date_due,
                    'product_uom_id': self.product_uom.id,
                    'product_id': self.product_id.id,
                    'price_unit': self.price_unit,
                    'quantity': l.product_uom_qty,
                    'partner_id': move.partner_id.id,
                    'analytic_account_id': self.account_analytic_id.id,
                    'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
                    'tax_ids': [(6, 0, self.taxes_id.ids)],
                    'display_type': self.display_type,
                    'delivery_note_name': l.picking_id.name,
                }




class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_task_count = fields.Integer(string='Tasks', compute='_compute_task_count')
    x_done_task = fields.Boolean(string='Complete Tasks', compute='_compute_done_task_count', store=True)
    x_source_projects = fields.Char(string="Project Reference", compute="_get_source_reference")

    def _compute_task_count(self):
        for order in self:
            order.x_task_count = self.env['purchase.order.line'].search_count(
                [('order_id', '=', order.id), ('x_task_id', '!=', False)])

    @api.depends('order_line.x_task_id.stage_id')
    def _compute_done_task_count(self):
        for order in self:
            completed_task = self.env['purchase.order.line'].search_count(
                [('order_id', '=', order.id), ('x_task_id.stage_id.name', '=', 'Completed')])
            if order.x_task_count == completed_task:
                order.x_done_task = True
            else:
                order.x_done_task = False
            if order.x_task_count == 0:
                order.x_done_task = True

    def action_view_task(self):
        self.ensure_one()
        line = self.env['purchase.order.line'].search([('order_id', '=', self.id)]).x_task_id.ids
        return {
            'name': _('Task'),
            'res_model': 'project.task',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('project.view_task_tree2').id, 'tree'),
                (self.env.ref('project.view_task_form2').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', line)],
        }

    @api.depends('order_line.x_reference_order')
    def _get_source_reference(self):
        for purchase in self:
            if not purchase.order_line:
                purchase.x_source_projects = False
            for task in purchase.order_line:
                if len(purchase.order_line) == 1 and task.x_task_id and task.x_task_id.sale_line_id:
                    purchase.x_source_projects = task.x_task_id.sale_line_id.order_id.name
                elif len(purchase.order_line) > 1 and task.x_task_id and task.x_task_id.sale_line_id:
                    purchase.x_source_projects = '%s,' % task.x_task_id.sale_line_id.order_id.name
                else:
                    purchase.x_source_projects = False
