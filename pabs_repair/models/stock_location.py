from datetime import datetime
from dateutil import relativedelta
from odoo.exceptions import UserError

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class Location(models.Model):
    _inherit = "stock.location"

    x_is_spare_part = fields.Boolean(string="Is a Spare Parts Location", default=False, copy=False)
