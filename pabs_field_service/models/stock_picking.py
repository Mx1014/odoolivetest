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

    def _compute_x_repair_total(self):
        for rec in self:
            total = 0
            if rec.code == 'outgoing':
                helpdesk_ticket = self.env['helpdesk.ticket'].search([('picking_ids', 'in', rec.id)])
                if helpdesk_ticket:
                    for repair in helpdesk_ticket.repair_ids:
                        if repair.invoice_method in ['b4repair',
                                                     'after_repair'] and repair.invoice_id and repair.invoice_id.state == 'posted':
                            total += repair.invoice_id.amount_residual

            rec.x_repair_total = total

    x_repair_total = fields.Monetary(string='Repair Bill Amount', compute=_compute_x_repair_total)
    x_repair_product_model = fields.Char(string="Model", compute="get_repair_info")
    x_repair_product_serial = fields.Char(string="Serial No.", compute="get_repair_info")

    def get_repair_info(self):
        for rec in self:
            total = 0
            helpdesk_ticket = self.env['helpdesk.ticket'].search([('picking_ids', 'in', rec.id)])
            if helpdesk_ticket:
                for repair in helpdesk_ticket.repair_ids:
                    rec.x_repair_product_serial = repair.x_product_serial_no
                    rec.x_repair_product_model = repair.product_model
