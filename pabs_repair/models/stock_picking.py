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

    x_helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', string='Related Helpdesk Ticket')
    x_ticket_id = fields.Integer(string="ID", related="x_helpdesk_ticket_id.id")
    x_ticket_stage_id = fields.Many2one('helpdesk.stage', related="x_helpdesk_ticket_id.stage_id", string="Stage")
    x_ticket_type = fields.Many2one('helpdesk.ticket.type', related="x_helpdesk_ticket_id.ticket_type_id", string="Ticket Type")
    x_ticket_product = fields.Many2one('product.product', related="x_helpdesk_ticket_id.x_product_id", string="Ticket Product")