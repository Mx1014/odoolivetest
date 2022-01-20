import dateutil
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from datetime import timedelta
from datetime import datetime


class Picking(models.Model):
    _inherit = 'product.brand'

    extended_warranty_partner_id = fields.Many2one('res.partner', string='Extended Warranty Agent')
