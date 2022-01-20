from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class ProvisionAdjustmentLines(models.Model):
    _name = 'provision.adjustment.lines'
    x_employee_id = fields.Many2one('hr.employee', string='Employee', track_visibility='onchange')
    x_reference = fields.Many2one("provision.adjustment", string="Reference")
    x_current_provision = fields.Float(string="Current Provision")
    x_calculated_provision = fields.Float(string="Calculated Provision")
    x_adjustment = fields.Float(string="Adjustment")
    x_annual_leave_remaining = fields.Float(string='Annual Leave Remaining', store=True)
    x_period1_days = fields.Float(string='Period1', store=True)
    x_period2_days = fields.Float(string='Period2', store=True)
    x_join_date = fields.Date(string='Date Of Join')
    x_period1_amount = fields.Float(string='Period1 Amount', store=True)
    x_period2_amount = fields.Float(string='Period2 Amount', store=True)
    x_working_days = fields.Float(string='Working Days')
    # x_annual_leave_taken = fields.Float(string='Leave Taken', store=True)


