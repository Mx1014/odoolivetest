# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockReturnReason(models.Model):
    _name = 'stock.return.reason'
    _description = 'Reason of Return'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Text(string='Reason of Return', required=True, help="Reason of Return in details.")
    responsible_type = fields.Selection([
        ('customer', 'Customer'),
        ('installation_team', 'Installation Team'),
        ('sales_person', 'Sales Person'),
        ('warehouse', 'Warehouse'),
        ('alsalam', 'Al Salam'),
        ('principal_company ', 'Principal Company'),
        ('site_inspection ', 'Site Inspection / Teams'),
        ('other ', 'Other'),
    ], string='Responsible', default='customer', required=True)
    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type', required=True, domain="[('code', '=', 'outgoing')]")
