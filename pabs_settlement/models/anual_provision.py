from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class AnualProvision(models.Model):
    _name = 'anual.provision.lines'
    x_id = fields.Many2one('hr.settlement', string='Settlement', ondelete='cascade', index=True)
    anual_amount = fields.Float(string='Anual Amount', digits=(12, 3))
    anual_provision_amount = fields.Float(string='Anual Provision Amount', digits=(12, 3))
    total = fields.Float(string='Total', digits=(12, 3))

