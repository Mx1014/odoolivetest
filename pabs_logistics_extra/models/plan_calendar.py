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


class PlanCalendar(models.Model):
    _name = 'plan.calendar'
    _description = 'Planning Logistic'
    _order = 'start_datetime,id desc'
    _rec_name = 'status'
    _check_company_auto = True

    def name_get(self):
        result = []
        for account in self:
            if account.delivery:
                name = account.status.upper() + ' / ' + account.delivery.name
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

    def _default_delivery(self):
        active_id = self._context.get('active_id')
        active_model = self._context.get('active_model')

        # print(active_id)
        # print(active_model)
        if active_model == 'sale.order':
            # done = self.env['plan.calendar'].search([('sale_id', '=', active_id)])
            delivery = self.env['stock.picking'].search([('sale_id', '=', active_id)])
            filtered_d = []
            for d in delivery:
                if d.picking_type_id.business_line == self.business_line:
                    filtered_d.append(d.id)
            print(filtered_d)

            return [('id', 'in', filtered_d)]
        elif active_model == 'plan.calendar':
            delivery = self.env[active_model].search([('id', '=', active_id)]).delivery
            # print(delivery)
            # self.change_compute()
            return [('id', 'in', delivery.ids)]

    def _default_color(self):
        for rec in self:
            if rec.status == 'available':
                rec.color = 10
            else:
                rec.color = 30

    def _compute_x_delivery_temp(self):
        delivery_id = self._context.get('delivery_id')
        self.x_delivery_temp = delivery_id

    def _compute_reserves(self):
        print(self._context.get('x_dn_status'), 'self._context.get()')
        if self.x_delivery_temp.sale_order_type:
            if self.x_delivery_temp.sale_order_type in ['cash_memo', 'service']:
                self.x_dn_status = False
            else:
                if self.x_dn_state:
                    self.x_dn_status = self.x_dn_state
                else:
                   self.x_dn_status = self._context.get('x_dn_status')
        else:
            print('last__________________')
            self.x_dn_status = False

    def _compute_delivery_items(self):
        delivery_id = self._context.get('delivery_id')
        if delivery_id:
            self.delivery_items = self.x_delivery_temp.move_ids_without_package.ids
        elif self.delivery:
            self.delivery_items = self.delivery.move_ids_without_package.ids
        else:
            self.delivery_items = None

    name = fields.Char('Name')
    x_delivery_domain = fields.Many2many('stock.picking', string="Delivery Domain", compute="compute_delivery_domain")
    x_business_line = fields.Selection(string='Business Plan', default='cash_memo',
                                       selection=[('cash_memo', 'Cash Memo'), ('credit_sale', 'Credit Sale'),
                                                  ('paid_on_delivery', 'Paid on Delivery'),
                                                  ('advance_payment', 'Advance Payment')])
    auto_create = fields.Boolean(default=False, store=True)
    note = fields.Text('Note')
    start_datetime = fields.Datetime("Scheduled Date", required=True)
    end_datetime = fields.Datetime("End Date", required=True)
    business_line = fields.Many2one('business.line', string="Business Line")

    x_delivery_temp = delivery = fields.Many2one('stock.picking', 'Delivery', compute=_compute_x_delivery_temp)
    delivery = fields.Many2one('stock.picking', 'Delivery')
    delivery_state = fields.Selection(related="delivery.state", store=True)
    status = fields.Selection(string='Status', default='available',
                              selection=[('available', 'Available'), ('booked', 'Booked')])
    color = fields.Integer("Color", compute=_default_color, default=10)

    period = fields.Selection(string='Preferred Period', selection=[('morning', 'Morning'), ('evening', 'Evening')])
    delivery_items = fields.Many2many('stock.move', string="Items To Be delivered", compute=_compute_delivery_items)
    x_priority = fields.Selection(string='Priority', default='1',
                                  selection=[('0', 'Not urgent'), ('1', 'Normal'), ('2', 'Urgent'),
                                             ('3', 'Very urgent')])

    x_dn_status = fields.Selection([('reserved', 'Reserved'), ('normal', 'Normal')], string="Slot Delivery Type", compute=_compute_reserves)
    x_dn_state = fields.Selection([('reserved', 'Reserved'), ('normal', 'Normal')], string="Slot Delivery Type")

    @api.onchange('start_datetime')
    def onchange_start_datetime(self):
        self.end_datetime = self.start_datetime

    def compute_delivery_domain(self):
        # res = {}
        active_id = self._context.get('active_id')
        active_model = self._context.get('active_model')
        no_dom = self._context.get('no_dom')
        print(active_model)
        print(no_dom)
        coming_from = self._context.get('coming_from')
        # if active_model in ['sale.order', 'plan.calendar']:
        if active_model == 'sale.order':
            # done = self.env['plan.calendar'].search([('delivery', '=', active_id)])
            delivery = self.env['stock.picking'].search([('sale_id', '=', active_id)])
            filtered_d = []
            for d in delivery:
                done = self.env['plan.calendar'].search([('delivery', '=', d.id)])
                if (d.picking_type_id.business_line == self.business_line) and not done:
                    filtered_d.append(d.id)
            # print(filtered_d)
            self.x_delivery_domain = filtered_d
        elif active_model == 'plan.calendar':
            filtered_d = []
            sale_id = self.env[active_model].search([('id', '=', active_id)]).delivery.sale_id
            delivery = self.env['stock.picking'].search([('sale_id', '=', sale_id.id)])
            for d in delivery:
                done = self.env['plan.calendar'].search([('delivery', '=', d.id)])
                if (d.picking_type_id.business_line == self.business_line) and not done:
                    filtered_d.append(d.id)
            # print(filtered_d)
            self.x_delivery_domain = filtered_d
        else:
            self.x_delivery_domain = None
        # self.set_delivery()

    # @api.onchange('delivery')
    # def compute_delivery_items(self):
    #     if self.delivery:
    #         self.delivery_items = self.delivery.move_ids_without_package.ids
    #     else:
    #         self.delivery_items = False
    # @api.onchange('x_delivery_domain')
    # def set_delivery(self):
    #     delivery_id = self._context.get('delivery_id')
    #     if delivery_id:
    #         self.delivery = delivery_id
    #     print(delivery_id, 'del id onchange')

    @api.onchange('delivery')
    def onchange_delivery(self):
        for slot in self:
            if slot.delivery:
                slot.status = 'booked'
                slot.delivery_items = slot.delivery.move_ids_without_package.ids
            else:
                # delivery = self.env['plan.calendar'].search([('id', '=', slot._origin.id)]).delivery
                slot.delivery_items = False
                slot.status = 'available'
                # delivery.scheduled_date = delivery.sale_id.commitment_date

    # @api.onchange('period')
    # def onchange_period(self):
    #     if self.delivery:
    #         self.delivery.period = self.period

    def write(self, vals):
        status = self.env['plan.calendar'].search([('id', 'in', self.ids)]).mapped('status')
        # print(self.id)
        # print(status, 'status')
        invalid = True
        deliverychange = False
        for key, val in vals.items():
            if key == 'status' and val == 'available' and 'booked' in status:
                # if key == 'status' and status == 'available':
                invalid = False
            if key == 'delivery':
                # invalid = False
                deliverychange = True
                if val:
                    plan_slot = self.env['stock.picking'].search([('id', '=', val)])
                    plan_slot.x_slot = self.id

        if ('booked' in status) and invalid and deliverychange:
            raise Warning(_("""This slot has been booked already, please pick another slot."""))
        else:
            for key, val in vals.items():
                if key == 'delivery' and val:
                    delv =  self.env['stock.picking'].search([('id', '=', val)])
                    delv.scheduled_date = self.start_datetime

                    delv.x_dn_status = self.x_dn_status
                    if delv.batch_id:
                        delv.batch_id = False
                    for k, v in vals.items():
                        if k == 'period':
                            self.env['stock.picking'].search([('id', '=', val)]).period = v
                    for k, v in vals.items():
                        if k == 'x_priority':
                            self.env['stock.picking'].search([('id', '=', val)]).priority = v

            res = super(PlanCalendar, self).write(vals)
            return res

    def any_write(self):
        active_id = self._context.get('active_id')
        active_model = self._context.get('active_model')
        if active_model == 'plan.calendar':
            slot = self.env[active_model].search([('id', '=', active_id)])
            delivery = self.env[active_model].search([('id', '=', active_id)]).delivery
            delivery.scheduled_date = self.start_datetime
            # print(delivery, 'delivery write')
            # print(active_id, 'delivery write')
            vals = {'delivery': delivery.id, 'status': 'booked', 'note': slot.note, 'period': slot.period,
                    'x_priority': slot.x_priority, 'delivery_items': slot.delivery_items}
            self.env['plan.calendar'].search([('id', '=', active_id)]).status = 'available'
            self.env['plan.calendar'].search([('id', '=', active_id)]).delivery = None
            self.env['plan.calendar'].search([('id', '=', active_id)]).note = ""
            self.env['plan.calendar'].search([('id', '=', active_id)]).period = None
            self.env['plan.calendar'].search([('id', '=', active_id)]).x_priority = '1'
            self.env['plan.calendar'].search([('id', '=', active_id)]).delivery_items = False
            # print(self.env['plan.calendar'].search([('id', '=', active_id)]).status)
            self.write(vals)
            return self.with_context(sale_id=delivery.sale_id.id).action_delivery_reminder_shift_form_view()

    def action_delivery_reminder_shift_form_view(self):
        self.ensure_one()
        active_id = self._context.get('active_id')
        active_model = self._context.get('active_model')
        print(active_model, active_id, 'active stuff')
        sale_id = self._context.get('sale_id')
        print(sale_id, 'sale_id')
        return {
            'name': _('Logistic'),
            'res_model': 'delivery.reminder',
            'view_mode': 'form',
            'views': [
                (self.env.ref('pabs_logistics_extra.delivery_reminder_form_view').id, 'form'),
            ],
            'target': 'inline',
            'context': {"active_model": 'sale.order', "active_id": sale_id, 'sale_id': sale_id},
            # 'domain': [('id', 'in', show)],
            'type': 'ir.actions.act_window',
        }

    def inventory_any_write(self):
        active_id = self._context.get('active_id')
        active_model = self._context.get('active_model')
        if active_model == 'plan.calendar':
            slot = self.env[active_model].search([('id', '=', active_id)])
            delivery = self.env[active_model].search([('id', '=', active_id)]).delivery
            delivery.scheduled_date = self.start_datetime
            # print(delivery, 'delivery write')
            # print(active_id, 'delivery write')
            vals = {'delivery': delivery.id, 'status': 'booked', 'note': slot.note, 'period': slot.period,
                    'x_priority': slot.x_priority,
                    'delivery_items': slot.delivery_items}
            self.env['plan.calendar'].search([('id', '=', active_id)]).status = 'available'
            self.env['plan.calendar'].search([('id', '=', active_id)]).delivery = None
            self.env['plan.calendar'].search([('id', '=', active_id)]).note = ""
            self.env['plan.calendar'].search([('id', '=', active_id)]).period = None
            self.env['plan.calendar'].search([('id', '=', active_id)]).x_priority = '1'
            self.env['plan.calendar'].search([('id', '=', active_id)]).delivery_items = False
            # print(self.env['plan.calendar'].search([('id', '=', active_id)]).status)
            self.write(vals)
            return self.action_view_inventory_logistic_gantt()

    # def _compute_delivery_shift(self):
    #     active_id = self._context.get('active_id')
    #     active_model = self._context.get('active_model')
    #     # print(active_id)
    #     # print(active_model)
    #     print('test 2')
    #     if active_model == 'plan.calendar':
    #         self.delivery = self.env[active_model].search([('id', '=', active_id)]).delivery
    #
    # def change_compute(self):
    #     res = {}
    #     res['compute'] = {'delivery': [self._compute_delivery_shift]}
    #     print('test 1')
    #     return res

    def monthly_auto_slot_created(self):
        salam_teams = self.env['logistics.team'].search([('team_type', '=', 'salamgas')])
        subcontractor_teams = self.env['logistics.team'].search([('team_type', '=', 'subcontractor'),
                                                                 ('contract_period_to', '!=', False)])
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
                                                             ('is_new_team', '=', True)])
        new_teams_sub = self.env['logistics.team'].search([('team_type', '=', 'subcontractor'),
                                                           ('contract_period_to', '!=', False),
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
                                team.contract_period_to and team.contract_period_to > day_of_month):
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
        date_back = ''
        last_date += timedelta(hours=3)
        date_back = last_date
        for slot in team_available:
            working_days = []
            for days in self.env['team.working.attendance'].search(
                    [('team_id', '=', slot.id), ('capacity_per_day', '!=', 0)]):
                working_days.append(days.dayofweek)
            print(working_days)
            last_date = date_back
            if slot.team_type == 'salamgas' or (
                    slot.contract_period_to and slot.contract_period_to > last_date.date() and slot.status == 'available'):
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

    def action_view_logistic_gantt(self):
        self.ensure_one()
        active_id = self._context.get('active_id')
        active_model = self._context.get('active_model')
        plan_id = self._context.get('plan_id')
        print(plan_id)
        print(active_id, active_model)
        business = []
        sale_id = self.env[active_model].search([('id', '=', plan_id)]).delivery.sale_id
        print(sale_id)
        delivery = self.env['stock.picking'].search([('sale_id', '=', sale_id.id)])
        print(delivery)
        for d in delivery:
            if d.picking_type_id.business_line:
                business.append(d.picking_type_id.business_line.id)
        show = []
        for rec in self.env['plan.calendar'].search([]):
            if rec.business_line.id in business:
                if rec.status == 'available':
                    show.append(rec.id)
                elif rec.status == 'booked' and rec.delivery.sale_id.id == sale_id.id:
                    show.append(rec.id)
        print(business)
        return {
            'name': _('Logistic'),
            'res_model': 'plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_logistics_extra.plan_calendar_view_gantt').id, 'gantt'),
            ],
            # 'context': {"search_default_available": 1, "default_delivery": self.delivery.id},
            'domain': [('id', 'in', show)],
            'type': 'ir.actions.act_window',
        }

    def action_view_inventory_logistic_gantt(self):
        self.ensure_one()
        print('inventory any write')
        return {
            'name': _('Logistic'),
            'res_model': 'plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_logistics_extra.stock_plan_calendar_gantt').id, 'gantt'),
            ],
            'search_view_id': self.env.ref('pabs_logistics_extra.plan_calendar_search_view').id,
            'context': {'search_default_group_by_business_line': 1, 'search_default_group_by_status': 1},
            # 'domain': [('id', 'in', show)],
            'type': 'ir.actions.act_window',
        }

    # def test(self):
    #     self.ensure_one()
    #     print('TEST Remaining Delivery Notes')
    #     return {
    #         'name': _("Remaining Delivery Notes"),  # Name You want to display on wizard
    #         'view_mode': 'tree',
    #         'view_id': self.env.ref('pabs_logistics_extra.delivery_reminder_tree_view').id,
    #         'res_model': 'stock.picking',  # With . Example sale.order
    #         'type': 'ir.actions.act_window',
    #         'target': 'new',
    #     }

    def action_save_reminder(self):
        self.ensure_one()
        active_id = self._context.get('active_id')
        active_model = self._context.get('active_model')
        delivery_id = self._context.get('delivery_id')
        dn_state = self._context.get('x_dn_status')
        sale_id = 0
        if active_model == 'sale.order':
            sale_id = active_id
            print(sale_id, 'sale 1')
        elif active_model == 'plan.calendar':
            sale_id = self.env['plan.calendar'].search([('id', '=', active_id)]).delivery.sale_id.id
            print(sale_id, 'sale 2')
        # business_line = self.delivery.picking_type_id.business_line
        vals = {}
        if delivery_id:
            vals['delivery'] = delivery_id
            if self.status != 'booked':
                vals['status'] = 'booked'
            if self.period != self.env['plan.calendar'].search([('id', '=', self.id)]).period:
                vals['period'] = self.period
            if self.note != self.env['plan.calendar'].search([('id', '=', self.id)]).note:
                vals['note'] = self.note
            if self.delivery_items != self.env['plan.calendar'].search([('id', '=', self.id)]).delivery_items:
                vals['delivery_items'] = self.delivery_items
            # if self.x_priority != self.env['plan.calendar'].search([('id', '=', self.id)]).x_priority:
            vals['x_priority'] = self.x_priority
            print('DELIVERY_ID TRUE')
        else:
            if self.delivery != self.env['plan.calendar'].search([('id', '=', self.id)]).delivery:
                vals['delivery'] = self.delivery.id
            if self.status != self.env['plan.calendar'].search([('id', '=', self.id)]).status:
                vals['status'] = self.status
            if self.period != self.env['plan.calendar'].search([('id', '=', self.id)]).period:
                vals['period'] = self.period
            if self.note != self.env['plan.calendar'].search([('id', '=', self.id)]).note:
                vals['note'] = self.note
            if self.delivery_items != self.env['plan.calendar'].search([('id', '=', self.id)]).delivery_items:
                vals['delivery_items'] = self.delivery_items
            # if self.x_priority != self.env['plan.calendar'].search([('id', '=', self.id)]).x_priority:
            vals['x_priority'] = self.x_priority
        print(vals, 'vaaaaaaaaals')
        # vals = {'delivery': self.delivery.id, 'status': 'booked', 'period': self.period,
        #         'delivery_items': self.delivery_items}
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

    def action_save_plan_calendar_transfer(self):
        delivery_id = self._context.get('delivery_id')
        vals = {}
        if delivery_id:
            vals['delivery'] = delivery_id
            if self.status != 'booked':
                vals['status'] = 'booked'
            if self.period != self.env['plan.calendar'].search([('id', '=', self.id)]).period:
                vals['period'] = self.period
            if self.note != self.env['plan.calendar'].search([('id', '=', self.id)]).note:
                vals['note'] = self.note
            if self.delivery_items != self.env['plan.calendar'].search([('id', '=', self.id)]).delivery_items:
                vals['delivery_items'] = self.delivery_items
            # if self.x_priority != self.env['plan.calendar'].search([('id', '=', self.id)]).x_priority:
            vals['x_priority'] = self.x_priority
            print('DELIVERY_ID TRUE TRANSFER')
            self.write(vals)
            return {
                'name': _('Transfers'),
                'res_model': 'stock.picking',
                'res_id': delivery_id,
                'view_mode': 'form',
                'views': [
                    (self.env.ref('stock.view_picking_form').id, 'form'),
                ],
                # 'context': {"active_model": 'sale.order', "active_id": sale_id},
                # 'domain': [('id', 'in', show)],
                'type': 'ir.actions.act_window',
            }

    def action_save_shift_plan_calendar_transfer(self):
        business_line = self._context.get('business_line')
        delivery_id = self._context.get('delivery_id')
        slot_id = self._context.get('slot')
        active_id = self._context.get('active_id')
        active_model = self._context.get('active_model')
        reschedule = False
        vals = {}
        if slot_id:
            slot = self.env['plan.calendar'].search([('id', '=', slot_id)])
            vals = {'delivery': delivery_id, 'status': 'booked', 'note': slot.note, 'period': self.period,
                    'x_priority': self.x_priority, 'delivery_items': slot.delivery_items}
            self.env['plan.calendar'].search([('id', '=', slot_id)]).status = 'available'
            self.env['plan.calendar'].search([('id', '=', slot_id)]).delivery = None
            self.env['plan.calendar'].search([('id', '=', slot_id)]).note = ""
            self.env['plan.calendar'].search([('id', '=', slot_id)]).period = None
            self.env['plan.calendar'].search([('id', '=', slot_id)]).x_priority = '1'
            self.env['plan.calendar'].search([('id', '=', slot_id)]).delivery_items = False
        # print(self.env['plan.calendar'].search([('id', '=', active_id)]).status)
            deli = self.env['stock.picking'].search([('id', '=', delivery_id)])
            reschedule = self.env['delivery.reschedule'].create({
                'name': delivery_id,
                'user_id': self.env.user.id,
                'date': deli.date_done or deli.scheduled_date,
            })

        self.write(vals)
        reschedule.date_to = deli.scheduled_date
        deli.x_reschedule_confirm = 'pending'

    def action_copy_previous_week(self):
        print('nothing')

    def action_plan_calendar_view_gantt_method(self):
        show = []
        business_line = self._context.get('bl')
        for i in range(35):
            day = datetime.combine(fields.Date.today() + timedelta(days=i), datetime.min.time())
            slot = self.env['plan.calendar'].search(
                [('business_line', '=', business_line), ('status', '=', 'available'),
                 ('start_datetime', '>=', day), ('start_datetime', '<', day + timedelta(days=1))], limit=10).ids
            if slot:
                for s in slot:
                    show.append(s)
        return {
            'name': _('Logistic'),
            'res_model': 'plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_logistics_extra.plan_calendar_view_shift_gantt').id, 'gantt'),
            ],
            'target': 'new',
            'context': {'search_default_group_by_business_line': 1,
                        'search_default_group_by_status': 1},
            'domain': [('business_line', '=', business_line), ('status', '=', 'available'),
                       ('start_datetime', '>=', fields.Date.today()), ('id', 'in', show)],
            'type': 'ir.actions.act_window',
        }

    # def action_plan_calendar_view_gantt_backend(self):
    #     bl = self._context.get('bl')
    #     return {
    #         'name': _('Plan Calendar'),
    #         'res_model': 'plan.calendar',
    #         'view_mode': 'gantt',
    #         'views': [
    #             (self.env.ref('pabs_logistics_extra.plan_calendar_view_shift_gantt').id, 'gantt'),
    #         ],
    #         'target': 'new',
    #         # 'context': {"active_model": 'sale.order', "active_id": sale_id},
    #         'domain': [('business_line', '=', bl), ('status', '=', 'available')],
    #         'type': 'ir.actions.act_window',
    #     }

class deliveryReschedule(models.Model):
    _name = 'delivery.reschedule'

    name = fields.Many2one('stock.picking', string="Delivery")
    user_id = fields.Many2one('res.users', string="User")
    date = fields.Datetime(string="Scheduled From")
    date_to = fields.Datetime(string="Schedule To")
