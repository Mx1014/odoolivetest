# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_history_line = fields.One2many(related='partner_id.sale_order_ids', string='Order History')
    sale_order_type = fields.Selection(string='Sale Order Type', readonly=True,
                                       selection=[('cash_memo', 'Cash Memo'), ('credit_sale', 'Credit Sale'),
                                                  ('paid_on_delivery', 'Paid on Delivery'),
                                                  ('advance_payment', 'Cash Invoice'),
                                                  ('service', 'Service')],
                                       states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                       help='Select a Sale Order Type')
    # partner_id = fields.Many2one('res.partner', default=lambda self: self.env.ref('base.public_partner').id,
    #                              domain=[('customer_rank', '!=', 0)])
    partner_id = fields.Many2one('res.partner', domain=[('customer_rank', '!=', 0)])
    user_statement_id = fields.Many2one('account.user.statement', copy=False)
    user_id = fields.Many2one(
        'res.users', string='Salesperson', index=True, tracking=2, default=False,
        domain=lambda self: [('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').id)])
    x_user_mobile = fields.Char(related="user_id.work_phone")
    x_payment_state = fields.Selection([
        ('paid', 'Paid'),
        ('not_paid', 'Not Paid'),
        ('partially_paid', 'Partially Paid')],
        string='Payment Status', compute='_compute_x_payment_state')

    @api.onchange('sale_order_type')
    def _onchange_sale_order_type_payment_terms(self):
        if self.sale_order_type in ['cash_memo', 'paid_on_delivery', 'advance_payment', 'service']:
            self.payment_term_id = self.env['account.payment.term'].search([('payment_term_type', 'in', ['so', 'both']), ('name', '=', 'Immediate Payment')], limit=1)
        elif self.sale_order_type == 'credit_sale':
            if self.partner_id:
                self.payment_term_id = self.partner_id.property_payment_term_id

    def _compute_x_payment_state(self):
        for rec in self:
            # amount_total_partial_paid = sum(rec.order_line.mapped('price_total'))
            # returns = rec.return_picking_ids.filtered(lambda p: p.state == 'done')
            # returns_qty = sum(
            #     rec.return_picking_ids.filtered(lambda p: p.state == 'done').move_line_ids_without_package.mapped(
            #         'qty_done'))
            # print(returns, returns_qty)
            if rec.x_amount_residual == 0:
                rec.x_payment_state = 'paid'
            #     if returns:
            #         if returns_qty >= order_qty:
            #             rec.x_delivery_state = 'returned'
            #         else:
            #             rec.x_delivery_state = 'partial'
            elif rec.amount_total == rec.x_amount_residual:
                rec.x_payment_state = 'not_paid'
            else:
                if rec.x_amount_residual != 0:
                    if rec.amount_total > rec.x_amount_residual:
                        rec.x_payment_state = 'partially_paid'
                    print(rec.x_payment_state, "status")
            #     else:
            #         rec.x_delivery_state = 0

    @api.onchange('sale_order_type')
    def onchange_to_remove_detail(self):
        if self.sale_order_type == 'credit_sale' and self.partner_invoice_id.id != 866839:
            self.partner_shipping_id = False
            self.partner_invoice_id = False
            self.partner_id = False

    def attach_order(self):
        pdf = self.env.ref('pabs_sale_quotation.sale_quotation_email').render_qweb_pdf(self.id)
        b64_pdf = base64.b64encode(pdf[0])
        return self.env['ir.attachment'].create({
            'name': self.name + '.pdf',
            'type': 'binary',
            'datas': b64_pdf,
            # 'datas_fname': self.sale_order_id.name + '.pdf',
            'store_fname': self.name,
            'res_model': 'sale.order',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

    def action_quotation_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self.env.ref('pabs_sale.pabs_sale_inherit_mail_template_sale_confirmation').id
        # lang = self.env.context.get('lang')
        # template = self.env['mail.template'].browse(template_id)
        order = self.attach_order()
        # if template.lang:
        #     lang = template._render_template(template.lang, 'sale.order', self.ids[0])
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            # 'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            # 'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            # 'model_description': self.with_context(lang=lang).type_name,
            'default_attachment_ids': [(4, order.id)],
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    @api.onchange('partner_id')
    def set_phone(self):
        for rec in self:
            if rec.partner_id:
                rec.phone = '%s - %s - %s' % (
                    rec.partner_id.phone or '', rec.partner_id.mobile or '', rec.partner_id.x_mobile or '')
            if not rec.partner_id.phone and not rec.partner_id.mobile and not rec.partner_id.x_mobile:
                rec.phone = ''

    @api.onchange('sale_order_type', 'partner_invoice_id')
    def domain_order_type(self):
        res = {}
        if self.sale_order_type == 'credit_sale' and self.partner_invoice_id.id != 866839:
            res['domain'] = {'partner_id': [('x_credit_customer', '=', True)]}
        else:
            res['domain'] = {'partner_id': [('customer_rank', '!=', 0)]}
        return res

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        immediate_payment_term_id = self.env['account.payment.term'].search([('payment_term_type', 'in', ['so', 'both']), ('name', '=', 'Immediate Payment')], limit=1)
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': (self.partner_id.property_payment_term_id if self.partner_id.property_payment_term_id else (immediate_payment_term_id.id if immediate_payment_term_id else False)) if self.sale_order_type == 'credit_sale' else (immediate_payment_term_id.id if immediate_payment_term_id else False),
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            # 'user_id': partner_user.id or self.env.uid
        }
        if self.env['ir.config_parameter'].sudo().get_param(
                'account.use_invoice_terms') and self.env.company.invoice_terms:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms

        # Use team of salesman if any otherwise leave as-is
        values['team_id'] = partner_user.team_id.id if partner_user and partner_user.team_id else self.team_id
        if self.partner_invoice_id.id == 866839:
            values['partner_invoice_id'] = 866839
        self.update(values)

    # partner_invoice_id = fields.Many2one(
    #     'res.partner', string='Invoice Address',
    #     readonly=True, required=False,
    #     states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
    # partner_shipping_id = fields.Many2one(
    #     'res.partner', string='Delivery Address', readonly=True, required=False,
    #     states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
    # pricelist_id = fields.Many2one(
    #     'product.pricelist', string='Pricelist', check_company=True,  # Unrequired company
    #     required=False, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    #     help="If you change the pricelist, only newly added lines will be affected.")
    # currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True,
    #                               required=False)

    # @api.model
    # def create(self, vals):
    #     if vals.get('name', _('New')) == _('New'):
    #         seq_date = None
    #         if 'date_order' in vals:
    #             seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
    #         if 'company_id' in vals:
    #             if vals['sale_order_type'] == 'service':
    #                 vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
    #                     'repair.order', sequence_date=seq_date) or _('New')
    #             else:
    #                 vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
    #                     'sale.order', sequence_date=seq_date) or _('New')
    #         else:
    #             if vals['sale_order_type'] == 'service':
    #                 vals['name'] = self.env['ir.sequence'].next_by_code('repair.order', sequence_date=seq_date) or _(
    #                     'New')
    #             else:
    #                 vals['name'] = self.env['ir.sequence'].next_by_code('sale.order', sequence_date=seq_date) or _(
    #                     'New')
    #
    #
    #     # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
    #     if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
    #         partner = self.env['res.partner'].browse(vals.get('partner_id'))
    #         addr = partner.address_get(['delivery', 'invoice'])
    #         vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
    #         vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
    #         vals['pricelist_id'] = vals.setdefault('pricelist_id',
    #                                                partner.property_product_pricelist and partner.property_product_pricelist.id)
    #     result = super(SaleOrder, self).create(vals)
    #     return result

    def action_confirm(self):
        if self.partner_id == self.env.ref('base.public_partner'):
            raise UserError(
                _("Please change the Customer, because if the customer is Public User, Sell Order can't be confirmed."))
        user_statement_id = self.env['account.user.statement'].search(
            [('user_id', '=', self.env.user.id), ('state', '=', 'open')]).id
        # if not user_statement_id:
        #     raise UserError(_("Please start a Session via Sale Terminal as you can't start selling without a session opened."))
        self.user_statement_id = user_statement_id

        # self._create_invoices()
        # return self.action_view_invoice()
        return super(SaleOrder, self).action_confirm()

    def _prepare_invoice(self):
        values = super(SaleOrder, self)._prepare_invoice()
        values['sale_order_type'] = self.sale_order_type
        values['user_statement_id'] = self.user_statement_id.id
        return values


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('price_subtotal', 'x_standard_price', 'product_uom_qty')
    def margin_get(self):
        for line in self:
            line.x_product_margin = (line.price_subtotal - (line.x_standard_price * line.product_uom_qty))

    x_product_margin = fields.Float(string='Product Margin', compute="margin_get", digits=(14, 3))
    x_standard_price = fields.Float(related="product_id.standard_price")

    route_ids = fields.Many2many('stock.location.route', string='Route', track_visibility="always")
    x_virtual_qty = fields.Float(string="Forecasted QTY")
    sale_order_type = fields.Selection(string='Sale Order Type', readonly=True,
                                       selection=[('cash_memo', 'Cash Memo'), ('credit_sale', 'Credit Sale'),
                                                  ('paid_on_delivery', 'Paid on Delivery'),
                                                  ('advance_payment', 'Cash Invoice'),
                                                  ('service', 'Service')])

    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        values['sale_order_type'] = self.order_id.sale_order_type
        return values

    """
    def _prepare_invoice_line(self):
        values = super(SaleOrderLine, self)._prepare_invoice_line()
        if self.order_id.sale_order_type == "cash_memo":
            values['account_id'] = self.product_id.income_account_id.id,
        return values
                  """

#
# class SaleOrderHistory(models.Model):
#     _name = 'sale.order.history'
#     order_history_id = fields.Many2many('sale.order', string='Order Reference')
