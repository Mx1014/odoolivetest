from odoo import models, fields, api, _


class PlanningSlot(models.Model):
    _inherit = 'planning.slot'

    x_date_begin =  fields.Datetime(related="task_id.planned_date_begin")
    x_date_end = fields.Datetime(related="task_id.planned_date_end")
    x_dead_line = fields.Date(related="task_id.date_deadline")
    x_customer_id = fields.Many2one('res.partner', string="Customer")
    x_is_from_sale = fields.Boolean(default=False)
    x_tasks_ids = fields.Many2many('project.task', string='Tasks associated to sale')
    #x_planned_hours = fields.Float(compute="_allocated_hours_task_plan", store=True)

    # @api.onchange('project_id')
    # def planning_task_field_domain(self):
    #     res = {}
    #     if self.x_is_from_sale:
    #         project = self.x_tasks_ids.project_id.ids
    #         print(project)
    #         res['domain'] = {'project_id': [('id', 'in', project)], 'task_id': [('id', 'in', self.x_tasks_ids.ids)]}
    #     return res

    @api.onchange('x_customer_id')
    def onchange_filter_project(self):
        res = {}

        project = self.env['project.task'].search([('partner_id', '=', self.x_customer_id.id)]).mapped('project_id')
        res['domain'] = {'project_id': [('id', 'in', project.ids)]}
        return res

    @api.onchange('project_id')
    def onchange_project_id(self):
        res = {}
        task_project = self.env['project.task'].search(
            [('partner_id', '=', self.x_customer_id.id), ('project_id', '=', self.project_id.id)])
        res['domain'] = {'task_id': [('id', 'in', task_project.ids)]}
        return res

    #@api.onchange('start_datetime', 'end_datetime', 'allocated_hours')
    # def allocated_hours_task_plan(self):
    #     global hours
    #     for task in self:
    #         #task.task_id.planned_hours = 0.0
    #         if task.task_id:
    #             task.x_planned_hours = task.allocated_hours
    #             hours = hours + task.allocated_hours
    #             task.task_id.planned_hours += task.allocated_hours
    #         else:
    #             task.x_planned_hours = 0.0
    #     if self.task_id:
    #         self.task_id.planned_hours = hours

    # @api.depends('start_datetime', 'end_datetime', 'employee_id.resource_calendar_id', 'allocated_percentage')
    # def _allocated_hours_task_plan(self):
    #     plan = self.env['planning.slot'].search([('', '', )])
    #     for slot in self:
    #         if slot.start_datetime and slot.end_datetime and slot.task_id:
    #             percentage = slot.allocated_percentage / 100.0 or 1
    #             if slot.allocation_type == 'planning' and slot.start_datetime and slot.end_datetime:
    #                 slot.task_id.planned_hours += (slot.end_datetime - slot.start_datetime).total_seconds() * percentage / 3600.0
    #                 slot.x_planned_hours = 0.0
    #             else:
    #                 if slot.employee_id:
    #                     slot.task_id.planned_hours += \
    #                     slot.employee_id._get_work_days_data(slot.start_datetime, slot.end_datetime, compute_leaves=True)[
    #                         'hours'] * percentage
    #                     slot.x_planned_hours = 0.0
    #                 else:
    #                     slot.x_planned_hours = 0.0

