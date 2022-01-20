from odoo import models, fields, _


class CreateTaskCrm(models.TransientModel):
    _name = 'crm.create.fsm.task'
    _description = 'Create a Field Service task'

    x_crm_id = fields.Many2one('crm.lead', string='Related CRM ticket', required=True)
    name = fields.Char('Title', required=True)
    project_id = fields.Many2one('project.project', string='Project', help='Project in which to create the task', required=True, domain=[('is_fsm', '=', True)])
    partner_id = fields.Many2one('res.partner', string='Customer', help="Ticket's customer, will be linked to the task", required=True)

    def action_generate_task(self):
        self.ensure_one()
        values = self._prepare_values()
        new_task = self.env['project.task'].create(self._convert_to_write(values))
        return new_task

    def action_generate_and_return_to_ticket(self):
        self.ensure_one()
        new_task = self.action_generate_task()
        business_line_id = self.env['project.task'].search([('id', '=', new_task.id)]).x_business_line.id
        return {
            'name': _('Field Service Calendar'),
            'res_model': 'field.plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_field_service.field_plan_calendar_gantt_view_crm_ticket').id, 'gantt'),
            ],
            'target': 'new',
            'context': {'business_line': business_line_id, 'task_id': new_task.id},
            'domain': [('status', '=', 'available'), ('business_line', '=', business_line_id),
                       ('start_datetime', '>=', fields.Date.today())],
            'type': 'ir.actions.act_window',
        }

    def action_generate_and_view_task(self):
        self.ensure_one()
        new_task = self.action_generate_task()
        business_line_id = self.env['project.task'].search([('id', '=', new_task.id)]).x_business_line.id
        return {
            'name': _('Field Service Calendar'),
            'res_model': 'field.plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_field_service.field_plan_calendar_gantt_view_task').id, 'gantt'),
            ],
            'target': 'new',
            'context': {'business_line': business_line_id, 'task_id': new_task.id},
            'domain': [('status', '=', 'available'), ('business_line', '=', business_line_id),
                       ('start_datetime', '>=', fields.Date.today())],
            'type': 'ir.actions.act_window',
        }

    def _prepare_values(self, values={}):
        prepared_values = dict(values)
        for fname in ['x_crm_id', 'name', 'project_id', 'partner_id']:
            prepared_values[fname] = self[fname]
        return prepared_values

    # def action_generate_and_view_task(self):
    #     self.ensure_one()
    #     new_task = self.action_generate_task()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': _('Tasks from CRM'),
    #         'res_model': 'project.task',
    #         'res_id': new_task.id,
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('industry_fsm.project_task_view_form').id,
    #         'context': {
    #             'fsm_mode': True,
    #         }
    #     }


