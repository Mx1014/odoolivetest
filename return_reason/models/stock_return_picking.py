# -*- coding: utf-8 -*-
# Part of Odoo. See ICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    picking_type_id = fields.Many2one(related="picking_id.picking_type_id", string='Current Operation Type', readonly=True)
    is_reason_required = fields.Boolean(related="picking_type_id.is_reason_required")
    return_reason_id = fields.Many2one('stock.return.reason', 'Return Reason', domain="[('picking_type_id', '=', picking_type_id)]")
    picking_code = fields.Selection(related="picking_id.code", string='Type of Operation')

    def create_returns(self):
        res = super(ReturnPicking, self).create_returns()
        if self.is_reason_required:
            if not self.return_reason_id:
                raise UserError(_("You must select a reason for the return!"))
            self.picking_id.return_reason_id = self.return_reason_id
            if self.return_reason_id.responsible_type == 'customer':
                if self.picking_id.partner_id:
                    self.picking_id.reason_partner_id = self.picking_id.partner_id
            elif self.return_reason_id.responsible_type == 'installation_team':
                if self.picking_id.batch_id:
                    self.picking_id.reason_installation_team = self.picking_id.batch_id.x_team
            elif self.return_reason_id.responsible_type == 'sales_person':
                if self.picking_id.x_salesperson:
                    self.picking_id.reason_salesperson = self.picking_id.x_salesperson
            elif self.return_reason_id.responsible_type == 'warehouse':
                if self.picking_id.location_id:
                    self.picking_id.reason_location_id = self.picking_id.location_id
        return res
