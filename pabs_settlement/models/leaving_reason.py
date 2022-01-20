from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import date
from datetime import timedelta
from datetime import datetime
import dateutil


class PaymentType(models.Model):
    _name = 'leaving.reason'

    name = fields.Char(string='Description')
