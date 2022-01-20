from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import re
from datetime import datetime
from odoo.tools.misc import formatLang
from functools import partial


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_before_disc_price = fields.Float(string='Price Exc. Disc', compute="compute_price_before_discount",
                                       digits=(14, 3))
    x_price_tax = fields.Float(string='Tax Amount', compute="compute_price_before_discount", digits=(14, 3))
    x_discount_amount = fields.Float(string="Discount", digits=(14, 3), compute="amount_disc_get")
    x_vat = fields.Char(related='partner_id.vat')
    x_document_type = fields.Selection(related="move_id.type")
    x_origin_date = fields.Date(string="Origin Date", related="move_id.reversed_entry_id.invoice_date")

    @api.onchange('discount', 'price_unit', 'quantity')
    @api.depends('quantity', 'price_unit', 'discount')
    def amount_disc_get(self):
        for line in self:
            line.x_discount_amount = ((line.price_unit * line.quantity) / 100) * line.discount

    @api.onchange('x_discount_amount', 'price_unit', 'quantity')
    def perc_disc_from_amount(self):
        for line in self:
            if ((line.price_unit * line.quantity) / 100):
                line.discount = line.x_discount_amount / ((line.price_unit * line.quantity) / 100)

    @api.onchange('quantity', 'price_unit')
    @api.depends('quantity', 'price_unit')
    def compute_price_before_discount(self):
        for line in self:
            line.x_before_disc_price = line.price_unit * line.quantity
            line.x_price_tax = line.price_total - line.price_subtotal


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_before_disc_price = fields.Float(string='Price Exc. Disc', compute="compute_price_before_discount",
                                       digits=(14, 3))
    x_discount_amount = fields.Float(string="Discount", digits=(14, 3), compute="amount_disc_get")

    @api.onchange('discount', 'price_unit', 'product_uom_qty')
    @api.depends('product_uom_qty', 'price_unit', 'discount')
    def amount_disc_get(self):
        for line in self:
            line.x_discount_amount = ((line.price_unit * line.product_uom_qty) / 100) * line.discount

    @api.onchange('x_discount_amount', 'price_unit', 'product_uom_qty')
    def perc_disc_from_amount(self):
        for line in self:
            if ((line.price_unit * line.product_uom_qty) / 100):
                line.discount = line.x_discount_amount / ((line.price_unit * line.product_uom_qty) / 100)

    @api.onchange('product_uom_qty', 'price_unit')
    @api.depends('product_uom_qty', 'price_unit')
    def compute_price_before_discount(self):
        for line in self:
            line.x_before_disc_price = line.price_unit * line.product_uom_qty

    def _prepare_invoice_line(self):
        values = super(SaleOrderLine, self)._prepare_invoice_line()
        values['x_discount_amount'] = self.x_discount_amount
        values['x_price_tax'] = self.price_tax
        return values


