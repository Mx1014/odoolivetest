import base64
import math
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class Helpdesk(models.Model):
    _inherit = 'helpdesk.ticket'

    is_collect = fields.Boolean(string='No S.O.', default=False)
    close_days = fields.Integer("Time to close (Days)", compute='_compute_close_days', store=True)

    @api.depends('close_hours')
    def _compute_close_days(self):
        for rec in self:
            # print("3")
            # if rec.close_hours:
            round_up = rec.close_hours / 8
            rec.close_days = math.ceil(round_up)

    @api.constrains('partner_id')
    def check_for_customer_address(self):
        for ticket in self:
            if not ticket.partner_id.country_id or not ticket.partner_id.street_number or not ticket.partner_id.x_address_block or not ticket.partner_id.x_address_road:
                raise Warning(_('Please Edit Customer Address'))


    # @api.onchange('sale_order_id')
    # def set_product_id(self):
    #     res = {}
    #     ids = []
    #     if self.sale_order_id:
    #         for rec in self.sale_order_id.mapped("order_line"):
    #             ids.append(rec.product_id.id)
    #
    #         res["domain"] = {'product_id': [("id", "in", ids), ('type', '=', 'product')]}
    #
    #         return res
    #     else:
    #         return self.set_customer()
    #
    # @api.onchange('partner_id')
    # def set_customer(self):
    #     res = {}
    #     ids = self.env['sale.order'].search(
    #         [('partner_id', '=', self.partner_id.id)])
    #     prod_ids = []
    #     for rec in ids:
    #         for line in rec.order_line:
    #             prod_ids += line.product_id.ids
    #     res["domain"] = {'product_id': [("id", "in", prod_ids), ('type', '=', 'product')]}
    #
    #     return res
    def attach_sale_order(self):
        if self.sale_order_id:
            pdf = self.env.ref('pabs_sale_quotation.sale_quotation_email').render_qweb_pdf(self.sale_order_id.ids)
            b64_pdf = base64.b64encode(pdf[0])
            return self.env['ir.attachment'].create({
                'name': self.sale_order_id.name + '.pdf',
                'type': 'binary',
                'datas': b64_pdf,
                # 'datas_fname': self.sale_order_id.name + '.pdf',
                'store_fname': self.sale_order_id.name,
                'res_model': 'sale.order',
                'res_id': self.sale_order_id.id,
                'mimetype': 'application/pdf',
            })

    def attach_complain(self):
        pdf = self.env.ref('pabs_repair.complaint_form_by_email').render_qweb_pdf(self.id)
        b64_pdf = base64.b64encode(pdf[0])
        return self.env['ir.attachment'].create({
            'name': self.name + '.pdf',
            'type': 'binary',
            'datas': b64_pdf,
            # 'datas_fname': self.sale_order_id.name + '.pdf',
            'store_fname': self.name,
            'res_model': 'helpdesk.ticket',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

    def action_mail_send_To_Agent(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        sale_order_id = 0
        complain_id = 0
        sale_order = self.attach_sale_order()
        if sale_order:
            sale_order_id = sale_order.id
        complain = self.attach_complain()
        if complain:
            complain_id = complain.id
        template_id = self.env.ref('pabs_repair.pabs_helpdesk_email_template').id
        lang = self.env.context.get('lang')
        # template = self.env['mail.template'].browse(template_id)
        # template.send_mail(self.id, force_send=True)
        # if template.lang:
        #     lang = template._render_template(template.lang, 'helpdesk.ticket', self.ids[0])
        # print(id, "idddd")

        if self.sale_order_id:
            ctx = {
                'default_model': 'helpdesk.ticket',
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_partner_ids': self.brand_agent.ids,
                'default_composition_mode': 'comment',
                # 'mark_so_as_sent': True,
                'custom_layout': "mail.mail_notification_paynow",
                # 'proforma': self.env.context.get('proforma', True),
                'proforma': self.env.context.get('proforma', True),
                'force_email': True,
                'default_attachment_ids': [(4, complain_id), (4, sale_order_id)]
                # 'model_description': self.with_context(lang=lang).type_name,
            }
        else:
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
                'proforma': self.env.context.get('proforma', True),
                'force_email': True,
                'default_attachment_ids': [(4, complain_id)]
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

    @api.onchange('x_service_category_bot1', 'x_service_category_bot2')
    def compute_x_service_category(self):
        print('ttt')
        if self.x_product_id:
            self.x_service_category = self.x_service_category_bot1
            print(self.x_service_category)
        elif self.product_id:
            self.x_service_category = self.x_service_category_bot2
            print(self.x_service_category)

    # @api.onchange('product_id')
    # def onchange_warranty_reference(self):
    #     res = {}
    #     ids = self.env['warranty.line'].search(
    #         ['&', ('customer_name', '=', self.partner_id.id), ('order_id', '=', self.sale_order_id.id),
    #          ('product_id', '=', self.product_id.id)])
    #     prod_ids = []
    #     for rec in ids:
    #         prod_ids.append(rec.id)
    #     res["domain"] = {'warranty_sequence': [("id", "in", prod_ids)]}
    #     return res

    # @api.onchange('warranty_sequence')
    # def onchange_warranty_end_date(self):
    #     x = self.env['warranty.line'].search(
    #         ['&', ('order_id', '=', self.sale_order_id.id), ('product_id', '=', self.product_id.id),
    #          ('id', '=', self.warranty_sequence.id)])
    #     if x:
    #         for rec in x:
    #             self.warranty_end_date = rec.date_done
    #             self.warranty_status = rec.state
    #     else:
    #         self.warranty_end_date = 0
    #         self.warranty_status = 0

    # def _x_product_id_domain(self):
    #     ids = []
    #     sale_id = self.env['helpdesk.ticket'].browse(self.id).sale_order_id
    #     print(sale_id)
    #     if sale_id:
    #         for rec in sale_id.mapped("order_line"):
    #             ids.append(rec.product_id.id)
    #
    #         return [("id", "in", ids), ('type', '=', 'product')]
    #     else:
    #         return [('type', '=', 'product')]
    # @api.depends('sale_order_id')

    name = fields.Char('Type', translate=True, compute='_compute_name', store=True, default='/')

    product_id = fields.Many2one('product.product', string='Product', help="Product concerned by the ticket")
    x_product_id = fields.Many2one('product.product', string='Product', help="Product concerned by the ticket")
    x_service_category = fields.Many2one('service.category', store=True)
    x_service_category_bot1 = fields.Many2one('service.category', related="x_product_id.x_service_category")
    x_service_category_bot2 = fields.Many2one('service.category', related="product_id.x_service_category")
    warranty_sequence = fields.Many2one('warranty.line', string='Warranty Reference',
                                        domain="[('customer_name', '=', partner_id), ('product_id', '=', product_id)]")
    warranty_end_date = fields.Date(string='Warranty End Date', related='warranty_sequence.date_done')
    extended_warranty_end_date = fields.Date(string='Extended End Date', related='warranty_sequence.extended_end_date')
    warranty_status = fields.Selection([
        ('Running', 'Running'),
        ('Expired', 'Expired')],
        string=' Warranty Status', related='warranty_sequence.state')
    warranty_count = fields.Integer(string='Warranty')
    commercial_partner_id = fields.Many2one(related='partner_id.commercial_partner_id')
    agents_product = fields.Many2one('product.brand', related='product_id.product_brand_id', store=True)
    brand_agent = fields.Many2one('res.partner', string='Brand Agent', related='product_id.product_brand_id.partner_id', store=True)
    sale_order_date = fields.Datetime(string='Sale Order Date', related='sale_order_id.date_order')
    sale_order_id = fields.Many2one('sale.order', string='Sales Order',
                                    groups="",
                                    help="Reference of the Sales Order to which this ticket refers. Setting this information aims at easing your After Sales process and only serves indicative purposes.")
    x_show_send_agent = fields.Boolean('Show Send To Agent', compute='compute_x_show_send_agent')
    x_phone = fields.Char(string='Phone', related='partner_id.phone')
    x_mobile = fields.Char(string='Mobile', related='partner_id.mobile')
    x_mobile_2 = fields.Char(string='Mobile 2', related='partner_id.x_mobile')
    x_serial_no = fields.Char(string='Serial No')
    x_warranty_other_info = fields.Char(string='Warranty Other Info')
    x_issue_type = fields.Many2one('helpdesk.issue.type', string='Issue Type')
    x_product_domain = fields.Many2many('product.product', string='Products Domain',
                                        compute='_compute_x_product_domain')
    x_sale_order_domain = fields.Many2many('sale.order', string='Sale Domain',
                                           compute='_compute_x_sale_order_domain')
    x_move_id = fields.Many2many('account.move', string="Credit Note", relation="helpdesk_ticket_ref", readonly=True, copy=False)
    product_quantity = fields.Float(string='Quantity')
    x_invoice_counts = fields.Integer(string='invoices', compute="count_repair_and_task")
    x_comeback_id = fields.Many2one('helpdesk.ticket', string="Comeback Job")
    x_main_comeback_id = fields.Many2one('helpdesk.ticket', string="Main Job")
    x_comeback_counts = fields.Integer(string='Come-Back Job', compute="count_comeback")
    kanban_label = fields.Char(string="Kanban Label")
    x_ticket_issue = fields.Many2many(related="ticket_type_id.x_ticket_issue")
    x_is_close = fields.Boolean(related="stage_id.is_close")
    x_warranty_availbility = fields.Selection([('under_warr', 'Under Warranty'), ('out_warr', 'Out of Warranty')], string="Warranty Availability")
    x_sale_order_line = fields.One2many(related="sale_order_id.order_line")
    x_order_line = fields.Many2many('sale.order.line', string="Order Line", store=True)
    x_close_stage_id = fields.Many2one('helpdesk.stage', related="stage_id")
    x_product_required = fields.Boolean(related="ticket_type_id.x_product_required")

    @api.onchange('sale_order_id')
    def get_order_line(self):
        for ticket in self:
            if ticket.sale_order_id:
               ticket.x_order_line = ticket.x_sale_order_line.filtered(lambda x: not x.is_downpayment).ids
            else:
              ticket.x_order_line = False

    @api.constrains('product_quantity')
    def restrict_product_quantity(self):
        if not self.product_quantity or self.product_quantity < 0:
            if self.ticket_type_id.id != self.env.ref('pabs_repair.product_cancellation').id:
                 raise Warning(_('Please change the product quantity'))

    def count_repair_and_task(self):
        for ticket in self:
            ticket.x_invoice_counts = len(self.mapped('repair_ids.invoice_id')) + len(self.mapped('fsm_task_ids.sale_order_id.invoice_ids'))

    def count_comeback(self):
        for ticket in self:
            ticket.x_comeback_counts = self.search_count([('id', 'in', self.x_comeback_id.ids)])



    @api.depends('stage_id', 'kanban_state')
    def _compute_kanban_state_label(self):
        for task in self:
            if task.kanban_state == 'normal':
                task.kanban_state_label = task.legend_normal
                task.kanban_label = task.legend_normal
            elif task.kanban_state == 'blocked':
                task.kanban_state_label = task.legend_blocked
                task.kanban_label = task.legend_blocked
            else:
                task.kanban_state_label = task.legend_done
                task.kanban_label = task.legend_done


    @api.depends('sale_order_id', 'partner_id')
    def _compute_x_product_domain(self):
        for record in self:
            ids = []
            if record.partner_id:
                partner_so_ids = self.env['sale.order.line'].search(
                    [('order_partner_id', '=', record.partner_id.id), ('product_template_id.type', '!=', 'service')])
                for so in partner_so_ids:
                    # for line in so.order_line:
                    if so.product_id.id not in ids:
                        ids.append(so.product_id.id)
                # self.x_product_domain = ids
                # self.x_product_domain = [(6, 0, ids)]
            if record.sale_order_id:
                ids = []
                for rec in record.sale_order_id.order_line:
                    ids.append(rec.product_id.id)
                # self.x_product_domain = ids
                # self.x_product_domain = [(6, 0, ids)]
            record.x_product_domain = ids

        # if :
        #     self.x_product_domain = [(5, 0, 0)]

    @api.depends('product_id', 'partner_id')
    def _compute_x_sale_order_domain(self):
        order_cancelation = False
        for record in self:
            ids = []

            if self.env.ref('pabs_repair.product_cancellation').id == record.ticket_type_id.id:
                order_cancelation = True
            partner_so_ids = self.env['sale.order'].search(
                [('partner_id', '=', record.partner_id.id), ('state', '=', 'sale')])
            if record.partner_id:
                ids = partner_so_ids.ids

            if order_cancelation:
                ids = []
                for order in partner_so_ids:
                   if any(line.qty_delivered != 0.0 for line in order.order_line.filtered(lambda x: not x.is_downpayment)):
                       continue
                   else:
                       ids.append(order.id)

            if record.product_id:
                ids = []
                for rec in partner_so_ids:
                    for line in rec.order_line:
                        if record.product_id == line.product_id and line.order_id.id not in ids and not order_cancelation:
                            ids.append(line.order_id.id)

            record.x_sale_order_domain = ids

    @api.onchange('partner_id')
    def _onchange_partner_id_domain_sale_order_id(self):
        print("124")

    @api.onchange('x_product_id')
    def x_onchange_x_product_id(self):
        self.product_id = self.x_product_id

    @api.onchange('product_id')
    def x_onchange_product_id_remove_warranty(self):
        self.warranty_sequence = False

    # @api.onchange('product_id')
    # def set_customer_sale_order(self):
    #     res = {}
    #     ids = self.env['sale.order'].search(
    #         [('partner_id', '=', self.partner_id.id)])
    #     sale_ids = []
    #     if self.product_id:
    #         for rec in ids:
    #             for line in rec.order_line:
    #                 if line.product_id.id == self.product_id.id:
    #                     sale_ids += rec.ids
    #         res["domain"] = {'sale_order_id': [("id", "in", sale_ids)]}
    #         return res

    # @api.onchange('partner_id')
    # def x_onchange_partner_id(self):
    #     self.sale_order_id = False
    #     self.product_id = False
    #     self.x_product_id = False

    @api.onchange('is_collect')
    def x_onchange_is_collect(self):
        self.sale_order_id = False
        self.product_id = False
        self.x_product_id = False

    @api.onchange('sale_order_id', 'warranty_sequence', 'product_id')
    def x_onchange_sale_order_id_warranty_domain(self):
        res = {}

        if self.sale_order_id:
            ids = [self.product_id.id]
            if self.product_id.variant_bom_ids:
                for bom in self.product_id.variant_bom_ids.mapped('bom_line_ids'):
                    ids.append(bom.product_id.id)
            res['domain'] = {
                'warranty_sequence': [('customer_name', '=', self.partner_id.id),
                                      ('product_id', 'in', ids),
                                      ('order_id', '=', self.sale_order_id.id)]}
        else:
            res['domain'] = {
                'warranty_sequence': [('customer_name', '=', self.partner_id.id),
                                      ('product_id', '=', self.product_id.id)]}
        return res

    # @api.onchange('sale_order_id')
    # def set_product_id(self):
    #     res = {}
    #     ids = []
    #     self.product_id = False
    #
    #     if self.sale_order_id:
    #         for rec in self.sale_order_id.mapped("order_line"):
    #             ids.append(rec.product_id.id)
    #         res["domain"] = {'product_id': [("id", "in", ids), ('type', '=', 'product')]}
    #         return res
    #     else:
    #         res["domain"] = {'product_id': [('type', '=', 'product')]}
    #         return res

    def name_get(self):
        result = []
        for rec in self:
            name = 'ticket#' + (str(rec.id) if type(rec.id) is int else 'New')
            if rec.ticket_type_id.name:
                name = rec.ticket_type_id.name + '#' + (str(rec.id) if type(rec.id) is int else 'New')
            result.append((rec.id, name))
        return result

    @api.depends('ticket_type_id.name')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.display_name

    @api.depends('brand_agent')
    def compute_x_show_send_agent(self):
        for rec in self:
            if rec.brand_agent == rec.company_id.partner_id:
                rec.x_show_send_agent = False
            else:
                rec.x_show_send_agent = True

    def action_view_credit_note(self):
        self.ensure_one()
        return {
            'name': _('Credit Note'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_invoice_tree').id, 'tree'),
                (self.env.ref('account.view_move_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.x_move_id.ids)]
        }

    def action_create_credit_note(self):
        for ticket in self:
            if ticket.is_collect:
                vals = {
                    'partner_id': ticket.partner_id.id,
                    'type': 'out_refund',
                    'invoice_line_ids': [(0, 0, {'product_id': ticket.x_product_id.id})]
                }
                ticket.x_move_id = self.env['account.move'].create([vals])
                return self.action_view_credit_note()

    def action_view_repair_and_task_invoice(self):
        repair_invoice = self.mapped('repair_ids.invoice_id')
        task_invoices = self.mapped('fsm_task_ids.sale_order_id.invoice_ids')

        return {
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_invoice_tree').id, 'tree'),
                (self.env.ref('account.view_move_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', repair_invoice.ids + task_invoices.ids)],
        }

    def action_view_comeback_job(self):
        return {
            'name': _('Product Complain'),
            'res_model': 'helpdesk.ticket',
            'view_mode': 'kanban,form',
            'views': [
                (self.env.ref('helpdesk.helpdesk_ticket_view_kanban').id, 'kanban'),
                (self.env.ref('helpdesk.helpdesk_ticket_view_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.x_comeback_id.ids)],
        }

    def action_create_comeback_job(self):
        for ticket in self:
            ticket.x_comeback_id = ticket.copy({'x_main_comeback_id': ticket.id, 'ticket_type_id': self.env.ref('pabs_repair.comeback').id})

        # if any([vals.get('auto_post', False) for vals in default_values_list]):
        #     self.x_move_id = moves._reverse_moves(default_values_list)
        #
        # else:
        #     self.x_move_id = moves._reverse_moves(default_values_list, cancel=True)


    # def action_open_helpdesk_ticket(self):
    #     action = self.env.ref('helpdesk.helpdesk_ticket_action_main_tree').read()[0]
    #     action['context'] = {'default_partner_id': self.partner_id.id}
    #     action['domain'] = [('partner_id', 'child_of', self.partner_id.id)]
    #     return action


class ReturnStock(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.onchange('sale_order_id', 'partner_id')
    def _onchange_picking_id_filter(self):
        res = {}
        ids = []
        if self.sale_order_id:
            pickings = self.sale_order_id.picking_ids
            order_line = self.env['sale.order.line'].search(
                [('order_id', '=', self.sale_order_id.id), ('product_id', '=', self.ticket_id.product_id.id)])
            product_bom = self.env['mrp.bom'].search(
                [('product_id', '=', self.ticket_id.product_id.id)]).bom_line_ids.mapped('product_id').ids
            if product_bom:
                for rec in pickings:
                    if set(product_bom).issubset(rec.move_line_ids_without_package.mapped('product_id').ids):
                        ids.append(rec.id)
            else:
                for rec in pickings:
                    if self.ticket_id.product_id.id in rec.move_line_ids_without_package.mapped('product_id').ids:
                        ids.append(rec.id)

            # for rec in self.sale_order_id.picking_ids:
            #     for picking in rec.move_line_ids_without_package:
            #         if picking.product_id.id == self.ticket_id.product_id.id:
            #             ids.append(rec.id)
        res["domain"] = {'picking_id': [("id", "=", ids)]}
        return res
