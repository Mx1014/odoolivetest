import base64

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import re
from datetime import datetime
from odoo.tools.misc import formatLang
from functools import partial
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re


class AccountPriceExc(models.Model):
    _inherit = 'account.move.line'
    price_exc = fields.Float(compute='_price_exclusive', string='Price Exclusive', digits=(14, 3))
    discount_exc = fields.Float(compute='_discount_exclusive', string='Discount Exclusive', digits=(14, 3))

    @api.onchange('price_unit')
    def _price_exclusive(self):
        for line in self:
            line.price_exc = (line.price_unit / (100 + line.tax_ids.amount) * 100)

    @api.onchange('x_discount_amount')
    def _discount_exclusive(self):
        for line in self:
            line.discount_exc = (line.x_discount_amount / (100 + line.tax_ids.amount) * 100)


class AccountMoveGrouping(models.Model):
    _inherit = 'account.move'
    lpo_reference = fields.Char(string='LPO Reference')

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
                res[group]['name'] = line.tax_ids.name
                res[group]['tax_amount'] = line.tax_ids.amount
            # res = sorted(res.items(), key=lambda l: l[0].sequence)
            return res

    def print_tax_invoice(self):
        pickings = self.mapped('invoice_line_ids')
        if not pickings:
            raise UserError(_('Nothing to print.'))
        return self.env.ref(
            'pabs_sale_report.Tax_invoice').report_action(self)

    def _get_reconciled_info_JSON_values(self):
        res = super(AccountMoveGrouping, self)._get_reconciled_info_JSON_values()
        for payment in res:
            payment_id = self.env['account.payment'].search([('id', '=', payment['account_payment_id'])])
            move_id = self.env['account.move'].search([('id', '=', payment['move_id'])])
            payment['payment_method'] = payment_id.x_payment_methods.name or move_id.type_name
            payment['payment_ref'] = payment_id.name or move_id.name
            # payment['payment_re'] = payment_id.communication
        return res

    def attach_invoice(self):
        pdf = self.env.ref('pabs_sale_report.invoice_by_email').render_qweb_pdf(self.id)
        b64_pdf = base64.b64encode(pdf[0])
        return self.env['ir.attachment'].create({
            'name': self.name + '.pdf',
            'type': 'binary',
            'datas': b64_pdf,
            # 'datas_fname': self.sale_order_id.name + '.pdf',
            'store_fname': self.name,
            'res_model': 'account.move',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

    def action_invoice_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        invoice = self.attach_invoice()
        template = self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)
        lang = self.env.context.get('lang')
        if template and template.lang:
            lang = template._render_template(template.lang, 'account.move', self.id)
        else:
            lang = lang.code
        compose_form = self.env.ref('account.account_invoice_send_wizard_form', raise_if_not_found=False)
        ctx = {
            'default_model': 'account.move',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template),
            'default_template_id': template and template.id or False,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
            'default_attachment_ids': [(4, invoice.id)],
        }
        return {
            'name': _('Send Invoice'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.send',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }


class SaleOrderDeliveryAddress(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        res = super(SaleOrderDeliveryAddress, self)._prepare_invoice()
        res['lpo_reference'] = self.client_order_ref
        return res
