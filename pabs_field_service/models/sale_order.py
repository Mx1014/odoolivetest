# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.http import request
from odoo.exceptions import UserError, Warning
import re, uuid
import socket
from binascii import hexlify
# import getmac
from subprocess import Popen, PIPE


class SaleOrder(models.Model):
    _inherit = "sale.order"

    x_no_charge = fields.Boolean('Non Chargeable Visit', default=False)
    x_service_type = fields.Selection([('cash', 'Cash Service'), ('credit', 'Credit Service')], string="Service Type", default="cash", tracking=1, copy=False)



    def service_type_action(self):
        for sale in self:
            sale.x_service_type = 'credit'


    # x_invoice_method = fields.Selection([
    #     ("none", "No Invoice"),
    #     ("warranty", "Under Warranty"),
    #     ("after_sale", "After Sale")], string="Invoice Method",
    #     default='none', index=True)

    # def _prepare_invoice(self):
    #     res = super(SaleOrder, self)._prepare_invoice()
    #     if self.x_no_charge:
    #         res['partner_id'] = self.company_id.id
    #     return res

    # def action_approval(self):
    #     if self.partner_id == self.env.ref('base.public_partner'):
    #         raise UserError(
    #             _("Please change the Customer, because if the customer is Public User, Sell Order can't be confirmed."))
    #     user_statement_id = self.env['account.user.statement'].search(
    #         [('user_id', '=', self.env.user.id), ('state', '=', 'open')]).id
    #     if not user_statement_id:
    #         raise UserError(
    #             _("Please start a Session via Sale Terminal as you can't start selling without a session opened."))
    #     self.user_statement_id = user_statement_id
    #
    #     for order in self:
    #         check = 0
    #         for line in order.order_line:
    #             if line.price_unit != 0.0:
    #                 if line.price_subtotal < line.mini_validate:
    #                     check += 1
    #
    #         if check > 0:
    #             order.approval_state = True
    #             order.state = 'approve'
    #         else:
    #             order.approval_state = False
    #             order.action_confirm()
    #             dn = self.env['stock.picking'].search([('id', 'in', order.picking_ids.ids)])
    #             task = self.env['project.task'].search([('id', 'in', order.tasks_ids.ids)])
    #             list = []
    #             for delivery in dn:
    #                 if delivery.picking_type_id.business_line:
    #                     list.append(delivery.id)
    #             if not list and not task:
    #                 return self.action_view_invoice()
    #             else:
    #                 logistic = self.env['ir.module.module'].search([('name', '=', 'pabs_logistics_extra')])
    #                 print(logistic)
    #                 if not logistic or logistic.state == 'installed':
    #                     dn = self.env['stock.picking'].search([('id', 'in', order.picking_ids.ids)])
    #                     tasks = self.env['project.task'].search([('id', 'in', order.tasks_ids.ids)])
    #                     list = []
    #                     for delivery in dn:
    #                         if delivery.picking_type_id.business_line:
    #                             list.append(delivery.id)
    #                     if list or tasks:
    #                        # return self.action_view_logistic_gantt()
    #                        return self.action_delivery_reminder_form_view()
