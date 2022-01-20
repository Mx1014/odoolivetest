from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import re
from datetime import datetime
from odoo.tools.misc import formatLang
from functools import partial


class AccountMove(models.Model):
    _inherit = 'account.move'

    """
    def action_post(self):
        res = super(AccountMove, self).action_post()
        vehicle_invoice_line_ids = self.invoice_line_ids.filtered(lambda s: s.x_vehicle_id)
        print(vehicle_invoice_line_ids, 'LINES')
        if vehicle_invoice_line_ids:
            for line in vehicle_invoice_line_ids:
                vals = {'vehicle_id': line.x_vehicle_id.id,
                        'vendor_id': self.partner_id.id,
                        'x_invoice_id': self.id,
                        'x_invoice_line_id': line.id,
                        'cost_subtype_id': line.x_cost_subtype_id.id,
                        'amount': line.price_total,
                        'date': line.x_vehicle_service_date,
                        'inv_ref': self.name,
                        }
                self.env['fleet.vehicle.log.services'].create(vals)
        return res
        """

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        vehicle_invoice_line_ids = self.invoice_line_ids.filtered(lambda s: s.x_vehicle_id)
        print(vehicle_invoice_line_ids, 'LINES')
        if vehicle_invoice_line_ids:
            service_log_ids = self.env['fleet.vehicle.log.services'].search([('x_invoice_line_id', 'in', vehicle_invoice_line_ids.ids)])
            if service_log_ids:
                for line in service_log_ids:
                    if line.cost_id:
                        line.cost_id.unlink()
                    else:
                        line.unlink()
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    x_cost_subtype_id = fields.Many2one('fleet.service.type', string='Service Type')
    x_vehicle_service_date = fields.Date(string='Service Date')
