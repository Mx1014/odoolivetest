from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    x_is_final_settlement = fields.Boolean(string="Final Settlement?", default=False)
    x_provision_rule = fields.Many2one('hr.salary.rule', string="Provision Rule")
    x_usage_rule = fields.Many2one('hr.salary.rule', string="Usage Rule")


class WorkingDays(models.Model):
    _inherit = "hr.payslip.worked_days"

    x_date_from = fields.Date(string="From")
    x_date_to = fields.Date(string="To")
    #
