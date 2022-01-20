from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning
from random import choice
from string import digits
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _compute_x_teams(self):
        teams = self.env['logistics.team'].search([('team_owner', '=', self.id)])
        self.x_teams = teams

    def _inverse_x_teams(self):
        for record in self:
            print(self.x_teams,'OPPPPPP')
            print(self.env['logistics.team'].search([('team_owner', '=', self.id)]),'OOO')
            for team in self.x_teams:
                for t in self.env['logistics.team'].search([('id', 'in', self.x_teams.ids)]):
                    if team.id == t.id:
                        t.team_owner = record.id
            for t in self.env['logistics.team'].search([('team_owner', '=', self.id)]):
                if t.id not in self.x_teams.ids:
                    print('deletion happened')
                    t.team_owner = None

    # < field
    # name = "test_date1"
    # widget = "daterange"
    # options = "{'related_end_date': 'test_date2'}" / >
    # < field
    # name = "test_date2"
    # widget = "daterange"
    # options = "{'related_start_date': 'test_date1'}" / >

    contract_period_from = fields.Date()
    contract_period_to = fields.Date()
    x_is_subcontractor = fields.Boolean(string="Subcontractor")
    x_teams = fields.Many2many('logistics.team', string='Teams', compute=_compute_x_teams, inverse=_inverse_x_teams,
                               domain="[('team_type', '=', 'subcontractor'), ('team_owner', '=', False)]")
