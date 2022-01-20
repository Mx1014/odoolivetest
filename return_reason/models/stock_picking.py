# -*- coding: utf-8 -*-
# Part of Odoo. See ICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    # Reason Fields
    return_reason_id = fields.Many2one('stock.return.reason', 'Return Reason', store=True, readonly=True)
    return_responsible_type = fields.Selection(related="return_reason_id.responsible_type", string='Responsible', readonly=True)
    reason_partner_id = fields.Many2one('res.partner', string='Customer', store=True, readonly=True)
    reason_installation_team = fields.Many2one('logistics.team', string="Installation Team", store=True, readonly=True)
    reason_salesperson = fields.Many2one('res.users', string='Salesperson', store=True, readonly=True)
    reason_location_id = fields.Many2one('stock.location', string='Location', store=True, readonly=True)
