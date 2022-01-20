import datetime
from dateutil import relativedelta
from odoo import api, fields, models, _
from odoo.addons.helpdesk.models.helpdesk_ticket import TICKET_PRIORITY
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    x_location_id = fields.Many2one('stock.location', string='Repair Location')
    x_operation_id = fields.Many2many('stock.picking.type', string='Return Operations')
    x_unassigned_count = fields.Integer(string="Unassigned Tasks", compute="task_not_assigned")

    def task_not_assigned(self):
        for team in self:
            team.x_unassigned_count = self.env['helpdesk.ticket'].search_count([('fsm_task_ids.x_team_id', '=', False), ('team_id', '=', team.id)])

    def action_view_unassigned_repair(self):
        unassined = self.env['helpdesk.ticket'].search([('fsm_task_ids.x_team_id', '=', False), ('team_id', '=', self.id)])
        #('repair_ids', '=', False),
        return {
            'name': _('Tickets'),
            'res_model': 'helpdesk.ticket',
            'view_mode': 'kanban,tree,form,activity',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {'search_default_team_id': self.id},
            'domain': [('id', 'in', unassined.ids)],
        }

    def action_new_ticket(self):
        return {
            'name': _('Tickets'),
            'res_model': 'helpdesk.ticket',
            'view_mode': 'form',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': {'default_team_id': self.id},
            'target': 'current',
        }