class Sale(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        values = super(Sale, self)._prepare_invoice()
        SALE_ORDER_TYPE = {
            'cash_memo': self.env.ref('pabs_account.type_cashmemo').ids,
            'credit_sale': self.env.ref('pabs_account.type_credit').ids,
            'paid_on_delivery': self.env.ref('pabs_account.type_pod').ids,
            'advance_payment': self.env.ref('pabs_account.type_cashinvoice').ids,
            'service': self.env.ref('pabs_account.type_service').ids,

        }
        journals = self.env['account.journal']
        journal = journals.search([('x_sale_order_type_ids', 'in', SALE_ORDER_TYPE[self.sale_order_type])], limit=1).id
        if journal:
            values['journal_id'] = journal
        return values


class AccountMove(models.Model):
    _inherit = 'account.move'

    reversed_entry_id = fields.Many2one('account.move', string="Document No", readonly=True, copy=False)
    x_show_tax = fields.Boolean(default=False, copy=False, compute="show_tax_qweb_line")
    x_bill_origin = fields.Char(string='L.P.O')
    reversed_entry_no = fields.Char(string='Invoice Reference')
    reversed_entry_date = fields.Date(string='Invoice Date')
    type = fields.Selection(selection_add=[
        ('adjustment', 'Adjustment'),
        ('apportionment', 'Apportionment')])
    x_previous_period = fields.Boolean(string="Previous Tax Period")
    x_cn_reason = fields.Char(string="Reason")
    x_user_mobile = fields.Char(related="invoice_user_id.work_phone")
    x_receivable = fields.Boolean(string="Receivable", default=False)
    x_payable = fields.Boolean(string="Payable", default=False)
    x_due_am = fields.Monetary(string='Paid Amount', compute='compute_invoiceids')
    x_shipping_address = fields.Text('Address', compute='_compute_x_address', store=True)

    @api.onchange('x_receivable', 'invoice_line_ids')
    def on_change_x_receivable(self):
        if self.type in ['in_invoice', 'in_refund']:
            if self.x_receivable:
                if self.partner_id.property_account_receivable_id and self.partner_id.property_account_payable_id:
                    if self.line_ids:
                        for line in self.line_ids:
                            if line.account_id == self.partner_id.property_account_payable_id:
                                line.account_id = self.partner_id.property_account_receivable_id
            else:
                if self.partner_id.property_account_receivable_id and self.partner_id.property_account_payable_id:
                    if self.line_ids:
                        for line in self.line_ids:
                            if line.account_id == self.partner_id.property_account_receivable_id:
                                line.account_id = self.partner_id.property_account_payable_id

    @api.onchange('x_payable', 'invoice_line_ids')
    def on_change_x_payable(self):
        if self.type in ['out_invoice', 'out_refund']:
            if self.x_payable:
                if self.partner_id.property_account_receivable_id and self.partner_id.property_account_payable_id:
                    if self.line_ids:
                        for line in self.line_ids:
                            if line.account_id == self.partner_id.property_account_receivable_id:
                                line.account_id = self.partner_id.property_account_payable_id
            else:
                if self.partner_id.property_account_receivable_id and self.partner_id.property_account_payable_id:
                    if self.line_ids:
                        for line in self.line_ids:
                            if line.account_id == self.partner_id.property_account_payable_id:
                                line.account_id = self.partner_id.property_account_receivable_id


    x_brand = fields.Char(string="Brand", compute="partner_ladger_brand", store=1)

    @api.depends('invoice_line_ids')
    def partner_ladger_brand(self):
        for rec in self:
            if rec.invoice_line_ids:
                for record in rec.invoice_line_ids[0]:
                    rec.x_brand = record.product_id.product_brand_id.name
            else:
                rec.x_brand = ''

    def compute_invoiceids(self):
       for line in self:
           line.x_due_am = 0
           info = line._get_reconciled_info_JSON_values()
           for payment in info:
               if self._context.get('active_id') == payment['account_payment_id']:
                   line.x_due_am = payment['amount']
               elif payment['amount'] == 0:
                   line.x_due_am = 0

    @api.depends('partner_shipping_id')
    def _compute_x_address(self):
        for rec in self:
            address = ''
            if rec.partner_shipping_id:
                if rec.partner_shipping_id.name:
                    address += rec.partner_shipping_id.name
                if rec.partner_shipping_id.street_number:
                    address += ', House: ' + rec.partner_shipping_id.street_number
                if rec.partner_shipping_id.x_address_block.name:
                    address += ', Block: ' + rec.partner_shipping_id.x_address_block.name
                if rec.partner_shipping_id.x_address_road.name:
                    address += ', Road: ' + rec.partner_shipping_id.x_address_road.name
                if rec.partner_shipping_id.x_block_area:
                    address += ', Area: ' + rec.partner_shipping_id.x_block_area
                if rec.partner_shipping_id.x_flat:
                    address += ', Flat: ' + rec.partner_shipping_id.x_flat
                if rec.partner_shipping_id.x_gate:
                    address += ', Gate: ' + rec.partner_shipping_id.x_gate
                if rec.partner_shipping_id.city:
                    address += ', City: ' + rec.partner_shipping_id.city
                if rec.partner_shipping_id.state_id.name:
                    address += ', State: ' + rec.partner_shipping_id.state_id.name
                if rec.partner_shipping_id.zip:
                    address += ', Zip: ' + rec.partner_shipping_id.zip
                if rec.partner_shipping_id.mobile:
                    address += ', Mobile: ' + rec.partner_shipping_id.mobile
                if rec.partner_shipping_id.phone:
                    address += ', Phone: ' + rec.partner_shipping_id.phone
            if address:
                rec.x_shipping_address = address
            else:
                rec.x_shipping_address = False
    # def attach_invoice(self):
    #     pdf = self.env.ref('pabs_repair.complaint_form_by_email').render_qweb_pdf(self.id)
    #     b64_pdf = base64.b64encode(pdf[0])
    #     return self.env['ir.attachment'].create({
    #         'name': self.name + '.pdf',
    #         'type': 'binary',
    #         'datas': b64_pdf,
    #         # 'datas_fname': self.sale_order_id.name + '.pdf',
    #         'store_fname': self.name,
    #         'res_model': 'account.move',
    #         'res_id': self.id,
    #         'mimetype': 'application/pdf',
    #     })
    #
    # def action_invoice_sent(self):
    #     """ Open a window to compose an email, with the edi invoice template
    #         message loaded by default
    #     """
    #     self.ensure_one()
    #     template = self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)
    #     lang = get_lang(self.env)
    #     if template and template.lang:
    #         lang = template._render_template(template.lang, 'account.move', self.id)
    #     else:
    #         lang = lang.code
    #     compose_form = self.env.ref('account.account_invoice_send_wizard_form', raise_if_not_found=False)
    #     ctx = dict(
    #         default_model='account.move',
    #         default_res_id=self.id,
    #         default_use_template=bool(template),
    #         default_template_id=template and template.id or False,
    #         default_composition_mode='comment',
    #         mark_invoice_as_sent=True,
    #         custom_layout="mail.mail_notification_paynow",
    #         model_description=self.with_context(lang=lang).type_name,
    #         force_email=True
    #     )
    #     return {
    #         'name': _('Send Invoice'),
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'account.invoice.send',
    #         'views': [(compose_form.id, 'form')],
    #         'view_id': compose_form.id,
    #         'target': 'new',
    #         'context': ctx,
    #     }

    @api.depends('invoice_line_ids')
    def show_tax_qweb_line(self):
        for invoice in self:
            invoice.x_show_tax = False
            for line in invoice.invoice_line_ids:
                if line.tax_ids:
                    invoice.x_show_tax = True

    def grouping(self):
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(formatLang, self.with_context(lang=order.partner_id.lang).env, currency_obj=currency)
            res = {}
            for line in order.invoice_line_ids:
                group = line.tax_ids.name
                res.setdefault(group, {'amount': 0.0, 'base': 0.0, 'desc': ''})
                res[group]['amount'] += order.currency_id._convert(line['x_price_tax'], order.company_id.currency_id,
                                                                   order.company_id, order.date)
                res[group]['base'] += order.currency_id._convert(line['price_subtotal'], order.company_id.currency_id,
                                                                 order.company_id, order.date)
                res[group]['desc'] = line.tax_ids.description
            # res = sorted(res.items(), key=lambda l: l[0].sequence)
            return res

    @api.onchange('sale_order_type')
    def onchange_sale_type(self):
        SALE_ORDER_TYPE = {
            'cash_memo': self.env.ref('pabs_account.type_cashmemo').ids,
            'credit_sale': self.env.ref('pabs_account.type_credit').ids,
            'paid_on_delivery': self.env.ref('pabs_account.type_pod').ids,
            'advance_payment': self.env.ref('pabs_account.type_cashinvoice').ids,
            'service': self.env.ref('pabs_account.type_service').ids,

        }
        journals = self.env['account.journal']
        for move in self:
            if move.type in ['out_invoice', 'out_refund'] and move.sale_order_type:
                journal = journals.search([('x_sale_order_type_ids', 'in', SALE_ORDER_TYPE[move.sale_order_type])],
                                          limit=1).id
                if journal:
                    move.journal_id = journal

    # @api.onchange('journal_id','id')
    # def onchange_journal(self):
    #     for move in self:
    #         move.sale_order_type = move.journal_id.sale_order_type

    @api.onchange('x_previous_period', 'line_ids', 'invoice_line_ids', 'currency_id', 'journal_id')
    def _onchange_previous_period(self):
        for line in self.mapped('line_ids'):
            if line.tax_ids:
                for tax in line.tax_ids:
                    for tag in tax.refund_repartition_line_ids:
                        if self.type == 'out_refund':
                            if self.x_previous_period:
                                if line.tag_ids.id == tag.tag_ids.id:
                                    if tag.x_tag_custom_ids:
                                        line.tag_ids = [(6, 0, tag.x_tag_custom_ids.ids)]
                            else:
                                self._recompute_tax_lines()

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.x_previous_period:
            self._onchange_previous_period()
        return res

    def _reverse_moves(self, default_values_list=None, cancel=False):
        reverse_moves = super(AccountMove, self)._reverse_moves(default_values_list, cancel)
        reverse_moves.update({
            'reversed_entry_no': reverse_moves.reversed_entry_id.name,
            'reversed_entry_date': reverse_moves.reversed_entry_id.invoice_date,
        })
        return reverse_moves


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    sale_order_type = fields.Selection(string='Sale Order Type', selection=[('cash_memo', 'Cash Memo'),
                                                                            ('credit_sale', 'Credit Sale'),
                                                                            ('paid_on_delivery', 'Paid on Delivery'),
                                                                            ('advance_payment', 'Cash Invoice'),
                                                                            ('service', 'Service')],
                                       help='Select a Sale Order Type')

    x_sale_order_type_ids = fields.Many2many('order.sale.type', string='Sale Order Type')


class SaleOrderType(models.Model):
    _name = 'order.sale.type'
    _description = 'sale order type'

    name = fields.Char(string="Name")


class AccountTaxRepartitionLine(models.Model):
    _inherit = 'account.tax.repartition.line'

    x_tag_custom_ids = fields.Many2many(string="Tax Grids Adjustment", comodel_name='account.account.tag',
                                        domain=[('applicability', '=', 'taxes')], copy=True, relation="custom_tag")

# class ReportPartnerLedgers(models.AbstractModel):
#     _inherit = "account.report"
#
#     def _get_columns_name(self, options):
#         columns = [
#             {},
#             {'name': _('JRNL')},
#             {'name': _('Account')},
#             {'name': _('Ref')},
#             {'name': _('lpo_reference')},
#             {'name': _('Due Date'), 'class': 'date'},
#             {'name': _('Matching Number')},
#             {'name': _('Initial Balance'), 'class': 'number'},
#             {'name': _('Debit'), 'class': 'number'},
#             {'name': _('Credit'), 'class': 'number'}]
#
#         if self.user_has_groups('base.group_multi_currency'):
#             columns.append({'name': _('Amount Currency'), 'class': 'number'})
#
#         columns.append({'name': _('Balance'), 'class': 'number'})
#
#         return columns
