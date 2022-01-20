from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning
from odoo.tools import float_is_zero
from odoo.tools import float_compare, float_round

class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    # def _get_line(self):
    #     line_num = 1
    #     for line_rec in self.slip_id.line_ids:
    #         line_rec.x_serial_no = line_num
    #         line_num += 1

    x_serial_no = fields.Integer(string='Serial Number', readonly=False, default=False)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    x_remaining_days = fields.Float(string="Remaining Days", compute="_get_remaining_days")
    x_provision = fields.Monetary(string="Total Provision")
    x_usage = fields.Monetary(string="Total Usage")
    x_balance = fields.Monetary(string="Balance")

    @api.onchange('employee_id')
    def _get_remaining_days(self):
        for payslip in self:
            days = self.env['hr.leave.report'].search(
                [('employee_id', '=', payslip.employee_id.id), ('holiday_status_id.x_show_in_payslip', '!=', False)])
            payslip.x_remaining_days = sum(days.mapped('number_of_days'))

    #
    # @api.onchange('employee_id')
    # def _get_provision(self):
    #     for payslip in self:
    #         provision = self.env['hr.payslip.line'].search([('employee_id', '=', payslip.employee_id.id), (
    #             'salary_rule_id', '=', payslip.struct_id.x_provision_rule.id),
    #                                                         ('date_to', '<=', payslip.date_to)])
    #         payslip.x_provision = sum(provision.mapped('total'))
    #
    # @api.onchange('employee_id')
    # def _get_usage(self):
    #     for payslip in self:
    #         usage = self.env['hr.payslip.line'].search([('employee_id', '=', payslip.employee_id.id), (
    #             'salary_rule_id', '=', payslip.struct_id.x_usage_rule.id),
    #                                                     ('date_to', '<=', payslip.date_to)])
    #         payslip.x_usage = sum(usage.mapped('total'))

    # @api.onchange('employee_id')
    # def _get_balance(self):
    #     for payslip in self:
    #         payslip.x_balance = payslip.x_provision - payslip.x_usage

    # def print_payslip(self):
    #     if self.struct_id.report_id.report_name == 'hr_payroll.report_payslip':
    #         return {'type': 'ir.actions.report', 'report_name': 'hr_payroll.report_payslip', 'report_type': "qweb-pdf"}
    #     elif self.struct_id.report_id.report_name == 'pabs_payroll.report_bonus_payslip':
    #         return {'type': 'ir.actions.report', 'report_name': 'pabs_payroll.report_bonus_payslip',
    #                 'report_type': "qweb-pdf"}
    #     elif self.struct_id.report_id.report_name == 'pabs_payroll.report_settlement_payslip':
    #         return {'type': 'ir.actions.report', 'report_name': 'pabs_payroll.report_settlement_payslip',
    #                 'report_type': "qweb-pdf"}

    # def compute_sheet(self):
    #     for payslip in self.filtered(lambda slip: slip.state not in ['cancel', 'done']):
    #         # number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
    #         number = payslip.number or self.env['ir.sequence'].next_by_code(
    #             payslip.struct_id.type_id.x_sequence_id.code)
    #         # delete old payslip lines
    #         payslip.line_ids.unlink()
    #         lines = [(0, 0, line) for line in payslip._get_payslip_lines()]
    #         payslip.write({'line_ids': lines, 'number': number, 'state': 'verify', 'compute_date': fields.Date.today()})
    #     return True

    # def action_payslip_done(self):
    #     res = super(HrPayslip, self).action_payslip_done()
    #     for payslip in self:
    #         rule_list = []
    #         all_rule = []
    #         partner = 0
    #         payslip.move_id.x_batch_payslip_id = payslip.payslip_run_id.id
    #         partner = self.env['hr.salary.rule'].search(
    #             [('name', '=', 'Net Salary'), ('struct_id', '=', payslip.struct_id.id)]).partner_id.id
    #         if not payslip.payslip_run_id:
    #             payslip.move_id.x_single_payslip_id = payslip.id
    #             rule = self.env['hr.salary.rule'].search(
    #                 [('x_use_employee', '=', True), ('struct_id', '=', payslip.struct_id.id)])
    #             for rule_id in rule:
    #                 rule_list.append(rule_id.name)
    #             if rule:
    #                 for move in payslip.move_id.mapped('line_ids'):
    #                     if move.name in rule_list:
    #                         move.partner_id = payslip.employee_id.address_home_id.id
    #         # for move in payslip.move_id.mapped('line_ids'):
    #         #     if 'Net Salary' in move.name:
    #         #         move.partner_id = partner
    #         #         print(partner)
    #         for move in payslip.move_id.mapped('line_ids'):
    #             vals = self.env['hr.salary.rule'].search(
    #                 [('name', '=', move.name), ('struct_id', '=', payslip.struct_id.id)], limit=1)
    #             if vals:
    #                 if vals.x_use_employee:
    #                     move.partner_id = payslip.employee_id.address_home_id.id
    #                 else:
    #                     move.partner_id = vals.partner_id.id
    #             # if 'Net Salary' in move.name:
    #             #     move.partner_id = partner
    #             #     print(partner)
    #     return res

    def action_view_journal(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Entry'),
            'res_model': 'account.move',
            'views': [(self.env.ref('account.view_move_form').id, 'form')],
            'view_mode': 'form',
            'res_id': self.move_id.id,
        }


    def _action_create_account_move(self):
        precision = self.env['decimal.precision'].precision_get('Payroll')

        # Add payslip without run
        payslips_to_post = self.filtered(lambda slip: not slip.payslip_run_id)

        # Adding pay slips from a batch and deleting pay slips with a batch that is not ready for validation.
        payslip_runs = (self - payslips_to_post).mapped('payslip_run_id')
        for run in payslip_runs:
            if run._are_payslips_ready():
                payslips_to_post |= run.slip_ids

        # A payslip need to have a done state and not an accounting move.
        payslips_to_post = payslips_to_post.filtered(lambda slip: slip.state == 'done')

        # Check that a journal exists on all the structures
        if any(not payslip.struct_id for payslip in payslips_to_post):
            raise ValidationError(_('One of the contract for these payslips has no structure type.'))
        if any(not structure.journal_id for structure in payslips_to_post.mapped('struct_id')):
            raise ValidationError(_('One of the payroll structures has no account journal defined on it.'))

        # Map all payslips by structure journal and pay slips month.
        # {'journal_id': {'month': [slip_ids]}}
        slip_mapped_data = {slip.struct_id.journal_id.id: {fields.Date().end_of(slip.date_to, 'month'): self.env['hr.payslip']} for slip in payslips_to_post}
        for slip in payslips_to_post:
            slip_mapped_data[slip.struct_id.journal_id.id][fields.Date().end_of(slip.date_to, 'month')] |= slip

        for journal_id in slip_mapped_data: # For each journal_id.
            for slip_date in slip_mapped_data[journal_id]: # For each month.
                line_ids = []
                debit_sum = 0.0
                credit_sum = 0.0
                date = slip_date
                move_dict = {
                    'narration': '',
                    'ref': date.strftime('%B %Y'),
                    'journal_id': journal_id,
                    'date': date,
                }

                for slip in slip_mapped_data[journal_id][slip_date]:
                    move_dict['narration'] += slip.number or '' + ' - ' + slip.employee_id.name or ''
                    move_dict['narration'] += '\n'
                    for line in slip.line_ids.filtered(lambda line: line.category_id):
                        amount = -line.total if slip.credit_note else line.total
                        if line.code == 'NET': # Check if the line is the 'Net Salary'.
                            for tmp_line in slip.line_ids.filtered(lambda line: line.category_id):
                                if tmp_line.salary_rule_id.not_computed_in_net: # Check if the rule must be computed in the 'Net Salary' or not.
                                    if amount > 0:
                                        amount -= abs(tmp_line.total)
                                    elif amount < 0:
                                        amount += abs(tmp_line.total)
                        if float_is_zero(amount, precision_digits=precision):
                            continue
                        debit_account_id = line.salary_rule_id.account_debit.id
                        credit_account_id = line.salary_rule_id.account_credit.id

                        if debit_account_id: # If the rule has a debit account.
                            debit = amount if amount > 0.0 else 0.0
                            credit = -amount if amount < 0.0 else 0.0

                            debit_line = self._get_existing_lines(
                                line_ids, line, debit_account_id, debit, credit)

                            if not debit_line:
                                debit_line = self._prepare_line_values(line, debit_account_id, date, debit, credit)
                                line_ids.append(debit_line)
                            else:
                                debit_line['debit'] += debit
                                debit_line['credit'] += credit

                        if credit_account_id: # If the rule has a credit account.
                            debit = -amount if amount < 0.0 else 0.0
                            credit = amount if amount > 0.0 else 0.0
                            credit_line = self._get_existing_lines(
                                line_ids, line, credit_account_id, debit, credit)

                            if not credit_line:
                                credit_line = self._prepare_line_values(line, credit_account_id, date, debit, credit)
                                line_ids.append(credit_line)
                            else:
                                credit_line['debit'] += debit
                                credit_line['credit'] += credit

                for line_id in line_ids: # Get the debit and credit sum.
                    debit_sum += line_id['debit']
                    credit_sum += line_id['credit']

                # The code below is called if there is an error in the balance between credit and debit sum.
                if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                    acc_id = slip.journal_id.default_credit_account_id.id
                    if not acc_id:
                        raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (slip.journal_id.name))
                    existing_adjustment_line = (
                        line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
                    )
                    adjust_credit = next(existing_adjustment_line, False)

                    if not adjust_credit:
                        adjust_credit = {
                            'name': _('Adjustment Entry'),
                            'partner_id': False,
                            'account_id': acc_id,
                            'journal_id': slip.journal_id.id,
                            'date': date,
                            'debit': 0.0,
                            'credit': debit_sum - credit_sum,
                        }
                        line_ids.append(adjust_credit)
                    else:
                        adjust_credit['credit'] = debit_sum - credit_sum

                elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                    acc_id = slip.journal_id.default_debit_account_id.id
                    if not acc_id:
                        raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (slip.journal_id.name))
                    existing_adjustment_line = (
                        line_id for line_id in line_ids if line_id['name'] == _('Adjustment Entry')
                    )
                    adjust_debit = next(existing_adjustment_line, False)

                    if not adjust_debit:
                        adjust_debit = {
                            'name': _('Adjustment Entry'),
                            'partner_id': False,
                            'account_id': acc_id,
                            'journal_id': slip.journal_id.id,
                            'date': date,
                            'debit': credit_sum - debit_sum,
                            'credit': 0.0,
                        }
                        line_ids.append(adjust_debit)
                    else:
                        adjust_debit['debit'] = credit_sum - debit_sum

                # Add accounting lines in the move
                move_dict['line_ids'] = [(0, 0, line_vals) for line_vals in line_ids]
                print(move_dict['line_ids'], 'llll')
                if not slip.move_id:
                   move = self.env['account.move'].create(move_dict)
                   for slip in slip_mapped_data[journal_id][slip_date]:
                    slip.write({'move_id': move.id, 'date': date})
                else:
                   slip.move_id.line_ids = move_dict['line_ids']

        return True



