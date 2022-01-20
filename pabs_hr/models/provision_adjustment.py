from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta


class ProvisionAdjustment(models.Model):
    _name = 'provision.adjustment'
    name = fields.Char(string='Name')
    x_date = fields.Date(string='Date')
    x_type = fields.Selection([('annual_leave', 'Annual Leave'), ('indemnity', 'Indemnity')], string='Type')
    x_provision_adjustment_lines = fields.One2many('provision.adjustment.lines', 'x_reference',
                                                   string="Provision Adjustment Lines")
    compute_sheet = fields.Boolean(string='Compute Sheet Done', readonly=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('approved', 'Approve'), ('validated', 'Validated')],
        string='State', default='draft', readonly=True, track_visibility='onchange', copy=False)
    annual_leave_provision_account = fields.Many2one('account.account', string="Annual Leave Provision",
                                                     default_model='provision.adjustment')
    annual_leave_expense_account = fields.Many2one('account.account', string="Annual Leave Expense",
                                                   default_model='provision.adjustment')
    indemnity_leave_provision_account = fields.Many2one('account.account',
                                                        string="Indemnity Provision Account",
                                                        default_model='provision.adjustment')
    indemnity_leave_expense_account = fields.Many2one('account.account', string="Indemnity Expense",
                                                      default_model='provision.adjustment')
    journal = fields.Many2one('account.journal', string="journal",
                                      default_model='provision.adjustment')
    x_journal_count = fields.Integer(string='Slips', compute='get_journal_count')
    move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', store=True, readonly=True,
                                 default=lambda self: self.env.company)

    def action_view_journal(self):
        return {
            'name': _('Accounting Entry'),
            'domain': [('id', '=', self.move_id.id), ('state', '!=', 'cancel')],
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_journal_count(self):
        count = self.env['account.move'].search_count(
            [('id', '=', self.move_id.id), ('state', '!=', 'cancel')])
        self.x_journal_count = count

    def create_journal_entry(self):
        for rec in self:
            if rec.x_type == 'annual_leave':
                debit_vals = {
                    'name': rec.name,
                    'debit': abs(sum(rec.x_provision_adjustment_lines.mapped('x_adjustment'))),
                    'credit': 0.0,
                    'account_id': rec.annual_leave_expense_account.id,
                }
                credit_vals = {
                    'name': rec.name,
                    'debit': 0.0,
                    'credit': abs(sum(rec.x_provision_adjustment_lines.mapped('x_adjustment'))),
                    'account_id': rec.annual_leave_provision_account.id,
                }
                vals = {
                    'date': rec.x_date,
                    'journal_id': rec.journal.id,
                    'company_id': rec.company_id.id,
                    'ref': rec.name,
                    'type': 'entry',
                    'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
                }
                move = rec.env['account.move'].create(vals)
                move.post()
                rec.move_id = move
            else:
                debit_vals = {
                    'name': rec.name,
                    'debit':abs(sum(rec.x_provision_adjustment_lines.mapped('x_adjustment'))),
                    'credit': 0.0,
                    'account_id': rec.indemnity_leave_expense_account.id,
                }
                credit_vals = {
                    'name': rec.name,
                    'debit': 0.0,
                    'credit': abs(sum(rec.x_provision_adjustment_lines.mapped('x_adjustment'))),
                    'account_id': rec.indemnity_leave_provision_account.id,
                }
                vals = {
                    'date': rec.x_date,
                    'journal_id': rec.journal.id,
                    'company_id': rec.company_id.id,
                    'ref': rec.name,
                    'type': 'entry',
                    'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
                }
                move = rec.env['account.move'].create(vals)
                move.post()
                rec.move_id = move

    # @api.depends('x_employee_id')
    # def _compute_annual_leave(self):
    #     for employee in self:
    #         annual_leave = self.env['hr.leave.report'].search([
    #             ('employee_id.id', '=', employee.x_provision_adjustment_lines.x_employee_id.id),
    #             ('holiday_status_id.active', '=', True),
    #             ('state', '=', 'validate'),
    #             ('holiday_status_id.x_leave_types', '=', 'Annual Leave')
    #         ])
    #         annual_leave_timeoff = self.env['hr.leave.report'].search([
    #             ('employee_id.id', '=', employee.x_provision_adjustment_lines.x_employee_id.id),
    #             ('holiday_status_id.active', '=', True),
    #             ('state', '=', 'validate'),
    #             ('leave_type', '=', 'request'),
    #             ('holiday_status_id.x_leave_types', '=', 'Annual Leave')
    #         ])
    #         print(annual_leave, "lllll")
    #         print(annual_leave_timeoff, "lllll")
    #         employee.x_annual_leave_taken = sum(annual_leave.mapped('number_of_days'))
    #         employee.x_annual_leave_timeoff = sum(annual_leave_timeoff.mapped('number_of_days'))

    def unlink(self):
        for rec in self:
            if rec.state == 'validated':
                raise UserError(_('It is not allowed to delete a provision that already validated.'))
            return super(ProvisionAdjustment, self).unlink()

    def action_compute_sheet(self):
        current_annual_provision = self.env['anual.provision'].search([])
        current_indemnity_provision = self.env['indemnity.provision'].search([])
        dic = {}
        for rec in self:
            if rec.x_type == 'annual_leave':
                for annual in current_annual_provision:
                    if annual.employee_name not in dic:
                        dic[annual.employee_name] = annual.x_total
                    else:
                        dic[annual.employee_name] += annual.x_total
                for key in dic:
                    if key.active:
                        annual_leave = self.env['hr.leave.report'].search([
                            ('employee_id.id', '=', key.id),
                            ('holiday_status_id.active', '=', True),
                            ('state', '=', 'validate'),
                            ('holiday_status_id.x_leave_types', '=', 'Annual Leave')
                        ])
                        val = sum(annual_leave.mapped('number_of_days')) * ((
                                key.contract_id.wage * 12 / 365))
                        if dic[key]:
                            self.x_provision_adjustment_lines = [
                                (0, 0, {'x_reference': rec.id,
                                        'x_employee_id': key.id,
                                        'x_annual_leave_remaining': sum(annual_leave.mapped('number_of_days')),
                                        'x_current_provision': dic[key],
                                        'x_calculated_provision': val,
                                        'x_adjustment': val - dic[key]
                                        })]
            if rec.x_type == 'indemnity':
                for indemnity in current_indemnity_provision:
                    if indemnity.employee_name.id not in dic:
                        dic[indemnity.employee_name] = indemnity.x_total
                    else:
                        dic[indemnity.employee_name] += indemnity.x_total
                for key in dic:
                    if key.active:
                        if key.country_id.id != 23:
                            d1 = datetime.strptime(str(key.date_of_join), '%Y-%m-%d')
                            d2 = datetime.strptime(str(rec.x_date), '%Y-%m-%d')
                            d3 = d2 - d1
                            work_date = str(d3.days)
                        else:
                            work_date = 0
                        if key.country_id.id != 23:
                            unpaid_leave = self.env['hr.leave.report'].search([
                                ('employee_id.id', '=', key.id),
                                ('holiday_status_id.active', '=', True),
                                ('state', '=', 'validate'),
                                ('holiday_status_id.name', '=', 'Unpaid Leave')
                            ])
                            unpaid = abs(sum(unpaid_leave.mapped('number_of_days')))
                            if float(work_date) <= float(1095):
                                working_dates = work_date
                            else:
                                working_dates = 1095
                            final_working_days = int(working_dates)
                            indemnity_balance = (final_working_days * 15) / 365
                            indemnity_amount = ((key.contract_id.wage * 12) / 365) * indemnity_balance
                            if float(work_date) >= float(1095):
                                period2 = float(work_date) - 1 - 1095 - unpaid
                            else:
                                period2 = 0
                            indemnity_amount2 = ((key.contract_id.wage * 12) / 365) * (period2 * 30) / 365
                            self.x_provision_adjustment_lines = [
                                (0, 0, {'x_reference': rec.id,
                                        'x_employee_id': key.id,
                                        'x_working_days': work_date,
                                        'x_join_date': key.date_of_join,
                                        'x_period1_days': working_dates,
                                        'x_period2_days': period2,
                                        'x_period1_amount': indemnity_amount,
                                        'x_period2_amount': indemnity_amount2,
                                        'x_current_provision': dic[key],
                                        'x_calculated_provision': indemnity_amount + indemnity_amount2,
                                        'x_adjustment': indemnity_amount + indemnity_amount2 - dic[key]
                                        })]
            rec.write({'compute_sheet': True})
            rec.write({'state': 'approved'})

    def action_validate(self):
        for rec in self:
            for line_id in self.x_provision_adjustment_lines:
                if rec.x_type == 'annual_leave':
                    vals = {
                        'employee_name': line_id.x_employee_id.id,
                        'name': rec.name,
                        'x_date': rec.x_date,
                        # 'x_rule': 'ALP',
                        # 'x_reference': line_id.x_reference,
                        'x_total': line_id.x_adjustment,
                    }
                    anual = self.env['anual.provision'].create(vals)
                if rec.x_type == 'indemnity':
                    vals = {
                        'employee_name': line_id.x_employee_id.id,
                        'name': rec.name,
                        'x_date': rec.x_date,
                        # 'x_rule': 'ID',
                        # 'x_reference': line_id.x_reference,
                        'x_total': line_id.x_adjustment,
                    }
                    indemnity = self.env['indemnity.provision'].create(vals)
                rec.create_journal_entry()
                rec.write({'state': 'validated'})
