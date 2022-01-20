from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    # x_attachement = fields.Binary('Attachement', attachment=True)
    x_attachement = fields.Many2many('ir.attachment', string='Attachement')
    # max_leaves = fields.Float(compute='_compute_leaves')
    leaves_taken = fields.Float(compute='leave_taken_in_timeoff')
    x_total = fields.Float('Total Leave Days')
    x_manager = fields.Many2one(related='employee_id.parent_id')
    x_registration_number = fields.Char(string='Code ID', related='employee_id.registration_number')

    # x_required_attach = fields.Selection([('required','Required'), ('optional','Optional')], realted="holiday_status_id.x_required_attach")

    @api.onchange('holiday_status_id')
    def onchange_holidays(self):
        for employee in self:
            total = self.env['hr.leave.report'].search([
                ('employee_id.id', '=', employee.employee_id.id),
                ('holiday_status_id.active', '=', True),
                ('state', '=', 'validate'),
                ('holiday_status_id', '=', employee.holiday_status_id.id),
            ])
            employee.x_total = sum(total.mapped('number_of_days'))

    def leave_taken_in_timeoff(self):
        self.leaves_taken = self.number_of_days

    # @api.depends('employee_id', 'holiday_status_id')
    # def _compute_leaves(self):
    #     for timeoff in self:
    #         leave_type = timeoff.holiday_status_id.with_context(employee_id=timeoff.employee_id.id)
    #         timeoff.max_leaves = leave_type.max_leaves
    #         timeoff.leaves_taken = leave_type.leaves_taken

    # @api.depends('number_of_days')
    # def _compute_number_of_days_display(self):
    #     for timeoff in self:
    #         timeoff.number_of_days_display = timeoff.number_of_days

    def post_attachment(self):
        attach = []
        for att in self.x_attachement:
            attach.append(att.id)
        self.message_post(body='Attachment', attachment_ids=attach)
        # else:
        #     True

    @api.constrains('employee_id', 'holiday_status_id')
    def user_restriction(self):
        # if self.env.user == self.x_manager.user_id:
        if self.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
            self.holiday_status_id.x_required_attach = 'optional'
        elif not self.x_attachement:
            raise UserError(_("Please Attach Document To Move On !!!"))


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    x_required_attach = fields.Selection([('required', 'Required'), ('optional', ' Optional')],
                                         string="Require Attachment")
    x_show_in_payslip = fields.Boolean(string="Display Remaining Days", default=False, store=True)
