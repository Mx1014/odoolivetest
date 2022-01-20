from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_batch_payslip_id = fields.Many2one('hr.payslip.run', string="Batch")
    x_payment_slips = fields.Many2one('account.payment', related="x_batch_payslip_id.x_payment_id")
    x_single_payslip_id = fields.Many2one('hr.payslip', string="Payslip")
    x_single_payment = fields.Many2one('account.payment', string="Payments")
    x_payslip_journal = fields.Many2one('account.journal', string="Payslip Journal", domain=[('type', 'in', ['cash', 'bank'])])

    def action_register_payment(self):
        total_amount = 0.0
        partner = 0
        for sum in self.mapped('line_ids'):
            if sum.partner_id:
                    partner = sum.partner_id.id
        for move in self:
            batch = move.x_batch_payslip_id
            if batch:
                payment_methods = batch.x_bank_journal_id.outbound_payment_method_ids if total_amount < 0 else batch.x_bank_journal_id.inbound_payment_method_ids
                for slip in batch.mapped('slip_ids'):
                  total_amount += slip.net_wage
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': 'outbound',
                    'partner_id': partner,
                    'partner_type': 'supplier',
                    'journal_id': batch.x_bank_journal_id.id,
                    'payment_date': batch.date_end,
                    #'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
                    'amount': total_amount,
                    'communication': move.ref,
                    'x_payroll_move_id': move.id,
                })
                batch.x_payment_id = payment
                #batch.x_payment_id.post()

    def action_register_single_payment(self):
        total_amount = 0.0
        for move in self:
            single = move.x_single_payslip_id
            true = self.env['hr.salary.rule'].search([('name', '=', 'Net Salary'), ('struct_id', '=', single.struct_id.id)]).x_use_employee
            if single:
                if not move.x_payslip_journal:
                    raise UserError(_("Please Select Payslip Journal!"))
                #payment_methods = batch.x_bank_journal_id.outbound_payment_method_ids if total_amount < 0 else batch.x_bank_journal_id.inbound_payment_method_ids
                payment_methods = move.x_payslip_journal.outbound_payment_method_ids if total_amount < 0 else move.x_payslip_journal.inbound_payment_method_ids
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': 'outbound',
                    'partner_id': single.employee_id.address_home_id.id,
                    'partner_type': 'supplier',
                    'journal_id': move.x_payslip_journal.id,
                    'payment_date': single.date_to,
                    # 'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
                    'amount': single.net_wage,
                    'communication': move.ref,
                    'x_payroll_move_id': move.id,
                })
                move.x_single_payment = payment
                #move.x_single_payment.post()



    def action_view_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment'),
            'res_model': 'account.payment',
            'views': [(self.env.ref('account.view_account_payment_form').id, 'form')],
            'view_mode': 'form',
            'res_id': self.x_batch_payslip_id.x_payment_id.id,
        }

    def action_view_single_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment'),
            'res_model': 'account.payment',
            'views': [(self.env.ref('account.view_account_payment_form').id, 'form')],
            'view_mode': 'form',
            #'view_id': False,
            #'domain': [('id', '=', self.x_single_payment.id)]
            'res_id': self.x_single_payment.id,
        }

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    x_payroll_move_id = fields.Many2one('account.move', string="Payroll Move")

    def action_view_payroll_entry(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Entry'),
            'res_model': 'account.move',
            'views': [(self.env.ref('account.view_move_form').id, 'form')],
            'view_mode': 'form',
            'res_id': self.x_payroll_move_id.id,
        }