class HrPayslipBatch(models.Model):
    _inherit = 'hr.payslip.run'

    x_bank_journal_id = fields.Many2one('account.journal', string="Bank Journal", copy=False)
    x_payment_id = fields.Many2one('account.payment', string="Payment", readonly=True, copy=False)
    x_move_id = fields.Many2one('account.move', string="Accounting Entry", related="slip_ids.move_id")

    # def action_register_payment(self):
    #     total_amount = 0.0
    #     partner = 0
    #     for sum in self.mapped('slip_ids'):
    #         total_amount += sum.net_wage
    #         for salary in sum.mapped('line_ids'):
    #             if 'Net Salary' in salary.name:
    #                 partner = salary.salary_rule_id.partner_id.id
    #     for batch in self:
    #         payment_methods = batch.x_bank_journal_id.outbound_payment_method_ids if total_amount < 0 else batch.x_bank_journal_id.inbound_payment_method_ids
    #         payment = self.env['account.payment'].create({
    #             'payment_method_id': payment_methods and payment_methods[0].id or False,
    #             'payment_type': 'outbound',
    #             'partner_id': partner,
    #             'partner_type': 'supplier',
    #             'journal_id': batch.x_bank_journal_id.id,
    #             'payment_date': batch.date_end,
    #             'state': 'posted',
    #             #'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
    #             'amount': total_amount,
    #             'name': batch.name,
    #         })
    #         batch.x_payment_id = payment

    # @api.multi
    def print_transfer_request(self):
        return {'type': 'ir.actions.report', 'report_name': 'pabs_payroll.report_transfer_request',
                'report_type': "qweb-pdf"}

    # @api.multi
    def print_transfer_xlsx(self):
        return {'type': 'ir.actions.report', 'report_name': 'pabs_payroll.report_transfer_request_xls',
                'report_type': "xlsx"}

    # def amount_to_text(self, amount):
    #     return self.company_id.currency_id.amount_to_text(amount)
    #
    def action_view_journal(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Entry'),
            'res_model': 'account.move',
            'views': [(self.env.ref('account.view_move_form').id, 'form')],
            'view_mode': 'form',
            'res_id': self.x_move_id.id,
        }

    def action_validates(self):
        self.mapped('slip_ids').filtered(lambda slip: slip.state != 'cancel')._action_create_account_move()


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    x_is_authorized = fields.Boolean(string="Authorized Signatory", default=False, copy=False)


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    x_single_partner_id = fields.Many2one('res.partner', string="Partner +")
    x_use_employee = fields.Boolean(string="Use Employee Name", store=True)


