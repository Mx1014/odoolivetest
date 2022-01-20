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


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    x_user_ids = fields.Many2many('res.users', string="Users Allowed")
    x_user_dest_ids = fields.Many2many('res.users',  relation="user_destination_picking", string="Users Destination Allowed")
    x_is_customer_service = fields.Boolean(string='Is Customer Service', default=False)
    x_need_product_cartoon = fields.Boolean(string='Need Product Cartoon', default=False)
