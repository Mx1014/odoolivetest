from ast import literal_eval
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
import json
import logging
import pytz
import uuid

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    x_print_count = fields.Integer(string='Counting Print', tracking=True)
    x_current_time = fields.Datetime(string='Current Datetime', tracking=True)

    @api.depends('state')
    def print_x_delivery_report(self):
        if self.state == 'done':
            return self.env.ref('pabs_delivery_report.action_report_delivery_note_pabs_delivery_report').report_action(self)

    # def button_validate(self):
    #     res = super(StockPicking, self).button_validate()
    #     print(res, 'result')
    #     if self.state == 'done':
    #         return self.print_x_delivery_report()
    #     else:
    #         return res

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if self.state == 'done':
            return self.print_x_delivery_report()
        else:
            return res


    def action_print_report_from_batch(self):
        return self.env.ref('pabs_delivery_report.action_report_delivery_note_pabs_delivery_report').report_action(self)

    # def button_validate(self):
    #     res = super(StockPicking, self).button_validate()
    #     print(res, 'result')
    #     if self.state == 'done':
    #         if self.x_business_line and not self.x_business_line.x_no_print and not self.batch_id:
    #             return self.print_x_delivery_report()
    #         elif not self.x_business_line:
    #             return self.print_x_delivery_report()
    #         else:
    #             return res
    #     else:
    #         return res
    def count_print_no(self):
        for rec in self:
            rec.x_print_count += 1

    def current_print_datetime(self):
        for rec in self:
            rec.x_current_time = datetime.now()
