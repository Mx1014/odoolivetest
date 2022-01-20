from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning



class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        for payslip in self:
            rule_list = []
            if not payslip.payslip_run_id:
                #payslip.move_id.x_single_payslip_id = payslip.id
                rule = self.env['hr.salary.rule'].search(
                    [('x_use_employee', '=', True), ('struct_id', '=', payslip.struct_id.id)])
                for rule_id in rule:
                    rule_list.append(rule_id.name)
                if rule:
                    for move in payslip.move_id.mapped('line_ids'):
                        if move.name in rule_list:
                            move.partner_id = payslip.employee_id.address_home_id.id

            for move in payslip.move_id.mapped('line_ids'):
                vals = self.env['hr.salary.rule'].search([('name', '=', move.name), ('struct_id', '=', payslip.struct_id.id)],limit=1)
                if vals:
                    if vals.x_use_employee:
                        move.partner_id = payslip.employee_id.address_home_id.id
                    else:
                        move.partner_id = vals.partner_id.id
        return res

    # def action_view_journal(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': _('Entry'),
    #         'res_model': 'account.move',
    #         'views': [(self.env.ref('account.view_move_form').id, 'form')],
    #         'view_mode': 'form',
    #         'res_id': self.move_id.id,
    #     }


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    x_single_partner_id = fields.Many2one('res.partner', string="Partner +")
    x_use_employee = fields.Boolean(string="Use Employee Name", store=True)





