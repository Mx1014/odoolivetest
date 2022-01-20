from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import UserError, Warning
import datetime
import calendar


# import datetime


class LogisticsTeamContract(models.Model):
    _name = "logistics.team.contract"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Logistics Teams Contracts"

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('name.sequence') or _('New')

        if vals['start_date'] and vals['end_date'] and fields.Date.from_string(vals['start_date']) > fields.Date.from_string(vals['end_date']):
            raise Warning(_("""The end date cannot be be before the start date"""))

        if vals['start_date'] and vals['team']:
            team = self.env['logistics.team'].search([('id', '=', vals['team'])])
            start_date = fields.Date.from_string(vals['start_date'])
            if team.contract_period_to and team.contract_period_to >= start_date:
                raise Warning(_("""The start date cannot be be before the end of the old contract"""))

        if vals['end_date'] and fields.Date.from_string(vals['end_date']) < fields.Date.today():
            raise Warning(_("""The end date cannot be before today"""))
        result = super(LogisticsTeamContract, self).create(vals)
        result.set_team_contract()
        return result

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    state = fields.Selection([('run', 'Running'), ('expired', 'Expired')], string='Contract Status',
                             compute="contract_status_check")
    team = fields.Many2one('logistics.team', 'Team')
    team_owner = fields.Many2one('res.partner', 'Team Owner', related='team.team_owner')
    start_date = fields.Date(string='Contract Start')
    end_date = fields.Date(string='Contract End')

    def set_team_contract(self):
        self.team.contract_id = self.id
        self.team.is_new_team = True

    def contract_status_check(self):
        for contract in self:
            if contract.start_date and contract.end_date:
                if date.today() > contract.end_date:
                    contract.state = 'expired'
                else:
                    contract.state = 'run'
            else:
                contract.state = False

