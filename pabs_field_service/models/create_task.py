from odoo import models, fields, _


class CreateTask(models.TransientModel):
    _inherit = 'helpdesk.create.fsm.task'

    # def action_generate_task(self):
    #     self.ensure_one()
    #     values = self._prepare_values()
    #     new_task = self.env['project.task'].create(self._convert_to_write(values))
    #     return new_task

    def action_generate_task(self):
        res = super(CreateTask, self).action_generate_task()
        comeback = self.env.ref('pabs_repair.comeback').id
        res.x_warranty_state = self.helpdesk_ticket_id.warranty_status
        if self.helpdesk_ticket_id.ticket_type_id.id == comeback:
            res.x_invoice_method = 'warranty'
            res.x_invoice_partner_id = self.helpdesk_ticket_id.company_id.partner_id
        else:
            if self.helpdesk_ticket_id.warranty_status == 'Running':
                res.x_invoice_method = 'warranty'
                res.x_invoice_partner_id = self.helpdesk_ticket_id.brand_agent
            elif self.helpdesk_ticket_id.warranty_status == 'Extended':
                res.x_invoice_method = 'warranty'
                res.x_invoice_partner_id = self.helpdesk_ticket_id.warranty_sequence.x_warranty_agent
            else:
                res.x_invoice_method = 'after_sale'
                res.x_invoice_partner_id = self.helpdesk_ticket_id.partner_id
        return res

    def action_generate_and_return_to_ticket(self):
        self.ensure_one()
        new_task = self.action_generate_task()
        business_line_id = self.env['project.task'].search([('id', '=', new_task.id)]).x_business_line.id
        return {
            'name': _('Field Service Calendar'),
            'res_model': 'field.plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_field_service.field_plan_calendar_gantt_view_helpdesk_ticket').id, 'gantt'),
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
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': _('Tasks from Tickets'),
        #     'res_model': 'project.task',
        #     'res_id': new_task.id,
        #     'view_mode': 'form',
        #     'view_id': self.env.ref('industry_fsm.project_task_view_form').id,
        #     'context': {
        #         'fsm_mode': True,
        #     }
        # }
