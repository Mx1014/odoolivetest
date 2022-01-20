# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.http import request
from odoo.exceptions import UserError
import math


class AccountMove(models.Model):
    _inherit = "account.move"

    new_id = fields.Many2one('account.move', copy=False, relation="bill_of_entry", string="Overseas Bill")
    bill_count = fields.Integer(string="Bill Of Entry", compute="get_boe")
    counter = fields.Integer()
    x_customs_journal_id = fields.Many2one('account.journal', string="BOE Journal")
    x_overseas_journal_id = fields.Many2one('account.journal', string="Overseas Journal")
    x_is_import = fields.Boolean(string="Is import of goods?", default=False, copy=False)
    x_is_valid_boe = fields.Boolean(string="Valid BOE", default=False, compute="get_x_is_import", store=True)
    x_price_previous = fields.Float(string="previous First Line", )

    def get_boe(self):
        for rec in self:
            count = self.env['account.move'].search([('new_id', '=', rec.id)])
            rec.bill_count = len(count)

    @api.depends('journal_id', 'currency_id', 'fiscal_position_id')
    def get_x_is_import(self):
        boe_journal = self.env['ir.default'].sudo().get('account.move', 'x_overseas_journal_id')
        for move in self:
            #if move.journal_id.id == boe_journal and move.currency_id.id != move.company_currency_id.id and move.fiscal_position_id.x_treatment_type == 'i_e':
            if move.fiscal_position_id.x_treatment_type == 'i_e' and move.type in ['in_invoice', 'in_refund']:
                move.x_is_valid_boe = True
            else:
                move.x_is_valid_boe = False


    # def bill_of_entry(self):
    #     print('running')
    #     for bill in self:
    #         for bill_line in bill.invoice_line_ids:
    #             if bill_line.tax_ids.name == 'IMG' and bill.new_id.name == False:
    #                 inline = [
    #                     (0, 0, {'name': 'Cost', 'quantity': bill_line.quantity, 'price_unit': bill_line.price_unit,
    #                             'discount': bill_line.discount, 'account_id': 0}),
    #                     (0, 0, {'name': 'Insurance', 'quantity': 1, 'price_unit': 0, 'discount': 0, 'account_id': 0}),
    #                     (0, 0, {'name': 'Freight', 'quantity': 1, 'price_unit': 0, 'discount': 0, 'account_id': 0}),
    #                     (0, 0, {'name': 'Total CIF', 'quantity': 1, 'price_unit': 0, 'discount': 0, 'account_id': 0}),
    #                     (0, 0, {'product_id': 4, 'name': 'Custom Duty', 'quantity': 1, 'price_unit': 0, 'discount': 0,
    #                             'account_id': 0, 'is_landed_costs_line': True}),
    #                     (0, 0,
    #                      {'name': 'Taxable Supply', 'quantity': 1, 'price_unit': 0, 'discount': 0, 'account_id': 0}),
    #                     (0, 0, {'name': 'Reverse', 'quantity': 1, 'price_unit': 0, 'discount': 0, 'account_id': 0}),
    #                 ]
    #
    #                 data = {
    #                     'partner_id': bill.partner_id.id,
    #                     'type': 'in_invoice',
    #                     'invoice_line_ids': inline,
    #                     'currency_id': bill.currency_id,
    #                     #'ref': 'BoE',
    #                 }
    #                 id = bill.create(data)
    #                 id.write({'new_id': bill.id})

    def bill_of_entry(self):
        for bill in self:
            amount = 0.0
            paid_at_customs_tax_id = self.env['account.tax'].search([('is_paid_at_customs', '=', True), ('type_tax_use', '=', 'purchase')], limit=1)
            # self.env.ref('l10n_bh.tax_img0')
            # tax = self.env['account.tax'].search([('id', '=', self.env.ref('l10n_bh.tax_img0').id)])
            if not self.env['ir.default'].sudo().get('account.move', 'x_customs_journal_id'):
                raise UserError(_('No default BOE Journal is configured'))
            if bill.x_is_import and bill.new_id.name == False:
                if not paid_at_customs_tax_id:
                    raise UserError(_('There is no taxed configured to be used in the Bill of Entry!'))
                # for bill_line in bill.invoice_line_ids:
                #         amount += bill_line.price_subtotal
                for bill_line in bill.line_ids:
                        amount += bill_line.credit
                amount = bill.currency_id._convert(bill.amount_untaxed, bill.company_currency_id, bill.company_id, bill.invoice_date)
                inline = [
                    # (0, 0, {'name': 'Cost', 'quantity': 1, 'price_unit': math.ceil(amount),
                    #         'discount': 0, 'account_id': 0}),
                    # (0, 0, {'name': 'Insurance', 'quantity': 1, 'price_unit': 0, 'discount': 0, 'account_id': 0}),
                    # (0, 0, {'name': 'Freight', 'quantity': 1, 'price_unit': 0, 'discount': 0, 'account_id': 0}),
                    (0, 0, {'name': 'Total CIF', 'quantity': 1, 'price_unit': 0, 'discount': 0, 'account_id': 0, 'x_custom_duty': True}), #math.ceil(amount)
                    (0, 0, {'product_id': self.env.ref('bill_of_entry.customs_duty'), 'name': 'Custom Duty', 'quantity': 1, 'price_unit': 0, 'discount': 0,
                            'account_id': 0, 'is_landed_costs_line': True}),
                    (0, 0,
                        {'name': 'Taxable Supply', 'quantity': 1, 'price_unit': 0, 'discount': 0, 'account_id': 0, 'tax_ids': [(4, paid_at_customs_tax_id.id)]}),
                    (0, 0, {'name': 'Clearing Reversal', 'quantity': 1, 'price_unit': 0, 'discount': 0, 'account_id': 0}),
                ]

                data = {
                    'partner_id': self.env.ref('bill_of_entry.customs_partner').id,
                    'type': 'in_invoice',
                    'invoice_line_ids': inline,
                    'currency_id': bill.company_currency_id.id,
                    'journal_id': self.env['ir.default'].sudo().get('account.move', 'x_customs_journal_id'),
                    'x_price_previous': 0.0
                }
                id = bill.create(data)
                id.new_id = bill.id

    def post(self):
        res = super(AccountMove, self).post()
        for move in self:
            if move.x_is_import:
                move.bill_of_entry()
        return res

    # def entry_call(self):
    #     return self.bill_of_entry()
    #
    # @api.model
    # def create(self, vals):
    #     res = super(AccountMove, self).create(vals)
    #     if 'narration' in vals:
    #         res.entry_call()
    #     return res

    # def write(self, vals):
    #     res = super(AccountMove, self).write(vals)
    #     self.entry_call()
    #     return res

    @api.onchange('currency_id')
    def currency_change(self):
        for bill in self:
            if bill.new_id and bill.currency_id != bill.company_id.currency_id and bill.counter == 0:
                for bill_line in bill.invoice_line_ids:
                    price_unit_comp = bill.currency_id._convert(bill_line.price_unit, bill.company_id.currency_id,
                                                                bill.company_id, bill.date)
                    bill_line.price_unit = price_unit_comp
                    bill.counter += 1
                # bill.invoice_line_ids._onchange_price_subtotal()
                bill._onchange_currency()

    # @api.onchange('invoice_line_ids')
    # def boe_compute(self):
    #     reverse = 0.0
    #     for move in self:
    #         if move.new_id and move.counter == 0: # and move.currency_id != move.company_id.currency_id:
    #             move.invoice_line_ids[3].price_unit = move.invoice_line_ids[0].price_unit + move.invoice_line_ids[
    #                 1].price_unit + move.invoice_line_ids[2].price_unit
    #             move.invoice_line_ids[4].price_unit = move.invoice_line_ids[3].price_unit * 0.05
    #             move.invoice_line_ids[5].price_unit = move.invoice_line_ids[3].price_unit + move.invoice_line_ids[
    #                 4].price_unit
    #             reverse = (move.invoice_line_ids[3].price_unit * 2) + move.invoice_line_ids[5].price_unit
    #             move.invoice_line_ids[6].price_unit = -reverse
    #             move.invoice_line_ids._onchange_price_subtotal()

    @api.onchange('invoice_line_ids')
    def boe_compute(self):
        reverse = 0.0
        for move in self:
            if move.new_id and move.x_price_previous != move.invoice_line_ids[0].price_unit and move.counter == 0:  # and move.currency_id != move.company_id.currency_id:
                # move.invoice_line_ids[3].price_unit = move.invoice_line_ids[0].price_unit + move.invoice_line_ids[
                #     1].price_unit + move.invoice_line_ids[2].price_unit
                move.invoice_line_ids[1].price_unit = move.invoice_line_ids[0].price_unit * 0.05
                move.invoice_line_ids[2].price_unit = move.invoice_line_ids[0].price_unit + move.invoice_line_ids[
                    1].price_unit
                reverse = move.invoice_line_ids[0].price_unit + move.invoice_line_ids[2].price_unit
                move.invoice_line_ids[3].price_unit = -reverse
                move.invoice_line_ids._onchange_price_subtotal()
                move.x_price_previous = move.invoice_line_ids[0].price_unit
                move.invoice_line_ids[2]._get_computed_taxes()



class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    currency_rate = fields.Float(related='move_id.currency_id.rate', readonly=False)
    x_custom_duty = fields.Boolean(string="Is custom duty", default=False)

    @api.onchange('price_unit')
    def some(self):
        self._get_computed_taxes()