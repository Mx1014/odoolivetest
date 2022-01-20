from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import UserError, Warning
import datetime
import calendar
import base64
from odoo.modules.module import get_module_resource



# import datetime


class LogisticsTeam(models.Model):
    _name = "logistics.team"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Logistics Teams"

    @api.model
    def default_get(self, vals):
        attends = [{
            'name': 'Saturday',
            'dayofweek': 'saturday',
            'team_id': self.id,
            'capacity_per_day': 0
        }, {
            'name': 'Sunday',
            'dayofweek': 'sunday',
            'team_id': self.id,
            'capacity_per_day': 0
        }, {
            'name': 'Monday',
            'dayofweek': 'monday',
            'team_id': self.id,
            'capacity_per_day': 0
        }, {
            'name': 'Tuesday',
            'dayofweek': 'tuesday',
            'team_id': self.id,
            'capacity_per_day': 0
        }, {
            'name': 'Wednesday',
            'dayofweek': 'wednesday',
            'team_id': self.id,
            'capacity_per_day': 0
        }, {
            'name': 'Thursday',
            'dayofweek': 'thursday',
            'team_id': self.id,
            'capacity_per_day': 0
        }, {
            'name': 'Friday',
            'dayofweek': 'friday',
            'team_id': self.id,
            'capacity_per_day': 0
        }]
        result = []
        for attend in attends:
            result.append((0, 0, attend))
        # self.attendance_ids = result
        res = super(LogisticsTeam, self).default_get(vals)
        res.update({'attendance_ids': result})
        return res

    @api.model
    def create(self, vals):
        res = super(LogisticsTeam, self).create(vals)
        if res.contract_period_to < res.contract_period_from:
            raise Warning(_("Start Date cannot be before End Date."))
        return res

    def write(self, vals):
        res = super(LogisticsTeam, self).write(vals)
        print(res)
        if self.contract_period_to and self.contract_period_from:
            if self.contract_period_to < self.contract_period_from:
                raise Warning(_("Start Date cannot be before End Date."))
        return res

    # def _compute_contract_period_from(self):
    #     self.contract_period_from = self.contract_id.start_date
    #
    # def _compute_contract_period_to(self):
    #     self.contract_period_to = self.contract_id.end_date

    name = fields.Char('Name', tracking=True)
    is_new_team = fields.Boolean(string='Is New Team', default=True)
    business_line = fields.Many2one('business.line', 'Business Line', tracking=True)
    capacity_by_week = fields.Integer('Capacity per week', compute="capacity_get")
    status = fields.Selection([('available', 'Available'), ('unavailable', 'Unavailable')], string='Status',
                              compute="team_availability")
    contract_id = fields.Many2one('logistics.team.contract', 'Contract Ref.', copy=False, tracking=True)
    contract_period_from = fields.Date(string='Contract Start', related='contract_id.start_date', copy=False)
    contract_period_to = fields.Date(string='Contract End', related='contract_id.end_date', copy=False)
    contract_capacity = fields.Integer(string="Contract Capacity", compute='contract_capacity_count')
    state = fields.Selection([('new', 'New'), ('run', 'Running'), ('expired', 'Expired')], string='Contract Status',
                             compute="contract_status_check")
    attendance_ids = fields.One2many('team.working.attendance', 'team_id', string='Working Days', tracking=True)
    team_owner = fields.Many2one('res.partner', string="Subcontract Team Owner", tracking=True)
    internal_team_owner = fields.Many2one('hr.employee', string="Internal Team Owner", tracking=True)
    team_type = fields.Selection([('salamgas', 'Al-Salam Gas'), ('subcontractor', 'Subcontractor')], default='salamgas',
                                 string='Team Type', tracking=True)
    x_team_mobile_no = fields.Char(string='Team Mobile', tracking=True)
    related_team_user = fields.Many2one('res.users', string="Responsible User")
    active = fields.Boolean(string="Archive", store=True, default=True)
    volume = fields.Float(string='Maximum Volume')
    weight = fields.Float(string='Maximum Weight')
    team_image = fields.Image()


    @api.onchange('team_type')
    def onchange_reset_team_owner(self):
        self.team_owner = None
        self.internal_team_owner = None

    # @api.onchange('business_line')
    # def add_default_attendance_ids(self):
    #     attend = {
    #         'name': 'line description 1',
    #         'dayofweek': 'monday',
    #         'capacity_per_day': 0
    #     }
    #     result = []
    #     result.append((0, 0, attend))
    #     self.attendance_ids = result

    # @api.depends('business_line')
    def team_availability(self):
        for team in self:
            available = self.env['team.unavailable.date'].search([('team', '=', team.id)], limit=1, order="id desc")
            print(available.date_from)
            if available.date_from and available.date_to:
                if available.date_from <= date.today() <= available.date_to:
                    team.status = 'unavailable'
                else:
                    team.status = 'available'
            else:
                team.status = 'available'

    # @api.depends('contract_period_from', 'contract_period_to')
    def contract_status_check(self):
        for team in self:
            if team.team_type == 'subcontractor':
                if team.contract_period_from and team.contract_period_to:
                    if date.today() > team.contract_period_to:
                        team.state = 'expired'
                    else:
                        team.state = 'run'
                else:
                    team.state = 'new'
            else:
                team.state = False

    @api.depends('attendance_ids')
    def capacity_get(self):
        for team in self:
            if team.attendance_ids:
                for work in team.attendance_ids:
                    team.capacity_by_week += work.capacity_per_day
            else:
                team.capacity_by_week = 0

    # @api.onchange('attendance_ids', 'contract_period_from', 'contract_period_to')
    def contract_capacity_count(self):
        if self.contract_period_from and self.contract_period_to:
            start_date = self.contract_period_from
            end_date = self.contract_period_to
            week = {}
            cap_count = 0
            for i in range((end_date - start_date).days):
                day = calendar.day_name[(start_date + datetime.timedelta(days=i + 1)).weekday()]
                week[day] = week[day] + 1 if day in week else 1
            if self.attendance_ids:

                for attend in self.attendance_ids:
                    if dict(attend._fields['dayofweek'].selection).get(attend.dayofweek) in week:
                        days_count = week[dict(attend._fields['dayofweek'].selection).get(attend.dayofweek)]
                        cap_count += (days_count * attend.capacity_per_day)
            self.contract_capacity = cap_count
        else:
            self.contract_capacity = 0

    def action_view_team_contract(self):
        self.ensure_one()
        return {
            'name': _('Team Contracts'),
            'res_model': 'logistics.team.contract',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('pabs_logistics_extra.logistic_team_contract_list_view').id, 'tree'),
                (self.env.ref('pabs_logistics_extra.view_logistics_team_contract_form').id, 'form'),
            ],
            # 'target': 'new',
            'context': {'team_id': self.id, 'default_team': self.id},
            'domain': [('team', '=', self.id)],
            'type': 'ir.actions.act_window',
        }

    def action_new_contract(self):
        self.ensure_one()
        return {
            'name': _('Team Contracts'),
            'res_model': 'logistics.team.contract',
            'view_mode': 'form',
            'views': [
                (self.env.ref('pabs_logistics_extra.view_logistics_team_contract_form_wizard').id, 'form'),
            ],
            'target': 'new',
            'context': {'default_team': self.id, 'team_id': self.id},
            # 'domain': [('team', '=', self.id)],
            'type': 'ir.actions.act_window',
        }


