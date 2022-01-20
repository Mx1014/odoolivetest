# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details

from odoo import models, api, fields, _


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    x_visit_sheet = fields.Many2one('project.task.batch', related='fsm_task_ids.x_batch_id', store=True)
    x_task_businessline = fields.Many2one('business.line', related='fsm_task_ids.x_business_line', store=True)

    def action_generate_fsm_task(self):
        res = super(HelpdeskTicket, self).action_generate_fsm_task()
        res['context']['default_name'] = self.display_name
        res['context']['default_project_id'] = self.x_product_id.x_service_category.project_id.id
        return res
        # self.ensure_one()
        # default_project_id = False
        # fsm_projects = self.env['project.project'].search([('is_fsm', '=', True)], limit=2)
        # if (len(fsm_projects) == 1):
        #     default_project_id = fsm_projects.id
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': _('Create a Field Service task'),
        #     'res_model': 'helpdesk.create.fsm.task',
        #     'view_mode': 'form',
        #     'target': 'new',
        #     'context': {
        #         'default_helpdesk_ticket_id': self.id,
        #         'default_partner_id': self.partner_id.id if self.partner_id else False,
        #         'default_name': self.name,
        #         'default_project_id': default_project_id,
        #     }
        # }
