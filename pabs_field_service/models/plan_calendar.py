
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class PlanCalendar(models.Model):
    _inherit = 'plan.calendar'

    def monthly_auto_slot_created(self):
        # for i in range(5):
        #     print(i, 'Iteration')
        salam_teams = self.env['logistics.team'].search(
            [('team_type', '=', 'salamgas'), ('business_line.business_line_type', '=', 'delivery')])
        subcontractor_teams = self.env['logistics.team'].search(
            [('team_type', '=', 'subcontractor'), ('contract_period_to', '!=', False),
             ('business_line.business_line_type', '=', 'delivery')])
        teams_ids = []
        if salam_teams:
            for team in salam_teams:
                teams_ids.append(team.id)
        if subcontractor_teams:
            for team in subcontractor_teams:
                teams_ids.append(team.id)
        print(salam_teams.ids, 'SALAM TEAMS IDS')
        print(subcontractor_teams.ids, 'SUBCONTRACTOR TEAMS IDS')
        print(teams_ids, 'TEAMS IDS')
        team_available = self.env['logistics.team'].search([('id', 'in', teams_ids)])
        dates = []
        check_last_date = self.env['plan.calendar'].search([], order='id desc', limit=1).start_datetime
        print(check_last_date, 'CHECK LAST DATE')
        new_teams_salam = self.env['logistics.team'].search([('team_type', '=', 'salamgas'),
                                                             ('business_line.business_line_type', '=', 'delivery'),
                                                             ('is_new_team', '=', True)])
        new_teams_sub = self.env['logistics.team'].search([('team_type', '=', 'subcontractor'),
                                                           ('contract_period_to', '!=', False),
                                                           ('business_line.business_line_type', '=', 'delivery'),
                                                           ('is_new_team', '=', True)])
        new_teams_ids = []
        if new_teams_salam:
            for team in new_teams_salam:
                new_teams_ids.append(team.id)
        if new_teams_sub:
            for team in new_teams_sub:
                new_teams_ids.append(team.id)
        new_teams = self.env['logistics.team'].search([('id', 'in', new_teams_ids)])
        if new_teams:
            for team in new_teams:
                working_days = []
                for days in self.env['team.working.attendance'].search(
                        [('team_id', '=', team.id), ('capacity_per_day', '!=', 0)]):
                    working_days.append(days.dayofweek)
                for day in range(29):
                    day_of_month = fields.Date.today() + timedelta(days=day)
                    team_timeoff_ids = self.env['team.unavailable.date'].search([('team', '=', team.id)])
                    is_timeoff = False
                    if team_timeoff_ids:
                        for team_timeoff in team_timeoff_ids:
                            if team_timeoff.date_from <= day_of_month <= team_timeoff.date_to:
                                is_timeoff = True
                    if not is_timeoff:
                        if (team.team_type == 'salamgas') or (
                                team.contract_period_to and team.contract_period_to >= day_of_month):
                            if day_of_month.strftime("%A").lower() in working_days:
                                for i in range(self.env['team.working.attendance'].search(
                                        [('team_id', '=', team.id),
                                         ('name', '=', day_of_month.strftime("%A"))]).capacity_per_day):
                                    self.create({
                                        'start_datetime': day_of_month,
                                        'end_datetime': day_of_month,
                                        'status': 'available',
                                        'business_line': team.business_line.id,
                                        'auto_create': True,
                                    })
                team.write({'is_new_team': False})

            print('First Month Slots Created')
        last_date = self.env['plan.calendar'].search([('auto_create', '!=', False)], order='id desc',
                                                           limit=1).start_datetime
        print(last_date, 'DFGSDGDFGDFGH')
        duple_check = self.env['plan.calendar'].search(
            [('auto_create', '!=', False), ('start_datetime', '>', last_date)])
        for last in duple_check:
            dates.append(last.start_datetime)
        if dates:
            last_date = max(dates)
        if last_date:
            last_date += timedelta(hours=3)
            if last_date < (fields.Datetime.today() + timedelta(days=28) + timedelta(hours=3)):
                last_date = fields.Datetime.today() + timedelta(days=28) + timedelta(hours=3)
        else:
            last_date = fields.Datetime.today() + timedelta(days=28) + timedelta(hours=3)
        date_back = ''
        date_back = last_date

        for slot in team_available:
            working_days = []
            for days in self.env['team.working.attendance'].search(
                    [('team_id', '=', slot.id), ('capacity_per_day', '!=', 0)]):
                working_days.append(days.dayofweek)
            print(working_days)
            last_date = date_back
            # for days in slot.attendance_ids:
            # for week in range(1):

            if slot.team_type == 'salamgas' or (
                    slot.contract_period_to and slot.contract_period_to >= (last_date + timedelta(days=1)).date() and slot.status == 'available'):
                last_date += timedelta(days=1)
                team_timeoff_ids = self.env['team.unavailable.date'].search([('team', '=', slot.id)])
                is_timeoff = False
                if team_timeoff_ids:
                    for team_timeoff in team_timeoff_ids:
                        if team_timeoff.date_from <= last_date.date() <= team_timeoff.date_to:
                            is_timeoff = True
                if not is_timeoff and last_date.strftime("%A").lower() in working_days:
                    for i in range(self.env['team.working.attendance'].search(
                            [('team_id', '=', slot.id), ('name', '=', last_date.strftime("%A"))]).capacity_per_day):
                        self.create({
                            'start_datetime': last_date,
                            'end_datetime': last_date,
                            'status': 'available',
                            'business_line': slot.business_line.id,
                            'auto_create': True,
                        })
                    if slot.is_new_team:
                        slot.write({'is_new_team': False})

