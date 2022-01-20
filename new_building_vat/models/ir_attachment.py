# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.http import request
from odoo.exceptions import UserError, Warning
import re, uuid
import socket
from binascii import hexlify
from subprocess import Popen, PIPE
from lxml import etree
from lxml.builder import E
import json
from datetime import datetime, timedelta
from collections import defaultdict


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    # Any attachment is uploaded to the sale order must be there in the messaging log
    @api.model_create_multi
    def create(self, vals_list):
        records = super(IrAttachment, self).create(vals_list)
        for record in records:
            if record.res_model == "sale.order":
                order_id = self.env['sale.order'].browse(record.res_id)
                order_id.message_post(attachment_ids=[record.id])
        return records
