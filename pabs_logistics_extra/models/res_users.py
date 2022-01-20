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
    _inherit = 'res.users'

    x_business_line_ids = fields.Many2many('business.line', string='Business Lines')