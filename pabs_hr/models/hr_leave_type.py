from odoo import models, fields, api, _
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo.exceptions import UserError


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'
    x_leave_types = fields.Selection([
        ('Annual Leave', 'Annual Leave'),
        ('Overtime Leave', 'Overtime Leave')],
        string='Leave Types')
    is_attachment_mandatory = fields.Boolean(string='is Attachment Mandatory', default=False)
    x_sequence_id = fields.Many2one('ir.sequence', string='Reference Sequence')


class HrLeave(models.Model):
    _inherit = 'hr.leave'
    name = fields.Char(string='Reference', default='New', readonly=1)
    x_related_is_expats = fields.Boolean(string='Related is Expats', related='employee_id.x_is_expats')
    rejoin_ids = fields.One2many('hr.rejoin.line', 'rejoin_id', copy=False)

    @api.model
    def create(self, vals):
        # self.gathering_rejoin_data()

        if vals.get('name', _('New')) == _('New'):
            holiday = self.env['hr.leave.type'].browse(vals.get('holiday_status_id'))
            if holiday and holiday.x_sequence_id:
                vals['name'] = holiday.x_sequence_id.next_by_id() or _('New')
        result = super(HrLeave, self).create(vals)

        line = {
            'start_date': result.request_date_from,
            'end_date': result.request_date_to,
            'rejoin_id': result.id,
        }
        print(line, "lineeeeeeeeeeee")
        self.env['hr.rejoin.line'].create(line)
        return result

    # def action_validate(self):
    #     self.action_create_unpaid_leave()
    #     res = super(HrLeave, self).action_validate()
    #     return res

    # def gathering_rejoin_data(self):
    #     rejoin_lines = []
    #     print(rejoin_lines, "pppp")
    #     for rec in self:
    #         print(rec, "llll")
    #         line = (0, 0, {
    #             'start_date': self.request_date_from
    #         })
    #         rejoin_lines.append(line)

    # def action_create_unpaid_leave(self):
    #     for rec in self:
    #         if rec.rejoin_ids.x_unpaid_days > 0:
    #             for line in self.rejoin_ids:
    #                 vals = {
    #                     'employee_id': self.employee_id.id,
    #                     'holiday_status_id': line.x_holiday_status.id,
    #                     'request_date_from': line.end_date,
    #                     'request_date_to': line.employee_rejoin_date,
    #                     'number_of_days': line.x_unpaid_days,
    #                     'state': 'confirm',
    #                 }
    #                 move = self.env['hr.leave'].create(vals)

    def action_suspend(self):
        self.employee_id.x_is_expats = True

    def action_resume(self):
        self.employee_id.x_is_expats = False

    def action_resume_suspend_slip(self):
        return {
            'name': _('Rejoin Confirmation'),
            'res_model': 'rejoin.popup',
            'view_mode': 'form',
            'views': [
                (self.env.ref('pabs_hr.rejoin_popup_wiza'
                              'rd_view_form').id, 'form'),
            ],
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
