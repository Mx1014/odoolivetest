# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import operator as py_operator
from ast import literal_eval
from collections import defaultdict

from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import pycompat,float_is_zero
from odoo.tools.float_utils import float_round

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne
}

class Product(models.Model):
    _inherit = "product.product"

    def _get_rules_from_location(self, location, route_ids=False, seen_rules=False):
        if not seen_rules:
            seen_rules = self.env['stock.rule']
        rule = self.env['procurement.group']._get_rule(self, location, {
            'route_ids': route_ids,
            'warehouse_id': location.get_warehouse()
        })
        if not rule:
            return seen_rules
        if rule.procure_method == 'make_to_stock' or rule.action not in ('pull_push', 'pull'):
            return seen_rules | rule
        else:
            return self._get_rules_from_location(rule.location_src_id, seen_rules=seen_rules | rule)

    def _get_quantity_in_progress(self, location_ids=False, warehouse_ids=False):
        return defaultdict(float), defaultdict(float)

    # def _get_quantity_in_progress(self, location_ids=False, warehouse_ids=False):
    #     if not location_ids:
    #         location_ids = []
    #     if not warehouse_ids:
    #         warehouse_ids = []
    #
    #     qty_by_product_location, qty_by_product_wh = super()._get_quantity_in_progress(location_ids, warehouse_ids)
    #     domain = []
    #     rfq_domain = [
    #         ('state', 'in', ('draft', 'sent', 'to approve')),
    #         ('product_id', 'in', self.ids)
    #     ]
    #     if location_ids:
    #         domain = expression.AND([rfq_domain, [
    #             '|',
    #             ('order_id.picking_type_id.default_location_dest_id', 'in', location_ids),
    #             '&',
    #             ('move_dest_ids', '=', False),
    #             ('orderpoint_id.location_id', 'in', location_ids)
    #         ]])
    #     if warehouse_ids:
    #         wh_domain = expression.AND([rfq_domain, [
    #             '|',
    #             ('order_id.picking_type_id.warehouse_id', 'in', warehouse_ids),
    #             '&',
    #             ('move_dest_ids', '=', False),
    #             ('orderpoint_id.warehouse_id', 'in', warehouse_ids)
    #         ]])
    #         domain = expression.OR([domain, wh_domain])
    #     groups = self.env['purchase.order.line'].read_group(domain,
    #                                                         ['product_id', 'product_qty', 'order_id', 'product_uom',
    #                                                          'orderpoint_id'],
    #                                                         ['order_id', 'product_id', 'product_uom', 'orderpoint_id'],
    #                                                         lazy=False)
    #     for group in groups:
    #         if group.get('orderpoint_id'):
    #             location = self.env['stock.warehouse.orderpoint'].browse(group['orderpoint_id'][:1]).location_id
    #         else:
    #             order = self.env['purchase.order'].browse(group['order_id'][0])
    #             location = order.picking_type_id.default_location_dest_id
    #         product = self.env['product.product'].browse(group['product_id'][0])
    #         uom = self.env['uom.uom'].browse(group['product_uom'][0])
    #         product_qty = uom._compute_quantity(group['product_qty'], product.uom_id, round=False)
    #         qty_by_product_location[(product.id, location.id)] += product_qty
    #         qty_by_product_wh[(product.id, location.get_warehouse().id)] += product_qty
    #     return qty_by_product_location, qty_by_product_wh

    def action_product_forecast_report(self):
        self.ensure_one()
        action = {'name': "Forecast", 'type': 'ir.actions.report', 'report_name': 'stock_check.report_product_product_replenishment', 'report_type': "qweb-html"}
        return action



    def test_browser_pdf(self):
        datas = {'ids': self.ids}
        return self.env.ref('stock_check.stock_replenishment_report_product_product_action').report_action(self, data=datas)

    @api.model
    def view_header_get(self, view_id, view_type):
        res = super(Product, self).view_header_get(view_id, view_type)
        if not res and self._context.get('active_id') and self._context.get('active_model') == 'stock.location':
            return _(
                'Products: %(location)s',
                location=self.env['stock.location'].browse(self._context['active_id']).name,
            )
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(Product, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                   submenu=submenu)
        if self._context.get('location') and isinstance(self._context['location'], int):
            location = self.env['stock.location'].browse(self._context['location'])
            fields = res.get('fields')
            if fields:
                if location.usage == 'supplier':
                    if fields.get('virtual_available'):
                        res['fields']['virtual_available']['string'] = _('Future Receipts')
                    if fields.get('qty_available'):
                        res['fields']['qty_available']['string'] = _('Received Qty')
                elif location.usage == 'internal':
                    if fields.get('virtual_available'):
                        res['fields']['virtual_available']['string'] = _('Forecasted Quantity')
                elif location.usage == 'customer':
                    if fields.get('virtual_available'):
                        res['fields']['virtual_available']['string'] = _('Future Deliveries')
                    if fields.get('qty_available'):
                        res['fields']['qty_available']['string'] = _('Delivered Qty')
                elif location.usage == 'inventory':
                    if fields.get('virtual_available'):
                        res['fields']['virtual_available']['string'] = _('Future P&L')
                    if fields.get('qty_available'):
                        res['fields']['qty_available']['string'] = _('P&L Qty')
                elif location.usage == 'production':
                    if fields.get('virtual_available'):
                        res['fields']['virtual_available']['string'] = _('Future Productions')
                    if fields.get('qty_available'):
                        res['fields']['qty_available']['string'] = _('Produced Qty')
        return res

    def action_view_orderpoints(self):
        action = self.env["ir.actions.act_window"].for_xml_id("stock_check", "action_orderpoint")
        action['context'] = literal_eval(action.get('context'))
        action['context'].pop('search_default_trigger', False)
        action['context'].update({
            'search_default_filter_not_snoozed': True,
        })
        if self and len(self) == 1:
            action['context'].update({
                'default_product_id': self.ids[0],
                'search_default_product_id': self.ids[0]
            })
        else:
            action['domain'] = expression.AND([action.get('domain', []), [('product_id', 'in', self.ids)]])
        return action

class ProductTemplate(models.Model):
    _inherit = 'product.template'



    def action_view_orderpoints(self):
        return self.product_variant_ids.action_view_orderpoints()


    def action_open_routes_diagram(self):
        products = False
        if self.env.context.get('default_product_id'):
            products = self.env['product.product'].browse(self.env.context['default_product_id'])
        if not products and self.env.context.get('default_product_tmpl_id'):
            products = self.env['product.template'].browse(self.env.context['default_product_tmpl_id']).product_variant_ids
        if not self.user_has_groups('stock.group_stock_multi_warehouses') and len(products) == 1:
            company = products.company_id or self.env.company
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
            return self.env.ref('stock.action_report_stock_rule').report_action(None, data={
                'product_id': products.id,
                'warehouse_ids': warehouse.ids,
            }, config=False)
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_stock_rules_report")
        action['context'] = self.env.context
        return action

    def action_product_tmpl_forecast_report(self):
        self.ensure_one()
        #action = self.env["ir.actions.actions"]._for_xml_id('stock.stock_replenishment_product_product_action')
        # form = self.env.ref('stock_check.stock_replenishment_product_product_action', False)
        # action = {
        #     'type': 'ir.actions.client',
        #     'view_id': form.id,
        #     'name': 'Forecasted Report',
        #     'tag': 'replenish_report',
        # }
        action = {'name': "Forecast", 'type': 'ir.actions.report', 'report_name': 'stock_check.report_product_template_replenishment',
                  'report_type': "qweb-html"}
        #return action
        return action

