from odoo import models, fields, api, _
from odoo.exceptions import Warning




class Helpdesk(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.onchange('sale_order_id')
    def set_product_id(self):
        res = {}
        ids = []
        if self.sale_order_id:
            for rec in self.sale_order_id.mapped("order_line"):
                ids.append(rec.product_id.id)

            res["domain"] = {'product_id': [("id", "in", ids), ('type', '=', 'product')]}

            return res
        else:
            return self.set_customer()

    @api.onchange('partner_id')
    def set_customer(self):
        res = {}
        ids = self.env['sale.order'].search(
            [('partner_id', '=', self.partner_id.id)])
        prod_ids = []
        for rec in ids:
            for line in rec.order_line:
                prod_ids += line.product_id.ids
        res["domain"] = {'product_id': [("id", "in", prod_ids), ('type', '=', 'product')]}

        return res

    @api.onchange('product_id')
    def set_customer_sale_order(self):
        res = {}
        ids = self.env['sale.order'].search(
            [('partner_id', '=', self.partner_id.id)])
        sale_ids = []
        if self.product_id:
            for rec in ids:
                for line in rec.order_line:
                    if line.product_id.id == self.product_id.id:
                        sale_ids += rec.ids
            res["domain"] = {'sale_order_id': [("id", "in", sale_ids)]}
            return res
        else:
            return self._onchange_partner_id_domain_sale_order_id()

    def _find_mail_template(self, force_confirmation_template=False):
        template_id = False
        if not template_id:
            template_id = self.env['ir.model.data'].xmlid_to_res_id('helpdesk.new_ticket_request_email_template',
                                                                    raise_if_not_found=False)
        return template_id


    # def action_mail_send_To_Customer(self):
    #     ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
    #     self.ensure_one()
    #     template_id = self._find_mail_template()
    #     lang = self.env.context.get('lang')
    #     template = self.env['mail.template'].browse(template_id)
    #     if template.lang:
    #         lang = template._render_template(template.lang, 'helpdesk.ticket', self.ids[0])
    #     ctx = {
    #         'default_model': 'helpdesk.ticket',
    #         'default_res_id': self.ids[0],
    #         'default_use_template': bool(template_id),
    #         'default_template_id': template_id,
    #         # 'default_partner_ids': self.brand_agent.ids,
    #         'default_composition_mode': 'comment',
    #         # 'mark_so_as_sent': True,
    #         'custom_layout': "mail.mail_notification_paynow",
    #         # 'proforma': self.env.context.get('proforma', False),
    #         'force_email': True,
    #         # 'model_description': self.with_context(lang=lang).type_name,
    #     }
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'mail.compose.message',
    #         'views': [(False, 'form')],
    #         'view_id': False,
    #         'target': 'new',
    #         'context': ctx,
    #
    #     }

    def action_mail_send_To_Agent(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self.env.ref('pabs_helpdesk.pabs_helpdesk_email_template').id
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        template.send_mail(self.id, force_send=True)
        if template.lang:
            lang = template._render_template(template.lang, 'helpdesk.ticket', self.ids[0])
        ctx = {
            'default_model': 'helpdesk.ticket',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_partner_ids': self.brand_agent.ids,
            'default_composition_mode': 'comment',
            # 'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            # 'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            # 'model_description': self.with_context(lang=lang).type_name,
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

    def Check_warranty(self):
        return {
            'name': _('Warranty'),
            'domain': ['&', ('order_id', '=', self.sale_order_id.id), ('product_id', '=', self.product_id.id)],
            'res_model': 'warranty.line',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def get_warranty_count(self):
        count = self.env['warranty.line'].search_count(
            ['&', ('order_id', '=', self.sale_order_id.id), ('product_id', '=', self.product_id.id)])
        self.warranty_count = count

    @api.onchange('product_id')
    def onchange_warranty_reference(self):
        res = {}
        ids = self.env['warranty.line'].search(
            ['&', ('order_id', '=', self.sale_order_id.id), ('product_id', '=', self.product_id.id)])
        prod_ids = []
        for rec in ids:
            prod_ids.append(rec.id)
        res["domain"] = {'warranty_sequence': [("id", "in", prod_ids)]}

        return res

    @api.onchange('warranty_sequence')
    def onchange_warranty_end_date(self):
        x = self.env['warranty.line'].search(
            ['&', ('order_id', '=', self.sale_order_id.id), ('product_id', '=', self.product_id.id),
             ('id', '=', self.warranty_sequence.id)])
        if x:
            for rec in x:
                self.warranty_end_date = rec.date_done
                self.warranty_status = rec.state
        else:
            self.warranty_end_date = 0
            self.warranty_status = 0

    @api.model
    def create(self, vals):
        if vals.get('complain_sequence', _('New')) == _('New'):
            vals['complain_sequence'] = self.env['ir.sequence'].next_by_code('complain.sequence') or _('New')
        result = super(Helpdesk, self).create(vals)
        return result

    warranty_sequence = fields.Many2one('warranty.line', string='Warranty Reference')
    warranty_end_date = fields.Date(string='Warranty End Date', related='warranty_sequence.date_done')
    warranty_status = fields.Selection([
        ('Running', 'Running'),
        ('Expired', 'Expired')],
        string=' Warranty Status', related='warranty_sequence.state')
    warranty_count = fields.Integer(string='Warranty', compute='get_warranty_count')
    product_id = fields.Many2one('product.product', string='Product', help="Product concerned by the ticket")
    commercial_partner_id = fields.Many2one(related='partner_id.commercial_partner_id')
    agents_product = fields.Many2one('product.brand', related='product_id.product_brand_id')
    brand_agent = fields.Many2one('res.partner', string='Brand Agent', related='product_id.product_brand_id.partner_id')
    sale_order_id = fields.Many2one('sale.order', string='Sales Order',
                                    domain="[('partner_id', 'child_of', commercial_partner_id), ('company_id', '=', company_id)]",
                                    groups="sales_team.group_sale_salesman,account.group_account_invoice",
                                    help="Reference of the Sales Order to which this ticket refers. Setting this information aims at easing your After Sales process and only serves indicative purposes.")
    complain_date = fields.Date('Complain Date', default=fields.Date.today())
    complain_sequence = fields.Char(string='Complain Reference', required=True, copy=False, readonly=True, index=True,
                                    default=lambda self: _('New'))


class ReturnStock(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.onchange('sale_order_id', 'partner_id')
    def _onchange_picking_id_filter(self):
        res = {}
        ids = []
        if self.sale_order_id:
            for rec in self.sale_order_id.picking_ids:
                for picking in rec.move_line_ids_without_package:
                    if picking.product_id.id == self.ticket_id.product_id.id:
                        ids.append(rec.id)
        res["domain"] = {'picking_id': [("id", "=", ids)]}
        return res
