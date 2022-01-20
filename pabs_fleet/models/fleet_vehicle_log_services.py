from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import re
from datetime import datetime
from odoo.tools.misc import formatLang
from functools import partial


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    x_invoice_id = fields.Many2one('account.move', string='Bill')
    x_invoice_line_id = fields.Many2one('account.move.line', string='Bill line')