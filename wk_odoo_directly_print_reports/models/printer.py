# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

PRINTER_TYPE=[
    ('zpl', "Zebra Printer (ZPL)")
]

class WkPrinter(models.Model):

    _name = 'wk_printer.printer'

    name = fields.Char(string="Printer Name", required=True)
    printer_type = fields.Selection(string="Type", selection=PRINTER_TYPE, default="zpl", required=True)