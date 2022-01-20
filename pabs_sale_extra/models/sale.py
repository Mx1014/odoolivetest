# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.http import request
from odoo.exceptions import UserError, Warning
import re, uuid
import socket
from binascii import hexlify
from subprocess import Popen, PIPE
from lxml import etree
from lxml.builder import E
import json
from datetime import datetime, timedelta
from collections import defaultdict


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # @api.model
    # def _default_warehouses_id(self):
    #     warehouse_ids = self.env['crm.team'].search([('member_ids', 'in', self.env.user.id)])
    #     print(warehouse_ids)
    #     return warehouse_ids

    """
    team_id = fields.Many2one(
        'crm.team', 'Sales Team',
        change_default=True, check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", readonly=True)
                                                                                             """

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('approve', 'Waiting For Approval'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    # user_id = fields.Many2one(
    #     'res.users', string='Salesperson', index=True, copy=False, tracking=2, default=lambda self: self.env.user,
    #     domain=lambda self: [('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').id)])

    def print_quotation(self):
        lines = self.mapped('order_line')
        if not lines:
            raise UserError(_('Nothing to print.'))
        return self.env.ref(
            'pabs_sale_quotation.sale_quotation').report_action(self)

    def print_order(self):
        lines = self.mapped('order_line')
        if not lines:
            raise UserError(_('Nothing to print.'))
        return self.env.ref(
            'pabs_sale_quotation.sale_quotation').report_action(self)

    @api.model
    def _get_sale_order_type_selection(self):
        groups = self.env.user.groups_id.ids
        vals = []
        if self.env.ref('pabs_sale_extra.group_cash_memo_sale').id in groups:
            vals.append(('cash_memo', 'Cash Memo'))
        if self.env.ref('pabs_sale_extra.group_credit_sale').id in groups:
            vals.append(('credit_sale', 'Credit Sale'))
        if self.env.ref('pabs_sale_extra.group_cash_pod').id in groups:
            vals.append(('paid_on_delivery', 'Paid on Delivery'))
        if self.env.ref('pabs_sale_extra.group_advanced_payment').id in groups:
            vals.append(('advance_payment', 'Cash Invoice'))
        if self.env.ref('pabs_sale_extra.group_service').id in groups:
            vals.append(('service', 'Service'))
        return vals
        # else:
        #     print('sh')
        #     return [('cash_memo', 'Cash Memo'), ('credit_sale', 'Credit Sale'),
        #             ('paid_on_delivery', 'Paid on Delivery'), ('advance_payment', 'Advance Payment'),
        #             ('service', 'Service')]

    sale_order_type = fields.Selection(string='Sale Order Type', readonly=True,
                                       selection=_get_sale_order_type_selection,
                                       help='Select a Sale Order Type')

    approval_state = fields.Boolean(string="Approval State", default=False, copy=False)
    msp_confirm = fields.Boolean(string="confirm msp", default=False)
    cashier_user = fields.Many2one('res.users', related="user_statement_id.user_id")
    phone = fields.Char(string="Mobile No.")
    barcode_count = fields.Integer(compute="_compute_barcode_picking_count")

    x_is_head_office = fields.Boolean(related="team_id.x_is_head_office", store=True)

    # team_id = fields.Many2one(
    #     'crm.team', 'Sales Team',
    #     change_default=True, check_company=True, copy=False,
    #     domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    #
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        check_company=True, copy=False)

    # @api.returns('self', lambda value: value.id)
    # def copy(self, default=None):
    #     order = super(SaleOrder, self).copy(default)
    #     order.login_ip_get()
    #     return order

    # @api.onchange('partner_id', 'user_id', 'team_id')
    # def login_ip_get(self):
    #     for teams in self:
    #         teams.update({'user_statement_id': self.env['account.user.statement'].search(
    #             [('user_id', '=', self.env.user.id), ('state', '=', 'open')]).id})
    #         if teams.team_id.team_ipaddress != request.httprequest.environ['REMOTE_ADDR']:
    #             ip = request.httprequest.environ['REMOTE_ADDR']
    #             if ip != '127.0.0.1':
    #                 ip_range = ".".join(ip.split('.')[0:-1])
    #                 # print(getmac.get_mac_address)
    #                 pid = Popen(["arp", "-n", ip], stdout=PIPE)
    #                 s = pid.communicate()[0]
    #                 mac_address = re.search(b"(([a-f\d]{1,2}\:){5}[a-f\d]{1,2})", s).groups()[0]
    #                 # res = self.env['crm.team'].search([('team_ipaddress','=', ip_range)])
    #                 # teams.update({
    #                 #               'team_id': res.id,
    #                 #               'warehouse_id': res.team_warehouse.id,
    #                 #               'analytic_account_id': res.analytic_account_id.id
    #                 #              })
    #                 res = self.env['crm.team'].search([('team_mac_address', '=', mac_address.decode("utf-8"))])
    #                 teams.update({
    #                     'team_id': res.id,
    #                     'warehouse_id': res.team_warehouse.id,
    #                     'analytic_account_id': res.analytic_account_id.id
    #                 })
    #                 if not res:
    #                     exception = self.env['crm.team'].search(
    #                         [('x_is_head_office', '!=', False), ('member_ids', 'in', self.env.user.id)])
    #                     if exception:
    #                         teams.update({
    #                             'team_id': exception.id,
    #                             'warehouse_id': exception.team_warehouse.id,
    #                             'analytic_account_id': exception.analytic_account_id.id
    #                         })

    @api.onchange('partner_id', 'user_id', 'team_id', 'company_id', 'sale_order_type')
    def login_ip_get(self):
        for teams in self:
            mac = ''
            ipaddress = 0
            teams.update({'user_statement_id': self.env['account.user.statement'].search(
                [('user_id', '=', self.env.user.id), ('state', '=', 'open'), ('date', '=', fields.Date.today())]).id})
            # if 'HTTP_X_FORWARDED_FOR' in request.httprequest.environ:
            #     ipaddress = request.httprequest.environ['HTTP_X_FORWARDED_FOR']
            # else:
            #     ipaddress = request.httprequest.environ['REMOTE_ADDR']
            # if ipaddress:
            #     pid = Popen(["arp", "-n", ipaddress], stdout=PIPE)
            #     s = pid.communicate()[0]
            #     mac_address = re.search(b"(([a-f\d]{1,2}\:){5}[a-f\d]{1,2})", s).groups()[0]
            #     mac = mac_address.decode("utf-8")
            # res = self.env['crm.team'].search([('team_mac_address', '=', mac)])
            # exception = self.env['crm.team'].search(
            #    [('x_is_head_office', '!=', False), ('member_ids', 'in', self.env.user.id)])
            res = self.env['crm.team'].search([('member_ids', 'in', self.env.user.id)])
            teams.update({
                'team_id': res.id,
                'warehouse_id': res.team_warehouse.id,
                'analytic_account_id': res.analytic_account_id.id
            })
            # if not res or exception:
            #     if exception:
            #         teams.update({
            #             'team_id': exception.id,
            #             'warehouse_id': exception.team_warehouse.id,
            #             'analytic_account_id': exception.analytic_account_id.id
            #         })

    @api.onchange('user_id')
    def onchange_user_id(self):
        res = super(SaleOrder, self).onchange_user_id()
        self.login_ip_get()
        return res

    def action_approval(self):
        if self.partner_id == self.env.ref('base.public_partner'):
            raise UserError(
                _("Please change the Customer, because if the customer is Public User, Sell Order can't be confirmed."))
        if not self.sale_order_type:
            raise UserError(_('Please Select Sale Order Type'))

        user_statement_id = self.env['account.user.statement'].search(
            [('user_id', '=', self.env.user.id), ('state', '=', 'open')]).id
        # if not user_statement_id:
        #     raise UserError(
        #         _("Please start a Session via Sale Terminal as you can't start selling without a session opened."))
        self.user_statement_id = user_statement_id

        for order in self:
            check = 0
            for line in order.order_line:
                if line.price_unit != 0.0 and line.product_mini != 0.0:
                    if line.price_subtotal < line.mini_validate:
                        check += 1

            if check > 0:
                order.approval_state = True
                order.state = 'approve'
                self.env['mail.activity'].create({
                    'res_id': order.id,
                    'res_model_id': self.env['ir.model']._get('sale.order').id,
                    'activity_type_id': order.activity_type_id.id,
                    'summary': order.activity_type_id.summary,
                    'user_id': order.team_id.user_id.id,
                })
            else:
                order.approval_state = False
                order.action_confirm()
                task = False
                logistic = self.env['ir.module.module'].search([('name', '=', 'pabs_logistics_extra')])
                service = self.env['ir.module.module'].search([('name', '=', 'pabs_field_service')])
                if logistic and logistic.state == 'installed':
                    dn = self.env['stock.picking'].search([('id', 'in', order.picking_ids.ids)])
                    if service and service.state == 'installed':
                        task = self.env['project.task'].search([('id', 'in', order.tasks_ids.ids)])
                    list = []
                    for delivery in dn:
                        if delivery.picking_type_id.business_line:
                            list.append(delivery.id)
                    # if not list:
                    #     return self.action_view_invoice()
                    if list or task:
                        # dn = self.env['stock.picking'].search([('id', 'in', order.picking_ids.ids)])
                        # tasks = self.env['project.task'].search([('id', 'in', order.tasks_ids.ids)])
                        # list = []
                        # for delivery in dn:
                        #     if delivery.picking_type_id.business_line:
                        #         list.append(delivery.id)
                        # if list or tasks:
                        # return self.action_view_logistic_gantt()
                        return self.action_delivery_reminder_form_view()

    def action_delivery_reminder_form_view(self):
        self.ensure_one()
        active_id = self._context.get('active_id')
        active_model = self._context.get('active_model')
        print(active_model, active_id, 'active stuff')
        sale_id = 0
        if active_model == 'sale.order':
            sale_id = active_id
        elif active_model == 'plan.calendar':
            sale_id = self.env['plan.calendar'].search([('id', '=', active_id)]).sale_id.id
        else:
            sale_id = self.id
        # business_line = self.delivery.picking_type_id.business_line
        # vals = {'delivery': self.delivery.id, 'status': self.status, 'period': self.period,
        #         'delivery_items': self.delivery_items}
        # self.write(vals)
        # print('inventory any write')
        return {
            'name': _('Logistic'),
            'res_model': 'delivery.reminder',
            'view_mode': 'form',
            'views': [
                (self.env.ref('pabs_logistics_extra.delivery_reminder_form_view').id, 'form'),
            ],
            'target': 'inline',
            'context': {"active_model": 'sale.order', "active_id": sale_id, 'sale_id': sale_id},
            # 'domain': [('id', 'in', show)],
            'type': 'ir.actions.act_window',
        }

    def approval_get(self):
        self.write({'state': 'approved'})
        # self.action_confirm()
        # dn = self.env['stock.picking'].search([('id', 'in', self.picking_ids.ids)])
        # logistic = self.env['ir.module.module'].search([('name', '=', 'pabs_logistics_extra')])
        # if not logistic or logistic.state != 'installed':
        #     return self.action_delivery_reminder_form_view()()

    def continue_the_confirm(self):
        self.action_confirm()
        logistic = self.env['ir.module.module'].search([('name', '=', 'pabs_logistics_extra')])
        if logistic and logistic.state == 'installed':
            return self.action_delivery_reminder_form_view()

    def sale_refused(self):
        self.write({'state': 'refused'})

    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel', 'sent', 'refused'])
        return orders.write({
            'state': 'draft',
            'signature': False,
            'signed_by': False,
            'signed_on': False,
        })

    def all_need_approve(self):
        all = self.env['sale.order'].search([('state', '=', 'approve')])
        all.approval_get()

    @api.onchange('order_line')
    def onchange_msp_confirm(self):
        validate = 0
        for order in self.mapped('order_line'):
            if order.product_mini != 0.0:
                if order.mini_validate > order.price_subtotal:
                    validate += 1
        if validate > 0:
            self.msp_confirm = True
        else:
            self.msp_confirm = False

    def print_so_ticket(self):
        return {'type': 'ir.actions.report', 'report_name': 'pabs_sale_extra.report_so_ticket',
                'report_type': "qweb-pdf"}

    def action_view_barcode(self):
        self.ensure_one()
        return {
            'name': _('Barcode'),
            'res_model': 'stock.picking',
            'view_mode': 'kanban',
            'views': [
                (self.env.ref('stock_barcode.stock_picking_kanban').id, 'kanban'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('sale_id', '=', self.id), ('state', '!=', 'done')],
        }

    def _compute_barcode_picking_count(self):
        for picking in self:
            picking.barcode_count = self.env['stock.picking'].search_count(
                [('sale_id', '=', picking.id), ('state', '!=', 'done')])

    # @api.onchange('pricelist_id', 'order_line')
    # def onchange_msp(self):
    #     for order in self:
    #         for line in order.order_line:
    #             if order.pricelist_id:
    #                 for items in order.pricelist_id.item_ids:
    #                     if items.compute_price == 'formula':
    #                         if items.applied_on == '3_global':
    #                             line['product_mini'] = items.price_min_margin
    #                         elif items.applied_on == '1_product':
    #                             if line.product_id.id == items.product_tmpl_id.id:
    #                                 line['product_mini'] = items.price_min_margin
    #                             else:
    #                                 line['product_mini'] = 0.0
    #                         elif items.applied_on == '2_product_category':
    #                             if line.product_id.categ_id.id == items.categ_id.id:
    #                                 line['product_mini'] = items.price_min_margin
    #                             else:
    #                                 line['product_mini'] = 0.0
    #                         else:
    #                             line['product_mini'] = 0.0
    #                 # line['product_mini'] = order.pricelist_id.item_ids[len(order.pricelist_id.item_ids) - 1].price_min_margin
    #             else:
    #                 line['product_mini'] = 0.0

    @api.model
    def create(self, vals):
        result = super(SaleOrder, self).create(vals)
        if result.partner_shipping_id:
            if not result.partner_shipping_id.country_id or not result.partner_shipping_id.street_number or not result.partner_shipping_id.x_address_block or not result.partner_shipping_id.x_address_road:
                if not result.partner_shipping_id.name.lower() == "cash customer":
                    raise UserError(_('Please Edit Customer Address'))
        return result


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_mini = fields.Float(string='MSP')
    mini_validate = fields.Float()

    # @api.onchange('product_id')
    # def call_onchange_msp(self):
    #     for product in self.order_id:
    #         product.onchange_msp()

    @api.onchange('product_id')
    def _onchange_msp(self):
        for product in self:
            product.product_mini = product.product_id.price_minimum

    @api.onchange('price_unit', 'price_subtotal')
    def total_mini(self):
        for line in self:
            if line.price_unit != 0.0:
                total_product_mini = line.product_uom_qty * line.product_mini
                line.mini_validate = total_product_mini

    # @api.onchange('product_id')
    # def _onchange_product_product_id(self):
    #     res = {}
    #     if self.order_id.sale_order_type == 'cash_memo':
    #         res['domain'] = {'product_id': [('x_exist_in_pos', '!=', False)]}
    #         return res

    @api.onchange('product_id', 'route_id')
    def onchange_route_id_warehouse(self):
        if self.route_id:
            print(self.route_id.id, 'route')
            self._compute_is_mto()

    @api.depends('product_id', 'route_id', 'order_id.warehouse_id', 'product_id.route_ids')
    def _compute_is_mto(self):
        """ Verify the route of the product based on the warehouse
            set 'is_available' at True if the product availibility in stock does
            not need to be verified, which is the case in MTO, Cross-Dock or Drop-Shipping
        """
        self.is_mto = False
        for line in self:
            if not line.display_qty_widget:
                continue
            product = line.product_id
            product_routes = line.route_id or (product.route_ids + product.categ_id.total_route_ids)

            # Check MTO
            mto_route = line.order_id.warehouse_id.mto_pull_id.route_id

            if line.route_id:
                mto_route = line.route_id
            else:
                mto_route = line.order_id.warehouse_id.mto_pull_id.route_id

            print(line.warehouse_id.name)
            print(line.order_id.warehouse_id.mto_pull_id.route_id)
            print(mto_route.name)
            if not mto_route:
                try:
                    mto_route = self.env['stock.warehouse']._find_global_route('stock.route_warehouse0_mto',
                                                                               _('Make To Order'))
                except UserError:
                    # if route MTO not found in ir_model_data, we treat the product as in MTS
                    pass

            if mto_route and mto_route in product_routes:
                line.is_mto = True
            else:
                line.is_mto = False


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    team_ipaddress = fields.Char(string='IP Address')
    team_warehouse = fields.Many2one('stock.warehouse', string='Warehouse')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    team_mac_address = fields.Many2many('crm.team.macadress', 'team_id', string='Mac Addresses')
    x_is_head_office = fields.Boolean(string="Is Head Office", store=True)
    x_short_name = fields.Char(string="Short Code")
    x_user_statement_count = fields.Integer(string="Sessions", compute="_compute_user_statement_count")

    @api.constrains('team_mac_address')
    def _check_something(self):
        for record in self:
            for address in record.team_mac_address:
                mac = self.env['crm.team'].search([('team_mac_address', '=', address.name)])
                if len(mac) > 1:
                    raise Warning('The MAC Address should be unique in Sales team!')


    def action_view_team_session(self):
        self.ensure_one()
        return {
            'name': _('Sessions'),
            'res_model': 'account.user.statement',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('pabs_sale.account_user_statement_tree').id, 'tree'),
                (self.env.ref('pabs_sale.account_user_statement_view_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('user_id.sale_team_id', '=', self.id)],
        }

    def _compute_user_statement_count(self):
        for statement in self:
            statement.x_user_statement_count = self.env['account.user.statement'].search_count(
                [('user_id.sale_team_id', '=', self.id)])


class CrmMacTeam(models.Model):
    _name = 'crm.team.macadress'
    _description = 'Mac Addresses'

    def _get_name_mac(self):
        if 'HTTP_X_FORWARDED_FOR' in request.httprequest.environ:
            ipaddress = request.httprequest.environ['HTTP_X_FORWARDED_FOR']
        else:
            ipaddress = request.httprequest.environ['REMOTE_ADDR']

        if ipaddress:
            pid = Popen(["arp", "-n", ipaddress], stdout=PIPE)
            s = pid.communicate()[0]
            mac_address = re.search(b"(([a-f\d]{1,2}\:){5}[a-f\d]{1,2})", s).groups()[0]
            return mac_address.decode("utf-8")
        else:
            raise Warning(_('You Have No Internet Connection..'))

    name = fields.Char(string="Mac Address", default=_get_name_mac)
    name_device = fields.Char(string='Device Name')
    team_id = fields.Many2one('crm.team', string='Branch')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The MAC Address should be unique!')
    ]

    def mac_address_get(self):
        for address in self:
            if 'HTTP_X_FORWARDED_FOR' in request.httprequest.environ:
                ipaddress = request.httprequest.environ['HTTP_X_FORWARDED_FOR']
            else:
                ipaddress = request.httprequest.environ['REMOTE_ADDR']

            if ipaddress:
                pid = Popen(["arp", "-n", ipaddress], stdout=PIPE)
                s = pid.communicate()[0]
                mac_address = re.search(b"(([a-f\d]{1,2}\:){5}[a-f\d]{1,2})", s).groups()[0]
                if self.env['crm.team.macadress'].search([('name', '=', mac_address.decode("utf-8"))]):
                    address.mac_bool = True
                else:
                    address.name = mac_address.decode("utf-8")
            else:
                raise Warning(_('You Have No Internet Connection..'))

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(CrmMacTeam, self).fields_view_get(view_id=view_id, view_type=view_type,
    #                                                                        toolbar=toolbar, submenu=submenu)
    #
    #     if view_type == 'form':
    #             doc = etree.XML(res['arch'])
    #             # The field you want to modify the attribute
    #             print(res['arch'])
    #             node = doc.xpath("//sheet//h1//field[@name='name']")[0]
    #             print(node)
    #             node.set('required', "0")
    #             modifiers = json.loads(node.get("modifiers"))
    #             modifiers['required'] = False
    #             node.set("modifiers", json.dumps(modifiers))
    #             print(modifiers)
    #             res['arch'] = etree.tostring(doc)
    #             return res
    #     return res

    # @api.model
    # def create(self, vals):
    #     if 'HTTP_X_FORWARDED_FOR' in request.httprequest.environ:
    #         ipaddress = request.httprequest.environ['HTTP_X_FORWARDED_FOR']
    #     else:
    #         ipaddress = request.httprequest.environ['REMOTE_ADDR']
    #
    #     if ipaddress:
    #         pid = Popen(["arp", "-n", ipaddress], stdout=PIPE)
    #         s = pid.communicate()[0]
    #         mac_address = re.search(b"(([a-f\d]{1,2}\:){5}[a-f\d]{1,2})", s).groups()[0]
    #         if self.env['crm.team.macadress'].search([('name', '=', mac_address.decode("utf-8"))]):
    #             self.mac_bool = True
    #         else:
    #             self.name = mac_address.decode("utf-8")
    #     return super(CrmMacTeam, self).create(vals)


class SaleTerminal(models.Model):
    _inherit = 'sale.terminal'

    allowed_team = fields.Many2one('crm.team', string='Responsible Team')
    allowed_journal = fields.Many2many('account.journal', string="Payment Method")
    allowed_payment_method = fields.Many2many('statement.payment.methods', string="Payment Methods",
                                              inverse="_compute_get_payment_method")
    short_name = fields.Char(string="Short Code")
    sequence_number_next = fields.Integer(string='Next Number', compute='_compute_seq_number_next',
                                          inverse='_inverse_seq_number_next')
    sequence_id = fields.Many2one('ir.sequence', string='Sequence', required=True, copy=False)
    tid_ids = fields.Many2many('bank.card.readers', string="TID")
    min_threshold = fields.Monetary(string="Minimum Threshold", store=True)
    tid_lines = fields.One2many('bank.card.reader.line', 'terminal_id', string="TIDS")
    allowed_user = fields.Many2one('res.users', string="Responsible Cashier")
    member_ids = fields.One2many(related="allowed_team.member_ids")
    will_session_start_username = fields.Char()
    payment_method_domain = fields.Many2many('statement.payment.methods', relation="payment_domain",
                                             compute="exist_payment_method")

    def exist_payment_method(self):
        self.payment_method_domain = None
        for line in self.tid_lines:
            if line.payment_methods:
                self.payment_method_domain = [(4, line.payment_methods.id)]

    @api.model
    def create(self, vals):
        team = self.env['crm.team'].browse(int(vals['allowed_team']))
        if team and 'name' in vals:
            vals['sequence_id'] = self.env['ir.sequence'].sudo().create({
                'name': '%s - %s' % (team.x_short_name ,vals['name']),
                #'code': '%s.%s' % (vals['short_name'], team.name),
                'implementation': 'standard',
                'padding': 4,
                'number_increment': 1,
                'company_id': self.company_id.id,
                'use_date_range': True,
                'prefix': '%(range_y)s/',
            }).id
        return super(SaleTerminal, self).create(vals)

    @api.onchange('tid_lines')
    def terminal_payment_method(self):
        self.exist_payment_method()
        for line in self:
            for tid in line.tid_lines:
                if tid.payment_methods.id not in line.allowed_payment_method.ids:
                    if tid.payment_methods.id != False:
                        line.write({'allowed_payment_method': [(4, tid.payment_methods.id)]})

    @api.depends('sequence_id.use_date_range', 'sequence_id.number_next_actual')
    def _compute_seq_number_next(self):
        '''Compute 'sequence_number_next' according to the current sequence in use,
        an ir.sequence or an ir.sequence.date_range.
        '''
        for terminal in self:
            if terminal.sequence_id:
                sequence = terminal.sequence_id._get_current_sequence()
                terminal.sequence_number_next = sequence.number_next_actual
            else:
                terminal.sequence_number_next = 1

    def _inverse_seq_number_next(self):
        '''Inverse 'sequence_number_next' to edit the current sequence next number.
        '''
        for terminal in self:
            if terminal.sequence_id and terminal.sequence_number_next:
                sequence = terminal.sequence_id._get_current_sequence()
                sequence.sudo().number_next = terminal.sequence_number_next

    def name_get(self):
        res = []
        for method in self:
            res.append((method.id, "%s (%s)" % (method.name, method.allowed_team.name)))
        return res

    # @api.depends('tid_ids')
    # def _compute_get_tid(self):
    #     tids = []
    #     for conf in self:
    #        for tid in self.env['bank.card.reader'].search([('terminal_id', '=', self.id)]):
    #            tids.append((0, 0, {
    #                'payment_methods': tid.payment_methods.id,
    #                'tid_ids': [(6, 0, tid.ids)],
    #            }))
    #        print(tids)
    #        conf.tid_lines = tids
    #
    # def _inverse_get_tid(self):
    #     for conf in self:
    #         for tid in self.tid_lines:
    #            tid.tid_ids.terminal_id = conf.id

    def _compute_get_payment_method(self):
        vals = []
        duplicate = []
        methods = []
        for line in self:
            for data in line.tid_lines:
                duplicate.append(data.payment_methods.id)
            for payment in line.allowed_payment_method:
                if payment.journal_account_id.x_bank_type == 'card' and payment.id not in duplicate:
                    vals.append((0, 0, {
                        'payment_methods': payment.id,
                    }))
            line.tid_lines = vals

            for method in line.allowed_payment_method:
                if method.journal_account_id.x_bank_type == 'card':
                    methods.append(method.id)
            for tid in line.tid_lines:
                if tid.payment_methods.id not in methods:
                    tid.unlink()

    # @api.constrains('tid_lines')
    # def _check_tid_lines(self):
    #     list = []
    #     for payment in self.tid_lines:
    #         list.append(payment.payment_methods.id)
    #     if len(list) != len(set(list)):
    #         raise UserError(_("You have duplicate records"))
