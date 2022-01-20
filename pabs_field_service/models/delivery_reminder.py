from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class DeliveryReminder(models.TransientModel):
    _inherit = 'delivery.reminder'

    def _compute_remaining_tasks(self):
        # delivery = self._context.get('delivery')
        # so_delivery_id = self.env['stock.picking'].search([('id', '=', delivery)]).sale_id.id
        sale_id = self._context.get('sale_id')
        print(sale_id, 'so_delivery_ids')
        tasks = self.env['project.task'].search([('sale_order_id.id', '=', sale_id), ('x_business_line', '!=', False), ('x_slot', '=', False), ('fsm_done', '=', False)])
        print(tasks, 'TASKS')
        return tasks

    x_task = fields.Many2many('project.task', string="Remaining Tasks", default=_compute_remaining_tasks)

    def action_view_field_service_gantt_from_reminder(self):
        # self.ensure_one()
        print('action_view_field_service_gantt_from_reminder')
        sale_id = self._context.get('sale_id')

        task_ids = self.env['project.task'].search([('sale_order_id', '=', sale_id), ('x_slot', '=', False)])
        business = []
        # print(delivery_ids, 'del')
        print(sale_id, 'sale')
        # print(delivery)
        for t in task_ids:
            if t.project_id.business_line:
                business.append(t.business_line.id)
        show = []
        for rec in self.env['field.plan.calendar'].search([]):
            # if rec.business_line.id in business:
            if rec.status == 'available' and rec.business_line.id in business:
                show.append(rec.id)
            elif rec.status == 'booked' and rec.x_task.sale_order_id.id == sale_id:
                show.append(rec.id)
        print(business)
        return {
            'name': _('Field Service Calendar'),
            'res_model': 'field.plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_field_service.field_plan_calendar_gantt_view_sale').id, 'gantt'),
            ],
            'context': {"active_model": 'sale.order', "active_id": sale_id},
            'domain': [('id', 'in', show)],
            'type': 'ir.actions.act_window',
        }