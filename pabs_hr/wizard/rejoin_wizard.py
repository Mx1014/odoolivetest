import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context
from dateutil.relativedelta import relativedelta


class PayslipPopup(models.TransientModel):
    _name = 'rejoin.popup'
    rejoin_date = fields.Date(string='Rejoin Date', default=fields.Date.today())
    x_holiday_status_id = fields.Many2one("hr.leave.type", string="Time Off Type")

    def action_validate(self):
        validate = self.env['hr.leave'].search([('id', '=', self._context.get('active_id'))])
        wizard_data = validate.rejoin_ids
        validate.action_resume()
        wizard_data.write({'employee_rejoin_date': self.rejoin_date, 'x_holiday_status': self.x_holiday_status_id})
        print(wizard_data.employee_rejoin_date, 'ggggggggg')
        print(wizard_data.id, 'ggggggggg')
        for rec in validate:
            if rec.rejoin_ids.x_unpaid_days > 0:
                for line in rec.rejoin_ids:
                    vals = {
                        'employee_id': rec.employee_id.id,
                        'holiday_status_id': line.x_holiday_status.id,
                        'request_date_from': line.end_date  + relativedelta(days=1),
                        'request_date_to': line.employee_rejoin_date,
                        'number_of_days': line.x_unpaid_days,
                        'state': 'confirm',
                    }
                    move = self.env['hr.leave'].create(vals)
