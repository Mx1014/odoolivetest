
from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import UserError, Warning
import datetime
import calendar
#import datetime


class LogisticsTeam(models.Model):
    _inherit = "logistics.team"

    x_route_id = fields.Many2one('stock.location.route', string='Spare Parts Route', tracking=True)