class TeamUnavailableDate(models.Model):
    _name = "team.unavailable.date"
    _description = "Logistics Teams Unavailability"

    def _default_team(self):
        active_model = self._context.get('active_model')
        active_id = self._context.get('active_id')
        if active_model == 'logistics.team':
            return active_id

    team = fields.Many2one('logistics.team', 'Team', default=_default_team)
    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')

    @api.model
    def create(self, vals):
        res = super(TeamUnavailableDate, self).create(vals)
        if res.date_to < res.date_from:
            raise Warning(_("Start Date cannot be before End Date."))
        return res

    def write(self, vals):
        res = super(TeamUnavailableDate, self).write(vals)
        print(res)
        if self.date_to and self.date_from:
            if self.date_to < self.date_from:
                raise Warning(_("Start Date cannot be before End Date."))
        return res


class TeamWorkingAttendance(models.Model):
    _name = "team.working.attendance"
    _description = "Team Working Attendance"
    _order = 'id'

    name = fields.Char(required=True)
    dayofweek = fields.Selection([
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday')
    ], 'Day of Week', required=True, index=True, default='saturday')
    team_id = fields.Many2one("logistics.team", string="Team")
    capacity_per_day = fields.Integer(string="Capacity Per Day")

    # day_period = fields.Selection([('morning', 'Morning'), ('afternoon', 'Afternoon')], required=True, default='morning')

    @api.onchange('dayofweek')
    def _onchange_set_name(self):
        self.name = dict(self._fields['dayofweek'].selection).get(self.dayofweek)
    #
    # @api.onchange('hour_from', 'hour_to')
    # def _onchange_hours(self):
    #     # avoid negative or after midnight
    #     self.hour_from = min(self.hour_from, 23.99)
    #     self.hour_from = max(self.hour_from, 0.0)
    #     self.hour_to = min(self.hour_to, 23.99)
    #     self.hour_to = max(self.hour_to, 0.0)
    #
    #     # avoid wrong order
    #     self.hour_to = max(self.hour_to, self.hour_from)
