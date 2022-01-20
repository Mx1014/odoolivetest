from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
from datetime import datetime, timedelta
from functools import partial
from itertools import groupby


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_so_line = fields.Many2many('sale.order.line')
    x_purchase_count = fields.Integer('Purchase Order', compute='_compute_purchase_count')
    #order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines', compute="filter_order_line", states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)


    # def filter_order_line(self):
    #     for order in self:
    #         res = self.env['sale.order.line'].search([('order_id', '=', order.id), ('is_downpayment', '=', False)])
    #         order.order_line = res

    # def all_same(self, item):
    #     return all(x == item[0] for x in item)



    def action_view_analytic(self):
        self.ensure_one()
        line = self.env['sale.order.line'].search([('order_id', '=', self.id)])
        return {
            'name': _('Costs & Revenues'),
            'res_model': 'account.analytic.line',
            'view_mode': 'tree,form,pivot,graph',
            'views': [
                (self.env.ref('analytic.view_account_analytic_line_tree').id, 'tree'),
                (self.env.ref('analytic.view_account_analytic_line_pivot').id, 'pivot'),
                (self.env.ref('analytic.view_account_analytic_line_graph').id, 'graph'),
                (self.env.ref('analytic.view_account_analytic_line_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('so_line', 'in', line.ids)],
            'context': {'search_default_group_by_so_line': 1}

        }

    def action_view_task(self):
        self.ensure_one()

        list_view_id = self.env.ref('project.view_task_tree2').id
        form_view_id = self.env.ref('project.view_task_form2').id

        action = {'type': 'ir.actions.act_window_close'}

        task_projects = self.tasks_ids.mapped('project_id')
        if len(task_projects) == 1 and len(self.tasks_ids) > 1:  # redirect to task of the project (with kanban stage, ...)
            action = self.with_context(active_id=task_projects.id).env.ref(
                'project.act_project_project_2_project_task_all').read()[0]
            if action.get('context'):
                eval_context = self.env['ir.actions.actions']._get_eval_context()
                eval_context.update({'active_id': task_projects.id})
                action['context'] = safe_eval(action['context'], eval_context)
        else:
            action = self.env.ref('project.action_view_task').read()[0]
            action['context'] = {}  # erase default context to avoid default filter
            if len(self.tasks_ids) > 1:  # cross project kanban task
                action['views'] = [[False, 'kanban'], [list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'calendar'], [False, 'pivot'],[False, 'gantt']]
            elif len(self.tasks_ids) == 1:  # single task -> form view
                action['views'] = [(form_view_id, 'form')]
                action['res_id'] = self.tasks_ids.id
        # filter on the task of the current SO
        action.setdefault('context', {})
        action['context'].update({'search_default_sale_order_id': self.id})
        return action

    # def action_view_profitability_report(self):
    #     self.ensure_one()
    #     line = self.env['sale.order.line'].search([('order_id', '=', self.id)])
    #     return {
    #         'name': _('Costs & Revenues'),
    #         'res_model': 'project.profitability.report',
    #         'view_mode': 'tree,pivot',
    #         'views': [
    #             (self.env.ref('pabs_contact.project_profitability_report_view_list').id, 'tree'),
    #             (self.env.ref('sale_timesheet.project_profitability_report_view_pivot').id, 'pivot'),
    #         ],
    #         'type': 'ir.actions.act_window',
    #         'search_view_id': [self.env.ref('sale_timesheet.project_profitability_report_view_search').id, 'search'],
    #         'domain': [('sale_order_id', 'in', line.ids)],
    #     }

    # def action_view_sale_cost_report(self):
    #     self.ensure_one()
    #     line = self.env['sale.order.line'].search([('order_id', '=', self.id)])
    #     return {
    #         'name': _('Costs & Revenues'),
    #         'res_model': 'sale.order.cost',
    #         'view_mode': 'tree,pivot',
    #         'views': [
    #             (self.env.ref('pabs_contact.sale_order_line_cost_view_list').id, 'tree'),
    #             (self.env.ref('pabs_contact.sale_order_line_cost_view_pivot').id, 'pivot'),
    #         ],
    #         'type': 'ir.actions.act_window',
    #         'domain': [('x_sale_order_line', 'in', line.ids)],
    #     }

    def action_view_sale_task_planning(self):
        self.ensure_one()
        line = self.env['sale.order.line'].search([('order_id', '=', self.id)])
        return {
            'name': _('Planning'),
            'res_model': 'planning.slot',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('planning.planning_view_gantt').id, 'gantt'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('order_line_id', 'in', line.ids)],
            'context': {'default_x_is_from_sale': True, 'default_x_tasks_ids': self.tasks_ids.ids}
        }


    def action_view_task_completed(self):
        self.ensure_one()
        list_view_id = self.env.ref('project.view_task_tree2').id
        form_view_id = self.env.ref('project.view_task_form2').id
        
        action = {'type': 'ir.actions.act_window_close'}
        task_projects = self.tasks_ids.mapped('project_id')

        stage = self.env['project.task.type'].search([('name', '=', 'Completed')], limit=1)
        
        action = self.env.ref('project.action_view_task').read()[0]
        action['context'] = {}
        action['views'] = [[False, 'kanban'], [list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'],
                                   [False, 'calendar'], [False, 'pivot']]
        action.setdefault('context', {})
        action['context'].update({'search_default_sale_order_id': self.id, 'search_default_stage_id': stage.id}) 
        #action['context'].update({'search_default_group_by_project_id': 1})
        return action


    def action_view_po_sale(self):
        self.ensure_one()
        print(self.mapped('order_line').ids)
        order = self.env['purchase.order.line'].search([('x_so_line', 'in', self.mapped('order_line').ids)])
        return {
            'name': _('Purchase'),
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('purchase.purchase_order_tree').id, 'tree'),
                (self.env.ref('purchase.purchase_order_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('order_line', 'in', order.ids)],
        }

    def _compute_purchase_count(self):
        for statement in self:
            order = self.env['purchase.order.line'].search([('x_so_line', 'in', self.mapped('order_line').ids)])
            statement.x_purchase_count = self.env['purchase.order'].search_count([('order_line', 'in', order.ids)])


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    
    def _prepare_invoice_line(self):
        value = super(SaleOrderLine, self)._prepare_invoice_line()
        value['x_so_line'] = self.task_id.sale_line_id.id
        return value

    # @api.onchange('qty_delivered')
    # def prepare_order_cost(self):
    #     id = self.env['sale.order.cost'].search([('x_id', '=', self[0].task_id.sale_line_id.id)])
    #     condition = id[len(id) - 1].x_qty if len(id) else 0
    #     if len(id) < self[0].product_uom_qty:
    #         if len(id) < self[0].qty_delivered:
    #             if self[0].qty_delivered <= self[0].product_uom_qty:
    #                 if self[0].qty_delivered != 0:
    #                     if condition < self[0].product_uom_qty:
    #                         data = {
    #                             'x_id': self[0].task_id.sale_line_id.id,
    #                             'x_sale_order_line': self[0].task_id.sale_line_id.id,
    #                             'x_product_id': self[0].product_id.id,
    #                             'x_task_id': self[0].task_id.id,
    #                             'name': self[0].task_id.name,
    #                             'x_project_id': self[0].task_id.project_id.id,
    #                             'x_amount_untaxed_to_invoice': self[0].price_unit * self[0].qty_delivered if self[0].qty_delivered == self[0].product_uom_qty else self[0].price_unit,
    #                             'x_qty': self[0].qty_delivered,
    #                         }
    #                         # if self[0].tax_id:
    #                         #     data[''] =
    #
    #                         self.env['sale.order.cost'].create(data)
    #
    #                 # if the delivery 2 and len 1
    #                 # price unit * qty delivered if qty 2 and delevered 1, the secand one total will be wrong
#
# class SaleOrderCost(models.Model):
#     _name = 'sale.order.cost'
#
#     name = fields.Char(string='Description')
#     x_sale_order_line = fields.Many2one('sale.order.line', string='Order Line')
#     x_project_id = fields.Many2one('project.project', string='Project', readonly=True)
#     x_task_id = fields.Many2one('project.task', string='Task', readonly=True)
#     x_currency_id = fields.Many2one('res.currency', string='Project Currency', readonly=True)
#     # cost
#     x_timesheet_unit_amount = fields.Float("Timesheet Unit Amount", digits=(16, 2), readonly=True)
#     x_timesheet_cost = fields.Float("Timesheet Cost", digits=(16, 3), readonly=True)
#     x_expense_cost = fields.Float("Other Cost", digits=(16, 2), readonly=True)
#     # sale revenue
#     x_completion_date = fields.Datetime('Completion Date', readonly=True)
#     x_product_id = fields.Many2one('product.product', string='Product', readonly=True)
#
#     x_amount_untaxed_to_invoice = fields.Float("Untaxed Amount To Invoice", digits=(16, 3), readonly=True)
#     x_amount_untaxed_invoiced = fields.Float("Untaxed Amount Invoiced", digits=(16, 3), readonly=True)
#     x_expense_amount_untaxed_to_invoice = fields.Float("Untaxed Amount to Re-invoice", digits=(16, 2), readonly=True)
#     x_expense_amount_untaxed_invoiced = fields.Float("Untaxed Re-invoiced Amount", digits=(16, 2), readonly=True)
#     x_id = fields.Integer(string="line id")
#     x_qty = fields.Integer(string="qty")
