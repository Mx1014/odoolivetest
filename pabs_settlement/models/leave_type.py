from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    x_filter_leave_type = fields.Boolean(string="Settlement Domain", default=False, store=True)
