from odoo import models, fields, api, _
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time
from odoo.addons.resource.models.resource import HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError


class Allocation(models.Model):
    """ Allocation Requests Access specifications: similar to leave requests """
    _inherit = 'hr.leave.allocation'

    # def action_approve(self):
    #     x = self.env['hr.leave.type'].search([])
    #
    #     y = self.env['ir.attachment'].search([('res_model', '=', 'hr.leave.allocation'), ('res_id', '=', self.id)])
    #     print(self)
    #     for rec in x:
    #         if rec.is_attachment_mandatory == True:
    #             print(y, "jjjjj")
    #             if not y:
    #                 raise UserError(_('You Have To Add Attachment'))
    #             else:
    #                 self.write({'state': 'validate'})
    #     res = super(Allocation, self).action_approve()
    #     print(self)
    #     return res
    x_registration_number = fields.Char(string='Code ID', related='employee_id.registration_number')
    interval_unit = fields.Selection([
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('days', 'Days'),
        ('years', 'Years')
    ], string="Unit of time between two intervals", default='weeks', readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    date = fields.Date(string='date', store=True)

    # computed_date = fields.Date(string='date', compute='_date')

    # def _date(self):
    #     self.computed_date = self.date

    @api.model
    def _update_accrual(self):
        dates = self.env['hr.leave.allocation'].search([])

        """
            Method called by the cron task in order to increment the number_of_days when
            necessary.
        """
        today = fields.Date.from_string(fields.Date.today())
        holidays = self.search(
            [('allocation_type', '=', 'accrual'), ('employee_id.active', '=', True), ('state', '=', 'validate'),
             ('holiday_type', '=', 'employee'),
             '|', ('date_to', '=', False), ('date_to', '>', fields.Datetime.now()),
             '|', ('nextcall', '=', False), ('nextcall', '<=', today)])

        for holiday in holidays:
            values = {}

            delta = relativedelta(days=0)

            if holiday.interval_unit == 'days':
                delta = relativedelta(days=holiday.interval_number)
            if holiday.interval_unit == 'weeks':
                delta = relativedelta(weeks=holiday.interval_number)
            if holiday.interval_unit == 'months':
                delta = relativedelta(months=holiday.interval_number)
            if holiday.interval_unit == 'years':
                delta = relativedelta(years=holiday.interval_number)

            values['nextcall'] = (holiday.nextcall if holiday.nextcall else today) + delta

            period_start = datetime.combine(today, time(0, 0, 0)) - delta
            period_end = datetime.combine(today, time(0, 0, 0))

            # We have to check when the employee has been created
            # in order to not allocate him/her too much leaves
            start_date = holiday.employee_id._get_date_start_work()
            # If employee is created after the period, we cancel the computation
            if period_end <= start_date:
                holiday.write(values)
                continue

            # If employee created during the period, taking the date at which he has been created
            if period_start <= start_date:
                period_start = start_date

            worked = holiday.employee_id._get_work_days_data(period_start, period_end,
                                                             domain=[('holiday_id.holiday_status_id.unpaid', '=', True),
                                                                     ('time_type', '=', 'leave')])['days']
            left = holiday.employee_id._get_leave_days_data(period_start, period_end,
                                                            domain=[('holiday_id.holiday_status_id.unpaid', '=', True),
                                                                    ('time_type', '=', 'leave')])['days']
            prorata = worked / (left + worked) if worked else 0

            days_to_give = holiday.number_per_interval
            if holiday.unit_per_interval == 'hours':
                # As we encode everything in days in the database we need to convert
                # the number of hours into days for this we use the
                # mean number of hours set on the employee's calendar
                days_to_give = days_to_give / (holiday.employee_id.resource_calendar_id.hours_per_day or HOURS_PER_DAY)

            values['number_of_days'] = holiday.number_of_days + days_to_give * prorata
            if holiday.accrual_limit > 0:
                values['number_of_days'] = min(values['number_of_days'], holiday.accrual_limit)

            holiday.write(values)

    # def action_approve(self):
    #     res = super(Allocation, self).action_approve()
    #     x = self.env['hr.leave.type'].search([])
    #     for rec in x:
    #         if rec.is_attachment_mandatory == True:
    #             print(self.message_attachment_count, "jjjjj")
    #             if self.message_attachment_count == 0:
    #                 raise UserError(_('You Have To Add Attachment'))
    #             else:
    #                 self.write({'state': 'validate'})
    #     return res
