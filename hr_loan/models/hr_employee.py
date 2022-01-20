from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import date
from datetime import timedelta
from datetime import datetime
import dateutil


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    loan_ids = fields.One2many('hr.loan', 'employee_id', string='Loans')
    loans_count = fields.Integer(compute='_compute_loans_count', string='Loans')

    def _compute_loans_count(self):
        loan_data = self.env['hr.loan'].sudo().read_group([('employee_id', 'in', self.ids)], ['employee_id'],
                                                          ['employee_id'])
        result = dict((data['employee_id'][0], data['employee_id_count']) for data in loan_data)
        for employee in self:
            employee.loans_count = result.get(employee.id, 0)
