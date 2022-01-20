from ast import literal_eval
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
import json
import logging
import pytz
import uuid

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class FieldPlanCalendar(models.Model):
    _name = 'field.plan.calendar'
    _description = 'Field Service Planning'
    _order = 'start_datetime,id desc'
    _rec_name = 'status'
    _check_company_auto = True

    def name_get(self):
        result = []
        for account in self:
            if account.x_task:
                name = account.status.upper() + ' / ' + account.x_task.name
            else:
                name = account.status.upper()
            # name = 'account.status' + ' ' + 'account.delivery.name'
            result.append((account.id, name))
        return result

    def _default_employee_id(self):
        return self.env.user.employee_id

    def _default_start_datetime(self):
        return fields.Datetime.to_string(datetime.combine(fields.Datetime.now(), datetime.min.time()))

    def _default_end_datetime(self):
        return fields.Datetime.to_string(datetime.combine(fields.Datetime.now(), datetime.max.time()))

    def _default_color(self):
        for rec in self:
            if rec.status == 'available':
                rec.color = 10
            else:
                rec.color = 30

    def _compute_auto_x_task(self):
        task_id = self._context.get('task_id')
        if task_id:
            self.auto_x_task = task_id
        else:
            self.auto_x_task = False

    name = fields.Char('Name')
    # x_delivery_domain = fields.Many2many('stock.picking', string="Delivery Domain", compute="compute_delivery_domain")
    # x_business_line = fields.Selection(string='Business Plan', default='cash_memo',
    #                                    selection=[('cash_memo', 'Cash Memo'), ('credit_sale', 'Credit Sale'),
    #                                               ('paid_on_delivery', 'Paid on Delivery'),
    #                                               ('advance_payment', 'Advance Payment')])
    auto_create = fields.Boolean(default=False, store=True)
    note = fields.Text('Note')
    start_datetime = fields.Datetime("Scheduled Date", required=True)
    end_datetime = fields.Datetime("End Date", required=True)
    business_line = fields.Many2one('business.line', string="Business Line",
                                    domain="[('business_line_type', '=', 'service')]")
    auto_x_task = fields.Many2one('project.task', string="Temp Task", compute=_compute_auto_x_task)
    x_task = fields.Many2one('project.task', string="Task", domain="[('project_id.business_line', '=', business_line)]")

    # x_delivery_temp = delivery = fields.Many2one('stock.picking', 'Delivery', compute=_compute_x_delivery_temp)
    # delivery = fields.Many2one('stock.picking', 'Delivery')
    status = fields.Selection(string='Status', default='available',
                              selection=[('available', 'Available'), ('booked', 'Booked')])
    color = fields.Integer("Color", compute=_default_color, default=10)

    period = fields.Selection(string='Preferred Period', selection=[('morning', 'Morning'), ('evening', 'Evening')])
    # delivery_items = fields.Many2many('stock.move', string="Items To Be delivered", compute=_compute_delivery_items)
    x_priority = fields.Selection(string='Priority', default='1',
                                  selection=[('0', 'Not urgent'), ('1', 'Normal'), ('2', 'Urgent'),
                                             ('3', 'Very urgent')])
    x_show_shift = fields.Boolean(default=False, store=True)

    @api.onchange('start_datetime')
    def onchange_start_datetime(self):
        self.end_datetime = self.start_datetime

    def write(self, vals):
        status = self.env['field.plan.calendar'].search([('id', '=', self.ids)]).mapped('status')
        valid = True
        for key, value in vals.items():
            if key == 'status':
                if vals['status'] == 'booked' and 'booked' in status:
                    valid = False
                    raise Warning(_("""This slot has been booked already, please pick another slot."""))
        if valid:
            for key, value in vals.items():
                if key == 'x_task':
                    if value:
                        task = self.env['project.task'].search([('id', '=', value)])
                        task.x_slot = self.id
                        task.x_scheduled_date = self.start_datetime
                        task.onchange_fleet_vehicle_id()
                    else:
                        task = self.env['project.task'].search([('x_slot', '=', self.id)])
                        task.x_slot = value
                        task.x_scheduled_date = False
                        task.onchange_fleet_vehicle_id()
            res = super(FieldPlanCalendar, self).write(vals)
            return res

    def action_save_field_reminder(self):
        if self.auto_x_task:
            task_id = self._context.get('task_id')
            sale_id = self.env['project.task'].search([('id', '=', task_id)]).sale_order_id.id
            self.x_task = self.auto_x_task
            vals = {}
            if self.x_task:
                vals['x_task'] = self.x_task.id
            if self.note:
                vals['note'] = self.note
            if self.x_priority:
                vals['x_priority'] = self.x_priority
            if self.period:
                vals['period'] = self.period
            vals['status'] = 'booked'
            self.write(vals)
            return {
                'name': _('Logistic'),
                'res_model': 'delivery.reminder',
                'view_mode': 'form',
                'views': [
                    (self.env.ref('pabs_logistics_extra.delivery_reminder_form_view').id, 'form'),
                ],
                'target': 'inline',
                'context': {"active_model": 'sale.order', "active_id": sale_id},
                # 'domain': [('id', 'in', show)],
                'type': 'ir.actions.act_window',
            }

    def action_save_field_task(self):
        if self.auto_x_task:
            task_id = self._context.get('task_id')
            self.x_task = self.auto_x_task
            vals = {}
            if self.x_task:
                vals['x_task'] = self.x_task.id
            if self.note:
                vals['note'] = self.note
            if self.x_priority:
                vals['x_priority'] = self.x_priority
            if self.period:
                vals['period'] = self.period
            vals['status'] = 'booked'
            self.write(vals)
            return {
                'name': _('Task'),
                'res_model': 'project.task',
                'res_id': task_id,
                'view_mode': 'form',
                'views': [
                    (self.env.ref('industry_fsm.project_task_view_form').id, 'form'),
                ],
                # 'target': 'new',
                # 'context': {"active_model": 'sale.order', "active_id": sale_id},
                # 'domain': [('id', 'in', show)],
                'type': 'ir.actions.act_window',
            }

    def action_save_field_helpdesk_ticket(self):
        if self.auto_x_task:
            task_id = self._context.get('task_id')
            ticket_id = self.env['project.task'].search([('id', '=', task_id)]).helpdesk_ticket_id.id
            self.x_task = self.auto_x_task
            vals = {}
            if self.x_task:
                vals['x_task'] = self.x_task.id
            if self.note:
                vals['note'] = self.note
            if self.x_priority:
                vals['x_priority'] = self.x_priority
            if self.period:
                vals['period'] = self.period
            vals['status'] = 'booked'
            self.write(vals)
            return {
                'name': _('Helpdesk Ticket'),
                'res_model': 'helpdesk.ticket',
                'res_id': ticket_id,
                'view_mode': 'form',
                'views': [
                    (self.env.ref('helpdesk.helpdesk_ticket_view_form').id, 'form'),
                ],
                # 'target': 'new',
                # 'context': {"active_model": 'sale.order', "active_id": sale_id},
                # 'domain': [('id', 'in', show)],
                'type': 'ir.actions.act_window',
            }

    def action_save_field_crm_ticket(self):
        if self.auto_x_task:
            task_id = self._context.get('task_id')
            crm_id = self.env['project.task'].search([('id', '=', task_id)]).x_crm_id.id
            self.x_task = self.auto_x_task
            vals = {}
            if self.x_task:
                vals['x_task'] = self.x_task.id
            if self.note:
                vals['note'] = self.note
            if self.x_priority:
                vals['x_priority'] = self.x_priority
            if self.period:
                vals['period'] = self.period
            vals['status'] = 'booked'
            self.write(vals)
            return {
                'name': _('Lead or Opportunity'),
                'res_model': 'crm.lead',
                'res_id': crm_id,
                'view_mode': 'form',
                'views': [
                    (self.env.ref('crm.crm_lead_view_form').id, 'form'),
                ],
                # 'target': 'new',
                # 'context': {"active_model": 'sale.order', "active_id": sale_id},
                # 'domain': [('id', 'in', show)],
                'type': 'ir.actions.act_window',
            }

    def action_shift_write(self):
        self.ensure_one()
        business_line = self._context.get('business_line')
        slot_id = self._context.get('slot_id')
        slot_data = self.env['field.plan.calendar'].search([('id', '=', slot_id)])
        sale_id = slot_data.x_task.sale_order_id.id
        vals = {}
        if slot_data:
            if slot_data.x_task:
                vals['x_task'] = slot_data.x_task.id

            if slot_data.note:
                vals['note'] = slot_data.note
            if slot_data.x_priority:
                vals['x_priority'] = slot_data.x_priority
            if slot_data.status == 'booked':
                vals['status'] = slot_data.status
            if slot_data.period:
                vals['period'] = slot_data.period
            self.write(vals)
            slot_data.x_task = None
            slot_data.note = ''
            slot_data.x_priority = '1'
            slot_data.status = 'available'
            slot_data.period = 0
        return {
            'name': _('Field Service Calendar'),
            'res_model': 'field.plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_field_service.field_plan_calendar_gantt_view').id, 'gantt'),
            ],
            # 'target': 'new',
            # 'context': {'business_line': business_line},
            # 'domain': [('x_task.sale_order_id', '=', sale_id)],
            'type': 'ir.actions.act_window',
        }

    def action_shift_write_sale(self):
        self.ensure_one()
        business_line = self._context.get('business_line')
        slot_id = self._context.get('slot_id')
        print(business_line, slot_id, 'AAAAAA')
        slot_data = self.env['field.plan.calendar'].search([('id', '=', slot_id)])
        sale_id = slot_data.x_task.sale_order_id.id
        vals = {}
        if slot_data:
            if slot_data.x_task:
                vals['x_task'] = slot_data.x_task.id

            if slot_data.note:
                vals['note'] = slot_data.note
            if slot_data.x_priority:
                vals['x_priority'] = slot_data.x_priority
            if slot_data.status == 'booked':
                vals['status'] = slot_data.status
            if slot_data.period:
                vals['period'] = slot_data.period
            self.write(vals)
            slot_data.x_task = None
            slot_data.note = ''
            slot_data.x_priority = '1'
            slot_data.status = 'available'
            slot_data.period = 0
        return {
            'name': _('Field Service Calendar'),
            'res_model': 'field.plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_field_service.field_plan_calendar_gantt_view').id, 'gantt'),
            ],
            # 'target': 'new',
            # 'context': {'business_line': business_line},
            'domain': [('x_task.sale_order_id', '=', sale_id)],
            'type': 'ir.actions.act_window',
        }

    def action_shift_write_task(self):
        business_line = self._context.get('business_line')
        slot_id = self._context.get('slot_id')
        slot_data = self.env['field.plan.calendar'].search([('id', '=', slot_id)])
        task_id = slot_data.x_task.id
        slot_data.x_task.x_batch_id = False
        vals = {}
        if slot_data:
            if slot_data.x_task:
                vals['x_task'] = slot_data.x_task.id

            if slot_data.note:
                vals['note'] = slot_data.note
            if slot_data.x_priority:
                vals['x_priority'] = slot_data.x_priority
            if slot_data.status == 'booked':
                vals['status'] = slot_data.status
            if slot_data.period:
                vals['period'] = slot_data.period
            self.write(vals)
            slot_data.x_task = None
            slot_data.note = ''
            slot_data.x_priority = '1'
            slot_data.status = 'available'
            slot_data.period = 0
        return {
            'name': _('Task'),
            'res_model': 'project.task',
            'res_id': task_id,
            'view_mode': 'form',
            'views': [
                (self.env.ref('industry_fsm.project_task_view_form').id, 'form'),
            ],
            # 'target': 'new',
            # 'context': {"active_model": 'sale.order', "active_id": sale_id},
            # 'domain': [('id', 'in', show)],
            'type': 'ir.actions.act_window',
        }

        # {
        #     'name': _('Field Plan Calendar'),
        #     'res_model': 'field.plan.calendar',
        #     'view_mode': 'gantt',
        #     'views': [
        #         (self.env.ref('pabs_field_service.field_plan_calendar_gantt_view').id, 'gantt'),
        #     ],
        #     # 'target': 'new',
        #     # 'context': {'business_line': business_line},
        #     'domain': [('x_task.sale_order_id', '=', sale_id)],
        #     'type': 'ir.actions.act_window',
        # }

    def action_shift_field_plan_calendar_view_gantt(self):
        self.ensure_one()
        business_line = self._context.get('business_line')
        slot_id = self._context.get('slot_id')
        return {
            'name': _('Field Slots'),
            'res_model': 'field.plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_field_service.shift_field_plan_calendar_gantt_view').id, 'gantt'),
            ],
            'target': 'new',
            'context': {'business_line': business_line, 'slot_id': slot_id},
            'domain': [('business_line', '=', business_line), ('status', '=', 'available')],
            'type': 'ir.actions.act_window',
        }

    def action_shift_field_plan_calendar_view_gantt_sale(self):
        self.ensure_one()
        business_line = self._context.get('business_line')
        slot_id = self._context.get('slot_id')
        return {
            'name': _('Field Slots'),
            'res_model': 'field.plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_field_service.shift_field_plan_calendar_gantt_view_sale').id, 'gantt'),
            ],
            'target': 'new',
            'context': {'business_line': business_line, 'slot_id': slot_id},
            'domain': [('business_line', '=', business_line), ('status', '=', 'available')],
            'type': 'ir.actions.act_window',
        }

    def monthly_auto_slot_created(self):
        # for i in range(5):
        #     print(i, 'Iteration')
        salam_teams = self.env['logistics.team'].search(
            [('team_type', '=', 'salamgas'), ('business_line.business_line_type', '=', 'service')])
        subcontractor_teams = self.env['logistics.team'].search(
            [('team_type', '=', 'subcontractor'), ('contract_period_to', '!=', False),
             ('business_line.business_line_type', '=', 'service')])
        teams_ids = []
        if salam_teams:
            for team in salam_teams:
                teams_ids.append(team.id)
        if subcontractor_teams:
            for team in subcontractor_teams:
                teams_ids.append(team.id)
        # team_available = self.env['logistics.team'].search([('contract_period_to', '!=', False), ('business_line.business_line_type', '=', 'service')])
        team_available = self.env['logistics.team'].search([('id', 'in', teams_ids)])
        dates = []
        check_last_date = self.env['field.plan.calendar'].search([], order='id desc', limit=1).start_datetime
        new_teams_salam = self.env['logistics.team'].search([('team_type', '=', 'salamgas'),
                                                             ('business_line.business_line_type', '=', 'service'),
                                                             ('is_new_team', '=', True)])
        new_teams_sub = self.env['logistics.team'].search([('team_type', '=', 'subcontractor'),
                                                           ('contract_period_from', '!=', False),
                                                           ('contract_period_to', '!=', False),
                                                           ('business_line.business_line_type', '=', 'service'),
                                                           ('is_new_team', '=', True)])
        new_teams_ids = []
        if new_teams_salam:
            for team in new_teams_salam:
                new_teams_ids.append(team.id)
        if new_teams_sub:
            for team in new_teams_sub:
                new_teams_ids.append(team.id)
        new_teams = self.env['logistics.team'].search([('id', 'in', new_teams_ids)])

        # if not check_last_date:
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
                        if (team.team_type == 'salamgas') or (team.contract_period_from and
                                                              team.contract_period_to and team.contract_period_from <= day_of_month <= team.contract_period_to):
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
                                if team.is_new_team:
                                    team.write({'is_new_team': False})

            print('First Month Slots Created')
        last_date = self.env['field.plan.calendar'].search([('auto_create', '!=', False)], order='id desc',
                                                           limit=1).start_datetime
        duple_check = self.env['field.plan.calendar'].search(
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
        if last_date and team_available:
            for slot in team_available:
                working_days = []
                for days in self.env['team.working.attendance'].search(
                        [('team_id', '=', slot.id), ('capacity_per_day', '!=', 0)]):
                    working_days.append(days.dayofweek)
                last_date = date_back
                if slot.team_type == 'salamgas' or (
                        slot.contract_period_to and slot.contract_period_to >= last_date.date() and slot.status == 'available'):
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
