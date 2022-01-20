import logging
from psycopg2 import sql, extras
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import email_re, email_split
from odoo.exceptions import UserError, AccessError
from odoo.addons.phone_validation.tools import phone_validation
from collections import OrderedDict


class Lead(models.Model):
    _inherit = 'crm.lead'

    fsm_task_count = fields.Integer(compute='_compute_fsm_task_count')

    def _compute_fsm_task_count(self):
        count = 0
        fsm_tasks = self.env['project.task'].search([('x_crm_id', '=', self.id)])
        if fsm_tasks:
            for task in fsm_tasks:
                count += 1

        for ticket in self:
            ticket.fsm_task_count = count

    def action_generate_fsm_task(self):
        self.ensure_one()
        default_project_id = False
        fsm_projects = self.env['project.project'].search([('is_fsm', '=', True)], limit=2)
        if(len(fsm_projects) == 1):
            default_project_id = fsm_projects.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create a Field Service task'),
            'res_model': 'crm.create.fsm.task',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_x_crm_id': self.id,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
                'default_name': self.name,
                'default_project_id': default_project_id,
            }
        }

    def action_view_fsm_tasks(self):
        fsm_form_view = self.env.ref('industry_fsm.project_task_view_form')
        fsm_list_view = self.env.ref('industry_fsm.project_task_view_list_fsm')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tasks from CRM Tickets'),
            'res_model': 'project.task',
            'domain': [('x_crm_id', '=', self.id)],
            'views': [(fsm_list_view.id, 'tree'), (fsm_form_view.id, 'form')],
        }

