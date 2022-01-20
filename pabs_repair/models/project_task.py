from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ProjectTask(models.Model):
    _inherit = 'project.task'

    x_repair_id = fields.Many2one('repair.order', string="Repair Order", copy=False)
    x_date_start = fields.Datetime(related="x_repair_id.repair_date", store=True)
    x_technician = fields.Many2one('hr.employee', related="x_repair_id.technician", store=True)
    x_product_id = fields.Many2one('product.product', string="Product", related='helpdesk_ticket_id.product_id',
                                   store=True)

    def action_repair_form_view(self):
        self.ensure_one()
        return {
            'name': _('Repair From Task'),
            'res_model': 'repair.order',
            'res_id': self.x_repair_id.id,
            'view_mode': 'form',
            'views': [
                (self.env.ref('repair.view_repair_order_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window'}

    def unlink(self):
        if self.sale_order_id and self.helpdesk_ticket_id:
            raise UserError('Cannot delete a task')
        if self.sale_order_id or self.x_batch_id:
            raise UserError('Cannot delete a task')
        return super(ProjectTask, self).unlink()




    def action_fsm_validate(self):
        result = super(ProjectTask, self).action_fsm_validate()
        sale = self.sale_order_id
        if sale.picking_ids and self.project_id.id == 14:
            # if 'assigned' in sale.picking_ids.mapped('state'):
            #     sale.picking_ids.button_validate()
            #     wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, sale.picking_ids.id)]})
            #     wiz.process()
            for delivery in sale.picking_ids:
                if 'confirmed' or 'waiting' in delivery.mapped('state'):
                    for move in delivery.move_ids_without_package.filtered(
                            lambda x: x.reserved_availability == 0.0):
                        delivery.move_line_ids_without_package = [(0, 0, {
                            'product_id': move.product_id.id,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            # 'product_uom_qty': move.product_uom_qty,
                            'origin': move.origin,
                            'picking_id': delivery.id,
                            'reference': delivery.name,
                            'company_id': delivery.company_id.id,
                            'product_uom_id': move.product_uom.id,
                            'qty_done': move.product_uom_qty,
                        })]
                        # sale.picking_ids.move_line_ids_without_package[-1].product_uom_qty = move.product_uom_qty
                delivery.button_validate()
                wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, delivery.id)]})
                wiz.process()
        return result

    def _validate_stock(self):
        return

    def action_field_plan_calendar_shift_task_wizards(self):
        self.ensure_one()
        return {
            'name': _('Field Service Calendar'),
            'res_model': 'field.plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_field_service.shift_field_plan_calendar_gantt_view_task').id, 'gantt'),
            ],
            'target': 'new',
            'context': {'business_line': self.x_business_line.id, 'slot_id': self.x_slot.id, 'task_id': self.id},
            'domain': [('business_line', '=', self.x_business_line.id), ('status', '=', 'available')],
            'type': 'ir.actions.act_window',
        }

    def action_task_reschedule_form_view(self):
        return {
            'name': _('Task'),
            'res_model': 'task.reschedule',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'context': {'default_name': self.id},
            'target': 'new'
        }


class TaskReschedule(models.TransientModel):
    _name = 'task.reschedule'
    _description = "Task Reschedule"

    name = fields.Many2one('project.task', string="Task")

    def reschedule_task(self):
        return self.name.action_field_plan_calendar_shift_task_wizards()

    def done_task(self):
        self.name.action_fsm_validate()
