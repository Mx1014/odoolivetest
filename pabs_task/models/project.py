from odoo import models, fields, api, _
from datetime import datetime, timedelta, date


class ProjectTask(models.Model):
    _inherit = 'project.task'

    x_subcontract = fields.Many2one('res.partner', string="Subcontractor")
    x_purchase_order = fields.Many2one('purchase.order', string='Purchase Order')
    x_product_uom_qty = fields.Float(related='sale_line_id.product_uom_qty')
    x_qty_delivered = fields.Float(related='sale_line_id.qty_delivered')
    x_qty_invoiced = fields.Float(related='sale_line_id.qty_invoiced')
    x_complete_date = fields.Date(string="Completion Date")
    x_schedule_date = fields.Date(string="Schedule Date")
    x_stage_closed = fields.Boolean(related='stage_id.is_closed')
    x_so_delivery_state = fields.Selection(related="sale_order_id.delivery_state")
    date_deadline = fields.Date(string='Deadline', index=True, copy=False, tracking=True)
    # x_planned_hours = fields.Float(compute="_allocated_hours_task_plan")

    def action_view_delivery(self):
        return self.sale_order_id.action_view_delivery()

    # @api.depends('start_datetime', 'end_datetime', 'employee_id.resource_calendar_id', 'allocated_percentage')
    # def _allocated_hours_task_plan(self):
    #     hours = 0.0
    #     plan = self.env['planning.slot'].search([('task_id', '=', self.id)])
    #     for slot in plan:
    #         hours += slot.allocated_hours
    #     self.planned_hours = hours
    #     self.x_planned_hours = hours
    # for slot in self:
    #     if slot.start_datetime and slot.end_datetime and slot.task_id:
    #         percentage = slot.allocated_percentage / 100.0 or 1
    #         if slot.allocation_type == 'planning' and slot.start_datetime and slot.end_datetime:
    #             slot.task_id.planned_hours += (slot.end_datetime - slot.start_datetime).total_seconds() * percentage / 3600.0
    #             slot.x_planned_hours = 0.0
    #         else:
    #             if slot.employee_id:
    #                 slot.task_id.planned_hours += \
    #                 slot.employee_id._get_work_days_data(slot.start_datetime, slot.end_datetime, compute_leaves=True)[
    #                     'hours'] * percentage
    #                 slot.x_planned_hours = 0.0
    #             else:
    #                 slot.x_planned_hours = 0.0

    @api.onchange('stage_id')
    def delivered_qty_done(self):
        for task in self:
            if task.stage_id.name == 'Completed':
                task.sale_line_id.qty_delivered = task.sale_line_id.product_uom_qty

    def action_create_po(self):
        data = {}
        for task in self:
            data = {
                'partner_id': task.x_subcontract.id,
                'fiscal_position_id': task.x_subcontract.property_account_position_id.id,
                'origin': task.sale_line_id.order_id.name,
                'partner_ref': task.sale_line_id.order_id.name,
                'x_sale_order': task.sale_line_id.order_id.id,
                'dest_address_id': task.partner_id.id,
                'order_line': [(0, 0, {
                    'product_id': task.sale_line_id.product_id.id,
                    'name': task.sale_line_id.product_id.name,
                    'x_so_line': task.sale_line_id.id,
                    'x_customer_id': task.partner_id.id,
                    'x_task_id': task.id,
                    'product_qty': task.sale_line_id.product_uom_qty,
                    'price_unit': 1,
                    'date_planned': task.date_deadline,
                    'product_uom': task.sale_line_id.product_uom.id,
                })]
            }

        for vendor in task.sale_line_id.product_id.mapped('seller_ids'):
            if vendor.name.id == data['partner_id']:
                data['order_line'][0][2]['price_unit'] = vendor.price
        self.x_purchase_order = self.env['purchase.order'].create(data)
        self.x_purchase_order._compute_tax_id()
        return self.action_view_po()

    def action_view_po(self):
        self.ensure_one()
        return {
            'name': _('Purchase'),
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'views': [
                (self.env.ref('purchase.purchase_order_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'res_id': self.x_purchase_order.id,
        }

    # @api.depends('planned_date_end')
    # def onchange_date_deadline(self):
    #     for task in self:
    #         if task.planned_date_end:
    #             task.date_deadline = task.planned_date_end + timedelta(days=2)
    #         # if task.planned_date_begin and task.planned_date_end:
    #         #     date_begin = task.planned_date_begin
    #         #     date_end = task.planned_date_end
    #         #     no_of_days = (date_end - date_begin).days
    #         #     task.planned_hours = no_of_days * 24
    #         else:
    #             task.date_deadline = False
