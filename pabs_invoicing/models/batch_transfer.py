# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockBatchTransfer(models.Model):
    _inherit = 'stock.picking.batch'

    x_invoice_count = fields.Integer(string="Invoices", compute="_get_invoice_counts")

    def action_create_batch_invoice(self):
        for picking in self.picking_ids:
            sale_order = picking.sale_id
            if picking.state == 'done' and sale_order and picking:
                invoice = picking.action_create_invoice()
                if invoice:
                    invoice.x_picking_id = picking.id


    def action_view_invoice_done(self):
        self.ensure_one()
        return {
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_invoice_tree').id, 'tree'),
                (self.env.ref('account.view_move_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('x_picking_id', 'in', self.picking_ids.ids)]
        }

    def _get_invoice_counts(self):
        for batch in self:
            count = self.env['account.move'].search_count([('x_picking_id', 'in', batch.picking_ids.ids)])
            batch.x_invoice_count = count

    def print_all_invoices(self):
        invoice = self.env['account.move'].search([('x_picking_id', 'in', self.picking_ids.ids)])
        if invoice:
            return self.env.ref('pabs_sale_report.Tax_invoice').report_action(invoice)
        else:
            raise UserError(_('Nothing to print.'))
