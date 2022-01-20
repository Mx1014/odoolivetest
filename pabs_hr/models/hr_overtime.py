import math
from xml import etree

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import date
from datetime import timedelta
from datetime import datetime
from dateutil.relativedelta import relativedelta
import dateutil


class HrOvertime(models.Model):
    _name = 'hr.overtime'
    _description = 'Employees Overtime'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, rec.x_employee_name.name))
        return result

    @api.model
    def create(self, vals):
        # vals['state'] = 'first_approve' using associate array
        res = super(HrOvertime, self).create(vals)
        return res

    def action_approval(self):
        for rec in self:
            rec.write({'state': 'approval'})
            self.env['mail.activity'].create({
                'res_id': rec.id,
                'res_model_id': self.env['ir.model']._get('hr.overtime').id,
                'activity_type_id': self.env.ref('pabs_hr.overtime_activity_type').id,
                'summary': 'Check The Overtime',
                'user_id': rec.x_manager_name.user_id.id,
            })

    def action_reset_to_draft(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def action_first_approve(self):
        for rec in self:
            rec.write({'state': 'first_approval'})
            self.env['mail.activity'].create({
                'res_id': rec.id,
                'res_model_id': self.env['ir.model']._get('hr.overtime').id,
                'activity_type_id': self.env.ref('pabs_hr.overtime_activity_type').id,
                'summary': 'Check The Overtime',
                'user_id':  rec.x_employee_name.responsible_id.id,
            })

    # def action_final_approve(self):
    #     for rec in self:
    #         rec.write({'state': 'final_approve'})
    #         self.env['mail.activity'].create({
    #             'res_id': rec.id,
    #             'res_model_id': self.env['ir.model']._get('hr.overtime').id,
    #             'activity_type_id': self.env.ref('pabs_hr.overtime_activity_type').id,
    #             'summary': 'Check The Overtime',
    #             'user_id': rec.x_employee_name.responsible_id.id,
    #         })

    def action_validate(self):
        for rec in self:
            rec.write({'state': 'validated'})
            self.env['mail.activity'].create({
                'res_id': rec.id,
                'res_model_id': self.env['ir.model']._get('hr.overtime').id,
                'activity_type_id': self.env.ref('pabs_hr.overtime_activity_type').id,
                'summary': 'Check The Overtime',
                'user_id': rec.x_employee_name.responsible_id.id,
            })
            if rec.x_compensation == 'payment':
                self.create_work_entry()
            elif rec.x_compensation == 'time_off':
                self.create_allocation()

    def create_work_entry(self):
        for rec in self.overtime_ids:
            vals = {
                'employee_id': self.x_employee_name.id,
                'name': self.x_employee_name.name + ' ' + str(rec.x_work_entry_type_id.name) + ' ' + str(
                    self.x_request_date),
                'date_start': rec.x_overtime_date_from,
                'date_stop': rec.x_overtime_date_to,
                'contract_id': self.x_employee_name.contract_id.id,
                'work_entry_type_id': rec.x_work_entry_type_id.id,
                'state': 'validated',
            }
            move = self.env['hr.work.entry'].create(vals)

    def create_allocation(self):
        total = sum(self.overtime_ids.mapped('x_overtime_period')) / 8
        if total:
            vals = {
                'employee_id': self.x_employee_name.id,
                'name': self.x_employee_name.name + ' ' + str(self.x_holiday_status_id.name) + ' ' + str(
                    self.x_request_date),
                'number_of_days': total,
                'holiday_type': self.x_holiday_type,
                'holiday_status_id': self.x_holiday_status_id.id,
                'state': 'validate',
            }
            move = self.env['hr.leave.allocation'].create(vals)

    def action_domain_overtime(self):
        employees = self.env['hr.employee'].search([('parent_id', '=', self.env.user.employee_id.id)]).ids
        if employees:
            employees.append(self.env.user.employee_id.id)
            return {
                'name': _('To Approve Overtime'),
                'res_model': 'hr.overtime',
                'view_mode': 'tree,form',
                'views': [
                    (self.env.ref('pabs_hr.hr_overtime_view_tree').id, 'tree'),
                    (self.env.ref('pabs_hr.hr_overtime_view_forms').id, 'form'),
                ],
                'type': 'ir.actions.act_window',
                'domain': [('state', '=', 'first_approval'),
                           ('x_employee_name', 'in', employees),
                           ],
            }
        else:
            return {
                'name': _('To Approve Overtime'),
                'res_model': 'hr.overtime',
                'view_mode': 'tree,form',
                'views': [
                    (self.env.ref('pabs_hr.hr_overtime_view_tree').id, 'tree'),
                    (self.env.ref('pabs_hr.hr_overtime_view_forms').id, 'form'),
                ],
                'type': 'ir.actions.act_window',
                'domain': [
                    ('x_employee_name.user_id', '=', self.env.user.id),
                ],
            }

    def action_domain_all_overtime(self):
        employees = self.env['hr.employee'].search([('parent_id', '=', self.env.user.employee_id.id)]).ids
        if employees:
            employees.append(self.env.user.employee_id.id)
            return {
                'name': _('All Overtime'),
                'res_model': 'hr.overtime',
                'view_mode': 'tree,form',
                'views': [
                    (self.env.ref('pabs_hr.hr_overtime_view_tree').id, 'tree'),
                    (self.env.ref('pabs_hr.hr_overtime_view_forms').id, 'form'),
                ],
                'type': 'ir.actions.act_window',
                'domain': [
                    ('x_employee_name', 'in', employees),
                ],
            }
        else:
            return {
                'name': _('All Overtime'),
                'res_model': 'hr.overtime',
                'view_mode': 'tree,form',
                'views': [
                    (self.env.ref('pabs_hr.hr_overtime_view_tree').id, 'tree'),
                    (self.env.ref('pabs_hr.hr_overtime_view_forms').id, 'form'),
                    (self.env.ref('pabs_hr.view_to_approve_search').id, 'search'),
                ],
                'type': 'ir.actions.act_window',
                'domain': [
                    ('x_employee_name.user_id', '=', self.env.user.id),
                ],
            }

    @api.model
    def button_to_invisible(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        # res = super(HrOvertime, self).button_to_invisible(view_id=view_id, view_type=view_type, toolbar=toolbar,
        #
        #                                                   submenu=submenu)
        manager = self.search([('x_manager_name', '=', self.env.user.id)])
        print(manager, "112212")
        if manager and view_id == self.env.ref(
                'pabs_hr.hr_overtime_view_forms').id:
            doc = etree.XML(res['arch'])
            node = doc.xpath("//form//header//button[@name='action_first_approval']")[0]
            print(node)
            node.set('invisible', "1")
            res['arch'] = etree.tostring(doc)
        return True

        # archnode = etree.fromstring(arch)
        # # add the js_class 'board' on the fly to force the webclient to
        # # instantiate a BoardView instead of FormView
        # archnode.set('js_class', 'board')
        # return etree.tostring(remove_unauthorized_children(archnode), pretty_print=True, encoding='unicode')

    overtime_ids = fields.One2many('hr.overtime.lines', 'overtime_id', copy=False)
    x_compensation = fields.Selection(string='Compensation', default='payment', selection=[
        ('payment', 'Payment'),
        ('time_off', 'Time off')])
    x_holiday_type = fields.Selection([
        ('employee', 'By Employee')],
        string='Allocation Mode', readonly=True, required=True, default='employee')
    allocation_type = fields.Selection(
        [
            ('regular', 'Regular Allocation')
        ], string="Allocation Type", default="regular")
    x_holiday_status_id = fields.Many2one("hr.leave.type", string="Time Off Type",
                                          domain=[('x_leave_types', '=', 'Overtime Leave')])
    x_employee_name = fields.Many2one('hr.employee', string='Employee', track_visibility='onchange',
                                      default=lambda self: self.env.user.employee_id)
    x_manager_name = fields.Many2one('hr.employee', string='Manager', related='x_employee_name.parent_id')
    x_department = fields.Many2one('hr.department', string='Department', track_visibility='onchange',
                                   related='x_employee_name.department_id')
    x_position = fields.Many2one('hr.job', string='Position', track_visibility='onchange',
                                 related='x_employee_name.job_id')
    x_cpr = fields.Char(string="CPR", related='x_employee_name.identification_id')
    x_contact_no = fields.Char(string="Contact No", related='x_employee_name.phone')
    x_employee_code = fields.Char(string="Employee Code", related='x_employee_name.registration_number')
    x_request_date = fields.Date('Request Date', default=datetime.today())
    state = fields.Selection(
        [('draft', 'Draft'), ('approval', 'Approval'), ('first_approval', 'First Approval'),
         ('validated', 'Validated')],
        string='State', default='draft', readonly=True, track_visibility='onchange', copy=False)
    x_registration_number = fields.Char(string='Code ID', related='x_employee_name.registration_number')
    current_user = fields.Integer(compute='_get_current_user')
    x_user_id = fields.Integer(string='Related User', related='x_manager_name.user_id.id')

    @api.depends()
    def _get_current_user(self):
        for rec in self:
            rec.current_user = self.env.user.id
    # current_user = fields.Many2one('res.users', compute='_get_current_user')
    #
    # @api.depends()
    # def _get_current_user(self):
    #     for rec in self:
    #         rec.current_user = self.env.user


class HrWorkEntryInherit(models.Model):
    _inherit = 'hr.work.entry.type'
    x_is_overtime = fields.Boolean(string='Is Overtime')
