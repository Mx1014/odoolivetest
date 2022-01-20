from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import date
from datetime import timedelta
from datetime import datetime
import calendar
import dateutil


class OvertimeLines(models.Model):
    _name = 'hr.overtime.lines'
    _description = 'Overtime Lines'

    @api.depends('x_overtime_time_to', 'x_overtime_time_from')
    def _compute_x_overtime_period(self):
        for rec in self:
            if rec.x_overtime_time_to > rec.x_overtime_time_from:
                rec.x_overtime_period = rec.x_overtime_time_to - rec.x_overtime_time_from
            else:
                rec.x_overtime_period = rec.x_overtime_time_to - rec.x_overtime_time_from + 24

    overtime_id = fields.Many2one('hr.overtime', 'Overtime')
    x_overtime_time_from = fields.Float('Time From')
    x_overtime_date = fields.Date('Overtime Date')
    x_overtime_date_for_allocation = fields.Date('Date')
    x_overtime_time_to = fields.Float('Time To', required=True)
    x_overtime_date_from = fields.Datetime('Overtime Date From')
    x_overtime_date_to = fields.Datetime('Overtime Date To')
    x_overtime_period = fields.Float('Total Hours', compute='_compute_x_overtime_period')
    x_overtime_reason = fields.Text('Overtime Reason')
    x_work_entry_type_id = fields.Many2one('hr.work.entry.type', 'Work Entry Type',
                                           domain=[('x_is_overtime', '=', 'True')], compute='automatic_work_entry')
    x_overtime_day = fields.Char('Overtime Day', compute='find_day')

    # def find_day(self):
    #     for rec in self:
    #         # born = datetime.strptime(str(rec.x_overtime_date_from), '%d %m %Y').weekday()
    #         born = datetime.strptime(str(rec.x_overtime_date_from), '%Y-%m-%d%H:%M:%S').weekday()
    #         rec.x_overtime_day = str(calendar.day_name[born])

    def find_day(self):
        for rec in self:
            if rec.overtime_id.x_compensation == 'payment':
                my_datetime = rec.x_overtime_date_from
                day_name = datetime.strptime(str(my_datetime), '%Y-%m-%d %H:%M:%S')
                rec.x_overtime_day = day_name.strftime("%A")
            else:
                rec.x_overtime_day = False
                # print(day_name.strftime("%A"))

    def automatic_work_entry(self):
        for rec in self:
            if rec.x_overtime_day == 'Friday':
                rec.x_work_entry_type_id = 131
            elif not rec.x_overtime_day == 'Friday':
                rec.x_work_entry_type_id = 130

    # if rec.x_overtime_date_from:
    #     day = fields.Datetime.from_string(rec.x_overtime_date_from).weekday()
    #     rec.x_overtime_day = day

    # @api.onchange('x_overtime_period')
    # def _onchange_x_overtime_period(self):
    #     self._inverse_x_overtime_period()
    #
    # @api.depends('x_overtime_time_to', 'x_overtime_time_from')
    # def _compute_x_overtime_period(self):
    #     for rec in self:
    #         rec.x_overtime_period = rec._get_x_overtime_period(rec.x_overtime_time_from,
    #                                                            rec.x_overtime_time_to)
    #
    # def _inverse_x_overtime_period(self):
    #     for rec in self:
    #         if rec.x_overtime_time_from and rec.x_overtime_period:
    #             rec.x_overtime_time_to = rec.x_overtime_time_from + relativedelta(
    #                 hours=rec.x_overtime_period)
    #
    # def _get_x_overtime_period(self, x_overtime_time_from, x_overtime_time_to):
    #     if not x_overtime_time_from or not x_overtime_time_to:
    #         return 0
    #     dt = x_overtime_time_to - x_overtime_time_from
    #     return dt.days * 24 + dt.seconds / 3600  # Number of hours

    # @api.depends('x_work_entry_type_id.x_is_overtime')
    # @api.onchange('x_compensation')
    # def _compute_work_entry(self):
    #     is_true = self.env['hr.work.entry.type'].search([('x_is_overtime', '=', 'True')])
    #     if self.x_compensation == 'payment':
    #         self.x_computed_work_entry = [(6, 0, is_true.ids)]
    #     else:
    #         self.x_computed_work_entry = None

    # overtime_id = fields.Many2one('hr.overtime', 'Overtime')
    # x_overtime_time_from = fields.Datetime('Time From')
    # x_overtime_date = fields.Date('Overtime Date')
    # x_overtime_time_to = fields.Datetime('Time To')
    # x_overtime_time_too = fields.Char('Time Too',compute='_date')
    # x_overtime_period = fields.Float('Total Hours', compute='_compute_x_overtime_period',
    #                                  inverse='_inverse_x_overtime_period', )
    # x_overtime_reason = fields.Text('Overtime Reason')
    # x_work_entry_type_id = fields.Many2one('hr.work.entry.type', 'Work Entry Type',
    #                                        domain=[('x_is_overtime', '=', 'True')])
    #
    # def _date(self):
    #     self.x_overtime_time_too = datetime.datetime.strftime (self.x_overtime_time_to.id, "%H")

    # x_computed_work_entry = fields.Many2many('hr.work.entry.type', string='Work Entry Computed',
    #                                          compute='_compute_work_entry')
    # # @api.onchange('x_overtime_period')
    # # def _onchange_x_overtime_period(self):
    # #     self._inverse_x_overtime_period()
    #
    # # @api.depends('x_overtime_time_to', 'x_overtime_time_from')
    # # def _compute_x_overtime_period(self):
    # #     for rec in self:
    # #         rec.x_overtime_period = rec._get_x_overtime_period(rec.x_overtime_time_from,
    # #                                                            rec.x_overtime_time_to)
    #
    # @api.depends('x_overtime_time_to', 'x_overtime_time_from')
    # def _compute_x_overtime_period(self):
    #     for rec in self:
    #         if rec.x_overtime_time_to > rec.x_overtime_time_from:
    #             rec.x_overtime_period = rec.x_overtime_time_to - rec.x_overtime_time_from
    #         else:
    #             rec.x_overtime_period = rec.x_overtime_time_to - rec.x_overtime_time_from + 24
    #
    # def _inverse_x_overtime_period(self):
    #     for rec in self:
    #         if rec.x_overtime_time_from and rec.x_overtime_period:
    #             rec.x_overtime_time_to = rec.x_overtime_time_from + relativedelta(
    #                 hours=rec.x_overtime_period)
    #
    # def _get_x_overtime_period(self, x_overtime_time_from, x_overtime_time_to):
    #     if not x_overtime_time_from or not x_overtime_time_to:
    #         return 0
    #     dt = x_overtime_time_to - x_overtime_time_from
    #     return dt.days * 24 + dt.seconds / 3600  # Number of hours
    #
    # # @api.depends('x_work_entry_type_id.x_is_overtime')
    # # @api.onchange('x_compensation')
    # # def _compute_work_entry(self):
    # #     is_true = self.env['hr.work.entry.type'].search([('x_is_overtime', '=', 'True')])
    # #     if self.x_compensation == 'payment':
    # #         self.x_computed_work_entry = [(6, 0, is_true.ids)]
    # #     else:
    # #         self.x_computed_work_entry = None
    #
    # overtime_id = fields.Many2one('hr.overtime', 'Overtime')
    # x_overtime_time_from = fields.Float('Time From')
    # x_overtime_date = fields.Date('Overtime Date')
    # x_overtime_time_to = fields.Float('Time To')
    # x_overtime_date = fields.Date('Overtime Date')
    # x_overtime_period = fields.Float('Total Hours', compute='_compute_x_overtime_period',
    #                                  inverse='_inverse_x_overtime_period', )
    # x_overtime_reason = fields.Text('Overtime Reason')
    # x_work_entry_type_id = fields.Many2one('hr.work.entry.type', 'Work Entry Type',
    #                                        domain=[('x_is_overtime', '=', 'True')])
    # # x_computed_work_entry = fields.Many2many('hr.work.entry.type', string='Work Entry Computed',
    # #                                          compute='_compute_work_entry')
    #
