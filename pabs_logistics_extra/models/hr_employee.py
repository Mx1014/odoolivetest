from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning
from random import choice
from string import digits
from odoo.osv import expression

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _compute_x_teams(self):
        teams = self.env['logistics.team'].search([('internal_team_owner', '=', self.id)])
        self.x_teams = teams

    x_is_supervisor = fields.Boolean(string="Supervisor")
    x_teams = fields.Many2many('logistics.team', string='Teams', compute=_compute_x_teams)


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    x_is_supervisor = fields.Boolean(string="Supervisor")

