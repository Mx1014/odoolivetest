from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang

from datetime import date, timedelta
from itertools import groupby
from itertools import zip_longest
from hashlib import sha256
from json import dumps

import json
import re


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_delivery_order_id = fields.Many2one('stock.picking', string='D.N.', related='purchase_line_id.x_delivery_order')