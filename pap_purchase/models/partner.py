import base64

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase
from serial import tools


class Purchase(models.Model):
    _inherit = 'purchase.order'

    def attach_sale_order(self):
        if self.x_sale_order:
            pdf = self.env.ref('pabs_sale_quotation.sale_quotation_email').render_qweb_pdf(self.x_sale_order.ids)
            b64_pdf = base64.b64encode(pdf[0])
            return self.env['ir.attachment'].create({
                'name': self.x_sale_order.name + '.pdf',
                'type': 'binary',
                'datas': b64_pdf,
                # 'datas_fname': self.sale_order_id.name + '.pdf',
                'store_fname': self.x_sale_order.name,
                'res_model': 'sale.order',
                'res_id': self.x_sale_order.id,
                'mimetype': 'application/pdf',
            })

    # def action_rfq_send(self):
    #     res = super(Purchase, self).action_rfq_send()
    #     sale_order_id = 0
    #     sale_order = self.attach_sale_order()
    #     if sale_order:
    #         sale_order_id = sale_order.id
    #     ctx = dict(self.env.context or {})
    #     ctx.update({
    #         'default_attachment_ids': [(4, sale_order_id)],
    #     })
    #     return res

    def action_rfq_send(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        sale_order = self.attach_sale_order()
        if sale_order:
            self.ensure_one()
            sale_order_id = 0
            if sale_order:
                sale_order_id = sale_order.ids
            ir_model_data = self.env['ir.model.data']
            try:
                if self.env.context.get('send_rfq', False):
                    template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase')[1]
                else:
                    template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase_done')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
            ctx = dict(self.env.context or {})
            ctx.update({
                'default_model': 'purchase.order',
                'active_model': 'purchase.order',
                'active_id': self.ids[0],
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'default_attachment_ids': [(6, 0, sale_order_id)],
                'custom_layout': "mail.mail_notification_paynow",
                'force_email': True,
                'mark_rfq_as_sent': True,
            })
            # In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
            # object. Therefore, we pass the model description in the context, in the language in which
            # the template is rendered.
            lang = self.env.context.get('lang')
            if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
                template = self.env['mail.template'].browse(ctx['default_template_id'])
                if template and template.lang:
                    lang = template._render_template(template.lang, ctx['default_model'], ctx['default_res_id'])

            self = self.with_context(lang=lang)
            if self.state in ['draft', 'sent']:
                ctx['model_description'] = _('Request for Quotation')
            else:
                ctx['model_description'] = _('Purchase Order')

            return {
                'name': _('Compose Email'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
                'context': ctx,
            }
        else:
            self.ensure_one()
            ir_model_data = self.env['ir.model.data']
            try:
                if self.env.context.get('send_rfq', False):
                    template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase')[1]
                else:
                    template_id = ir_model_data.get_object_reference('purchase', 'email_template_edi_purchase_done')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
            ctx = dict(self.env.context or {})
            ctx.update({
                'default_model': 'purchase.order',
                'active_model': 'purchase.order',
                'active_id': self.ids[0],
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'custom_layout': "mail.mail_notification_paynow",
                'force_email': True,
                'mark_rfq_as_sent': True,
            })

            # In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
            # object. Therefore, we pass the model description in the context, in the language in which
            # the template is rendered.
            lang = self.env.context.get('lang')
            if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
                template = self.env['mail.template'].browse(ctx['default_template_id'])
                if template and template.lang:
                    lang = template._render_template(template.lang, ctx['default_model'], ctx['default_res_id'])

            self = self.with_context(lang=lang)
            if self.state in ['draft', 'sent']:
                ctx['model_description'] = _('Request for Quotation')
            else:
                ctx['model_description'] = _('Purchase Order')

            return {
                'name': _('Compose Email'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
                'context': ctx,
            }

    @api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = 0.0
            val = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                total = line.price_unit * line.product_qty - line.x_discount_amount
                # if line.taxes_id.price_include:
                tax_calculate = (total * (1 + ((line.taxes_id.amount if line.taxes_id else 0) / 100))) - total
                val += tax_calculate
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': val,
                'amount_total': amount_untaxed + val,
            })

    def _set_purchase_type(self):
        if (self.env['res.users'].has_group('purchase.group_purchase_user') and not self.env['res.users'].has_group(
                'pap_purchase.group_oversees')) or self.env['res.users'].has_group(
            'purchase.group_purchase_manager'):
            return 'Local'
        else:
            return 'Oversees'

    @api.model
    def _default_picking_type(self):
        return False

    # def _set_purchase_readonly(self):
    #     if self.env['res.users'].has_group('purchase.group_purchase_user'):
    #         return "0"
    #     else:
    #         return "1"

    #
    # @api.model
    # def _populat_choice(self):
    #     choices = [
    #         ('Local', 'Local')
    #     ]
    #     if self.env['res.users'].has_group('pap_purchase.group_oversees'):
    #         choices = [
    #             ('Oversees', 'Oversees')
    #         ]
    #     return choices

   # @api.depends('product_id')
    #def _x_compute_currency_id(self):
        #for rec in self:
            #company_id = self.env.user.company_id
            #rec.currency_id = company_id.currency_id

    x_sale_order = fields.Many2one('sale.order', string='Sale Order')
    currency_id = fields.Many2one('res.currency', string='Currency')
    x_partner_code = fields.Char(string='Partner Code', related='partner_id.x_code')
    purchase_type = fields.Selection([('Local', 'Local')
                                         , ('Oversees', 'Oversees')], string='Purchase Type',
                                     readonly=True, track_visibility="always", default=_set_purchase_type)
    # purchase_type = fields.Selection(string="purchase_type", selection=_populat_choice)

    # narration = fields.Char(string='Narration')
    pick_type_id = fields.Many2one('stock.picking.type', 'Pick Type', track_visibility="always")
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=Purchase.READONLY_STATES,
                                      required=False,
                                      domain="[('is_stock_receive_operation', '=', True)]",
                                      default=False,
                                      help="This will determine operation type of incoming shipment",
                                      track_visibility="always")
    incoterm_id = fields.Many2one('account.incoterms', 'Incoterm', track_visibility="always")
    partner_id = fields.Many2one('res.partner',
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('supplier_rank', '!=', 0)]")

    @api.onchange('company_id')
    def _onchange_company_id(self):
        res = super(Purchase, self)._onchange_company_id()
        self.picking_type_id = False
        return res


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order.line'

    x_discount_amount = fields.Float(string="Discount", digits=(14, 3), compute='amount_disc_get')
    discount = fields.Float('Discount (%)', digits='Discount', default=0.0)
    price_exc = fields.Float(compute='_price_exc', string='Price Exclusive', digits=(14, 3))

    # @api.onchange('discount', 'price_unit', 'product_qty')
    # @api.depends('product_qty', 'price_unit', 'discount')
    # def amount_disc_get(self):
    #     for line in self:
    #         line.x_discount_amount = ((line.price_unit * line.product_qty) / 100) * line.discount

    @api.onchange('discount', 'price_unit', 'product_qty', 'taxes_id')
    @api.depends('product_qty', 'price_unit', 'discount', 'taxes_id')
    def amount_disc_get(self):
        for line in self:
            line.x_discount_amount = ((line.price_unit * line.product_qty) / 100) * line.discount

    @api.onchange('x_discount_amount', 'price_unit', 'product_qty', 'taxes_id')
    def perc_disc_from_amount(self):
        for line in self:
            if ((line.price_unit * line.product_qty) / 100):
                line.discount = line.x_discount_amount / ((line.price_unit * line.product_qty) / 100)

    @api.depends('product_qty', 'price_unit', 'discount', 'taxes_id')
    def _compute_amount(self):
        res = super(PurchaseOrder, self)._compute_amount()
        for line in self:
            total = line.price_unit * line.product_qty - line.x_discount_amount
            taxes = total / (1 + ((line.taxes_id.amount if line.taxes_id else 0) / 100))
            line.price_subtotal = total

        #     line.update({
        #         'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
        #         'price_total': taxes['total_included'],
        #         # 'price_subtotal': taxes['total_excluded'] - line.x_discount_amount,
        #         'price_subtotal': line.product_qty * line.price_unit - (
        #                 line.discount * (line.product_qty * line.price_unit) / 100),
        #         # 'price_subtotal': ((line.price_unit * line.product_qty) / 100) * line.discount,
        #     })
        # return res

    @api.onchange('product_id')
    def onchange_for_taxes(self):
        self.taxes_id = self.product_id.supplier_taxes_id


