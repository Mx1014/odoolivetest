# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from math import floor
import base64
import random


class SaleCoupon(models.Model):
    _inherit = 'sale.coupon.reward'

    reward_type = fields.Selection(selection_add=[('coupon', 'Coupon')])


class SaleCouponProgram(models.Model):
    _inherit = 'sale.coupon.program'

    promo_applicability = fields.Selection(selection_add=[('raffle', 'Raffle Draw')])
    x_third_party_code = fields.Boolean(string="Third Part Coupons", default=False)
    x_max_coupons = fields.Integer(string="Maximum Coupons")
    x_template_id = fields.Many2one('mail.template', 'Use template', index=True)
    x_report_id = fields.Many2one('ir.actions.report', string="Report", index=True, store=True)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    x_coupon_count = fields.Integer(compute='_compute_coupon_count', copy=False)

    def _create_new_no_code_promo_reward_lines(self):
        order = self
        prog = self.env['sale.coupon.program'].search(
            [('promo_applicability', '=', 'raffle'), ('active', '!=', False)])
        for programs in prog:
            programs = programs and programs._filter_on_mimimum_amount(order)
            programs = programs and programs._filter_programs_on_products(order)
            order_lines = order.order_line.filtered(lambda line: line.product_id) - order._get_reward_lines()
            products = order_lines.mapped('product_id')
            products_qties = dict.fromkeys(products, 0)
            for line in order_lines:
                products_qties[line.product_id] += line.product_uom_qty
                valid_products = programs._get_valid_products(products)
            amount = sum(order.order_line.filtered(lambda line: line.product_id.id in valid_products.ids).mapped('price_total'))
            qty = sum(order.order_line.filtered(lambda line: line.product_id.id in valid_products.ids).mapped('product_uom_qty'))
            for program in programs:
                if order.x_amount_residual == 0.0 and order.state == 'sale' and order.x_coupon_count == 0:
                    order.no_code_promo_program_ids = False

                    error_status = program._check_promo_code(order, False)
                    if not error_status.get('error'):
                        if program.promo_applicability == 'raffle':
                            if program.rule_minimum_amount > 0.0:
                                no_of_coupon = amount / program.rule_minimum_amount
                                while floor(no_of_coupon):
                                    if program.x_third_party_code:
                                        order._third_part_reward_coupon(program)
                                    else:
                                        order._create_reward_coupon(program)
                                    no_of_coupon -= 1
                            if program.x_third_party_code and program.rule_minimum_amount == 0.0:
                                # if qty and program.x_max_coupons > 0:
                                #     for ran in range(int(qty)):
                                #         if ran <= program.x_max_coupons:
                                #             order._third_part_reward_coupon(program)
                                #             print(ran, qty)
                                #elif qty and program.x_max_coupons == 0:
                                if qty and order.x_amount_residual == 0.0:
                                    ran = 1
                                    while ran <= int(qty):
                                        order._third_part_reward_coupon(program)
                                        ran += 1
                        order.no_code_promo_program_ids |= program
        return super(SaleOrder, self)._create_new_no_code_promo_reward_lines()


    def _third_part_reward_coupon(self, program):
        # if there is already a coupon that was set as expired, reactivate that one instead of creating a new one
        coupon = self.env['sale.coupon'].search([
            ('program_id', '=', program.id),
            ('state', '=', 'new'),
            ('partner_id', '=', False),
            ('order_id', '=', False),
        ], limit=1)
        if coupon:
            coupon.write({
                'state': 'reserved',
                'partner_id': self.partner_id.id,
                'order_id': self.id,
                })
        else:
            # coupon = self.env['sale.coupon'].create({
            #     'program_id': program.id,
            #     'state': 'reserved',
            #     'partner_id': self.partner_id.id,
            #     'order_id': self.id,
            # })
            raise Warning('No coupon available. Please contact marketing department')
        self.generated_coupon_ids |= coupon
        return coupon




    def _compute_coupon_count(self):
        for program in self:
            program.x_coupon_count = self.env['sale.coupon'].search_count([('order_id', '=', program.id)])

    def action_view_coupons(self):
        return {
            'name': _('Coupons'),
            'res_model': 'sale.coupon',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('sale_coupon.sale_coupon_view_tree').id, 'tree'),
                (self.env.ref('sale_coupon.sale_coupon_view_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('order_id', '=', self.id)],
        }

class SaleCoupons(models.Model):
    _inherit = 'sale.coupon'

    @api.model
    def _generate_code(self):
        """Generate a 20 char long pseudo-random string of digits for barcode
        generation.

        A decimal serialisation is longer than a hexadecimal one *but* it
        generates a more compact barcode (Code128C rather than Code128A).

        Generate 8 bytes (64 bits) barcodes as 16 bytes barcodes are not
        compatible with all scanners.
         """
        return str(random.getrandbits(64))

    customer_cpr = fields.Char(string='Cpr', related='partner_id.x_cpr')
    customer_phone = fields.Char(string='Phone', related='partner_id.phone')
    customer_mobile = fields.Char(string='Mobile', related='partner_id.mobile')
    customer_whatsapp_number = fields.Char(string='Whatsapp Number', related='partner_id.x_whatsapp_mobile')
    customer_invoice = fields.Many2many(string='Invoice Number', related='order_id.invoice_ids')
    coupon_send = fields.Boolean(string='Coupon Send')
    related_x_payment_state = fields.Selection([
        ('paid', 'Paid'),
        ('not_paid', 'Not Paid'),
        ('partially_paid', 'Partially Paid')],
        string='Payment Status', compute='_compute_related_x_payment_state')
    x_state = fields.Char(string='Payment state', default='payment_state')

    @api.depends('order_id')
    def payment_state(self):
        for rec in self:
            rec.x_state = rec.order_id.x_payment_state

    def _compute_related_x_payment_state(self):
        self.payment_state()
        for rec in self:
            rec.related_x_payment_state = \
                rec.order_id.x_payment_state
    code = fields.Char(default=_generate_code, required=True, readonly=False, store=True)
    code_url = fields.Char(string="Code Url", store=True, copy=False)

    def action_coupons_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        coupons = []
        template = self.env.ref('sale_coupon.mail_template_sale_coupon', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        active_id = self._context.get('active_ids')
        for pdf in self.search([('id', 'in', active_id)]):
            val = self.attach_coupons(pdf)
            coupons.append(val.id)
        ctx = dict(
            default_model='sale.coupon',
            default_res_id=active_id[0],
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            default_attachment_ids=[(6, 0, coupons)],
            custom_layout='mail.mail_notification_light',
            force_email=True,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def attach_coupons(self, id):
        #pdf = self.env.ref('sale_coupon.report_coupon_code').render_qweb_pdf(id.id)
        pdf = id.program_id.x_report_id.render_qweb_pdf(id.id)
        b64_pdf = base64.b64encode(pdf[0])
        return self.env['ir.attachment'].create({
            'name': id.code + '.pdf',
            'type': 'binary',
            'datas': b64_pdf,
            'store_fname': id.code,
            'res_model': 'sale.coupon',
            'res_id': id.id,
            'mimetype': 'application/pdf',
        })
