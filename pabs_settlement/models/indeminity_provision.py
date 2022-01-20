from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class IndemnityProvision(models.Model):
    _name = 'indemnity.provision.lines'
    x_id = fields.Many2one('hr.settlement', string='Settlement', ondelete='cascade', index=True)
    indemnity_amount = fields.Float(string='Indemnity Amount', digits=(12, 3))
    indemnity_provision_amount = fields.Float(string='Indemnity Provision Amount', digits=(12, 3))
    total = fields.Float(string='Total', digits=(12, 3))