class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'

    x_sequence_number_next = fields.Integer(string='Next Number',
                                            help='The next sequence number will be used for the next invoice.',
                                            compute='_compute_seq_number_next',
                                            inverse='_inverse_seq_number_next')

    x_sequence_id = fields.Many2one('ir.sequence', string='Sequence', required=True, copy=False)
    #
    # @api.depends('x_sequence_id.use_date_range', 'x_sequence_id.number_next_actual')
    # def _compute_seq_number_next(self):
    #     '''Compute 'sequence_number_next' according to the current sequence in use,
    #     an ir.sequence or an ir.sequence.date_range.
    #     '''
    #     for journal in self:
    #         if journal.x_sequence_id:
    #             sequence = journal.x_sequence_id._get_current_sequence()
    #             journal.x_sequence_number_next = sequence.number_next_actual
    #         else:
    #             journal.x_sequence_number_next = 1
    #
    # def _inverse_seq_number_next(self):
    #     '''Inverse 'sequence_number_next' to edit the current sequence next number.
    #     '''
    #     for journal in self:
    #         if journal.x_sequence_id and journal.x_sequence_number_next:
    #             sequence = journal.x_sequence_id._get_current_sequence()
    #             sequence.sudo().number_next = journal.x_sequence_number_next
    #
    # @api.model
    # def create(self, vals):
    #     prefix = ''
    #     prefix = vals['name'][0]
    #     for x in range(0, len(vals['name'])):
    #         print(vals['name'][x])
    #         if vals['name'][x] == " ":
    #             print(prefix)
    #             prefix = '%s%s' % (prefix, vals['name'][x + 1])
    #     vals['x_sequence_id'] = self.env['ir.sequence'].sudo().create({
    #         'name': '%s' % vals['name'],
    #         'code': prefix.upper(),
    #         'implementation': 'no_gap',
    #         'padding': 3,
    #         'number_increment': 1,
    #         # 'company_id': self.company_id.id,
    #         'prefix': prefix.upper(),
    #     }).id
    #     print(vals['x_sequence_id'])
    #     return super(HrPayrollStructureType, self).create(vals)
