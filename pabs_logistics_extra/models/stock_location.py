from datetime import datetime
from dateutil import relativedelta
from odoo.exceptions import UserError

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class Location(models.Model):
    _inherit = "stock.location"

    x_user_ids = fields.Many2many('res.users', string="Users Allowed", store=True)
    x_user_dest_ids = fields.Many2many('res.users', string="Users Allowed Destination", relation="user_destination", store=True)

