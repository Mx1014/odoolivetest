from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class Print(models.Model):
    _inherit = 'stock.picking.batch'
    x_print_count = fields.Integer(string='Counting Print', tracking=True)
    x_current_time = fields.Datetime(string='Printing Datetime', tracking=True)

    def count_print_no(self):
        for rec in self:
            rec.x_print_count += 1

    def current_print_datetime(self):
        for rec in self:
            rec.x_current_time = datetime.now()

    # @api.model
    # def print_report(self):
    #     print("dfdfdfd")
    #     return self.env.ref('pabs_tripsheet.detailed_tripsheet_report_template').report_action(self)

    def print_report(self):
        pickings = self.mapped('picking_ids').filtered(lambda p: p.state == 'done')
        if not pickings:
            raise UserError(_('Nothing to print.'))
        return self.env.ref(
            'pabs_delivery_report.action_report_delivery_note_pabs_delivery_report').report_action(pickings)

    def print_all_report(self):
        pickings = self.mapped('picking_ids')
        if not pickings:
            raise UserError(_('Nothing to print.'))
        return self.env.ref(
            'pabs_delivery_report.action_report_delivery_note_pabs_delivery_report').report_action(pickings)

    def print_all_repairs(self):
        pickings = self.mapped('picking_ids')
        print(pickings, 'x_business_line')
        helpdesk_ticket = self.env['helpdesk.ticket'].search([('picking_ids', 'in', pickings.ids)])
        if helpdesk_ticket:
            repairs = helpdesk_ticket.mapped('repair_ids')
            return self.env.ref('pabs_service.Service').report_action(repairs)
        else:
            raise UserError(_('Nothing to print.'))

    def print_tripsheet(self):
        pickings = self.mapped('picking_ids')
        if not pickings:
            raise UserError(_('Nothing to print.'))
        return self.env.ref(
            'pabs_tripsheet.Detailed_Tripsheet').report_action(self)

    def print_picking_list(self):
        pickings = self.mapped('picking_ids')
        if not pickings:
            raise UserError(_('Nothing to print.'))
        return self.env.ref('pabs_tripsheet.picking_lisit').report_action(self)