class DeliveryLocation(models.Model):
    _inherit = 'stock.location'
    partner_id = fields.Many2one('res.partner', string='Delivery Address')


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    is_stock_receive_operation = fields.Boolean(string='Is Stock Receipt Operation', default=False)

    @api.onchange('code')
    def x_on_change_code(self):
        self.is_stock_receive_operation = False


class Mails(models.TransientModel):
    _inherit = 'mail.compose.message'
    is_stock_receive_operation = fields.Boolean(string='Is Stock Receipt Operation', default=False)

    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        """ - mass_mailing: we cannot render, so return the template values
            - normal mode: return rendered values
            /!\ for x2many field, this onchange return command instead of ids
        """
        po = self.env['purchase.order'].search([('id', '=', self.res_id)])
        so_report = po.attach_sale_order()
        print('onchange_template_id')
        print(po, "POOOOO")
        if template_id and composition_mode == 'mass_mail':
            template = self.env['mail.template'].browse(template_id)
            fields = ['subject', 'body_html', 'email_from', 'reply_to', 'mail_server_id']
            values = dict((field, getattr(template, field)) for field in fields if getattr(template, field))
            if template.attachment_ids:
                values['attachment_ids'] = [att.id for att in template.attachment_ids]
            if template.mail_server_id:
                values['mail_server_id'] = template.mail_server_id.id
            if template.user_signature and 'body_html' in values:
                signature = self.env.user.signature
                values['body_html'] = tools.append_content_to_html(values['body_html'], signature, plaintext=False)
        elif template_id:
            values = self.generate_email_for_composer(template_id, [res_id])[res_id]
            # transform attachments into attachment_ids; not attached to the document because this will
            # be done further in the posting process, allowing to clean database if email not send
            attachment_ids = []
            Attachment = self.env['ir.attachment']
            for attach_fname, attach_datas in values.pop('attachments', []):
                data_attach = {
                    'name': attach_fname,
                    'datas': attach_datas,
                    'res_model': 'mail.compose.message',
                    'res_id': 0,
                    'type': 'binary',  # override default_type from context, possibly meant for another model!
                }
                attachment_ids.append(Attachment.create(data_attach).id)
                if so_report:
                    if values.get('attachment_ids', []) or attachment_ids:
                        values['attachment_ids'] = [(6, 0, values.get('attachment_ids', []) + attachment_ids + so_report.ids)]
                else:
                    if values.get('attachment_ids', []) or attachment_ids:
                        values['attachment_ids'] = [
                            (6, 0, values.get('attachment_ids', []) + attachment_ids)]
        else:
            default_values = self.with_context(default_composition_mode=composition_mode, default_model=model,
                                               default_res_id=res_id).default_get(
                ['composition_mode', 'model', 'res_id', 'parent_id', 'partner_ids', 'subject', 'body', 'email_from',
                 'reply_to', 'attachment_ids', 'mail_server_id'])
            values = dict((key, default_values[key]) for key in
                          ['subject', 'body', 'partner_ids', 'email_from', 'reply_to', 'attachment_ids',
                           'mail_server_id'] if key in default_values)

        if values.get('body_html'):
            values['body'] = values.pop('body_html')

        # This onchange should return command instead of ids for x2many field.
        values = self._convert_to_write(values)

        return {'value': values}
