# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from lxml import etree
from lxml.builder import E
import json


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_order_type = fields.Selection(string='Sale Order Type',
                                       selection=[('cash_memo', 'Cash Memo'), ('credit_sale', 'Credit Sale'),
                                                  ('paid_on_delivery', 'Paid on Delivery'),
                                                  ('advance_payment', 'Cash Invoice'), ('service', 'Service')])
    user_statement_id = fields.Many2one('account.user.statement', copy=False)
    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms',
                                              domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                              readonly=True, states={'draft': [('readonly', False)]})

    @api.onchange('type')
    def _onchange_type_payment_terms(self):
        if self.type in ['out_invoice', 'in_refund', 'out_receipt']:
            return {'domain': {'invoice_payment_term_id': ['|', '&', ('payment_term_type', 'in', ['so', 'both']), ('company_id', '=', False), ('company_id', '=', self.company_id.id)]}}
        elif self.type in ['out_refund', 'in_invoice', 'in_receipt']:
            return {'domain': {'invoice_payment_term_id': ['|', '&', ('payment_term_type', 'in', ['po', 'both']), ('company_id', '=', False), ('company_id', '=', self.company_id.id)]}}
        else:
            return {'domain': {'invoice_payment_term_id': ['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)]}}

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for statement in self:
            statement.update({'user_statement_id': self.env['account.user.statement'].search(
                [('user_id', '=', self.env.user.id), ('state', '=', 'open')]).id})
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountMove, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                       toolbar=toolbar, submenu=submenu)
        type = self.env.context.get('default_type')
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            node = doc.xpath("//field[@name='partner_id']")[0]
            if type in ['out_invoice', 'out_refund']:
                node.set("context",
                         "{'res_partner_search_mode': (context.get('default_type', 'entry') in ('out_invoice', 'out_refund', 'out_receipt') and 'customer') or (context.get('default_type', 'entry') in ('in_invoice', 'in_refund', 'in_receipt') and 'supplier') or False,'show_address': 1, 'default_is_company': True, 'show_vat': True, 'default_customer_rank': 1}")
            elif type in ['in_invoice', 'in_refund']:
                node.set("context",
                         "{'res_partner_search_mode': (context.get('default_type', 'entry') in ('out_invoice', 'out_refund', 'out_receipt') and 'customer') or (context.get('default_type', 'entry') in ('in_invoice', 'in_refund', 'in_receipt') and 'supplier') or False,'show_address': 1, 'default_is_company': True, 'show_vat': True, 'default_supplier_rank': 1}")
            res['arch'] = etree.tostring(doc)
            return res
        return res
