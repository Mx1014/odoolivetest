# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime, timedelta
from collections import defaultdict
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError


# class SaleOrderLine(models.Model):
#     _inherit = 'sale.order.line'
#
#     # @api.onchange('tax_id')
#     def planning_calendar(self):
#         # planning_slot = self.copy()
#         # context = dict(self.env.context)
#         # context['form_view_initial_mode'] = 'edit'
#         return {
#             'name': _('plan'),
#             'type': 'ir.actions.act_window',
#             'view_mode': 'gantt',
#             'res_model': 'planning.slot',
#             'views': [
#                 (self.env.ref('planning.planning_view_gantt').id, 'gantt'),
#             ],  # 'res_id': planning_slot.id,
#             # 'context': context,
#         }
# <field name="context">{'search_default_group_by_business_line': 1, 'search_default_group_by_status': 1}</field>

    # @api.depends('product_id', 'customer_lead', 'product_uom_qty', 'product_uom', 'order_id.warehouse_id',
    #              'order_id.commitment_date', 'route_id')
    # def _compute_qty_at_date(self):
    #     """ Compute the quantity forecasted of product at delivery date. There are
    #     two cases:
    #      1. The quotation has a commitment_date, we take it as delivery date
    #      2. The quotation hasn't commitment_date, we compute the estimated delivery
    #         date based on lead time"""
    #     qty_processed_per_product = defaultdict(lambda: 0)
    #     grouped_lines = defaultdict(lambda: self.env['sale.order.line'])
    #     # We first loop over the SO lines to group them by warehouse and schedule
    #     # date in order to batch the read of the quantities computed field.
    #     now = fields.Datetime.now()
    #     for line in self:
    #         if not line.display_qty_widget:
    #             continue
    #
    #         if line.route_id:
    #             wh = self.env['stock.warehouse'].search([('delivery_route_id', '=', line.route_id)])
    #             if wh:
    #                 line.warehouse_id = wh
    #         elif not line.route_id and line.product_id.categ_id.:
    #
    #         line.warehouse_id = line.order_id.warehouse_id
    #         if line.order_id.commitment_date:
    #             date = line.order_id.commitment_date
    #         else:
    #             confirm_date = line.order_id.date_order if line.order_id.state in ['sale', 'done'] else now
    #             date = confirm_date + timedelta(days=line.customer_lead or 0.0)
    #         grouped_lines[(line.warehouse_id.id, date)] |= line
    #
    #     treated = self.browse()
    #     for (warehouse, scheduled_date), lines in grouped_lines.items():
    #         product_qties = lines.mapped('product_id').with_context(to_date=scheduled_date, warehouse=warehouse).read([
    #             'qty_available',
    #             'free_qty',
    #             'virtual_available',
    #         ])
    #         qties_per_product = {
    #             product['id']: (product['qty_available'], product['free_qty'], product['virtual_available'])
    #             for product in product_qties
    #         }
    #         for line in lines:
    #             line.scheduled_date = scheduled_date
    #             qty_available_today, free_qty_today, virtual_available_at_date = qties_per_product[line.product_id.id]
    #             line.qty_available_today = qty_available_today - qty_processed_per_product[line.product_id.id]
    #             line.free_qty_today = free_qty_today - qty_processed_per_product[line.product_id.id]
    #             line.virtual_available_at_date = virtual_available_at_date - qty_processed_per_product[
    #                 line.product_id.id]
    #             if line.product_uom and line.product_id.uom_id and line.product_uom != line.product_id.uom_id:
    #                 line.qty_available_today = line.product_id.uom_id._compute_quantity(line.qty_available_today,
    #                                                                                     line.product_uom)
    #                 line.free_qty_today = line.product_id.uom_id._compute_quantity(line.free_qty_today,
    #                                                                                line.product_uom)
    #                 line.virtual_available_at_date = line.product_id.uom_id._compute_quantity(
    #                     line.virtual_available_at_date, line.product_uom)
    #             qty_processed_per_product[line.product_id.id] += line.product_uom_qty
    #         treated |= lines
    #     remaining = (self - treated)
    #     remaining.virtual_available_at_date = False
    #     remaining.scheduled_date = False
    #     remaining.free_qty_today = False
    #     remaining.qty_available_today = False
    #     remaining.warehouse_id = False


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    narration = fields.Char(string='Narration', track_visibility="always")

    def action_view_logistic_gantt(self):
        self.ensure_one()
        business = []
        for rec in self.env['stock.picking'].search([('sale_id', '=', self.id)]):
            if rec.picking_type_id.business_line.id not in business:
                if rec.picking_type_id.business_line.id:
                    business.append(rec.picking_type_id.business_line.id)
        print(business)
        show = []
        for rec in self.env['plan.calendar'].search([]):
            if rec.business_line.id in business:
                if rec.status == 'available':
                    show.append(rec.id)
                elif rec.status == 'booked' and rec.delivery.sale_id.id == self.id:
                    show.append(rec.id)
        print(show)

        # print(business)

        return {
            'name': _('Logistic'),
            'res_model': 'plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_logistics_extra.plan_calendar_view_gantt').id, 'gantt'),
            ],
            'context': {'search_default_group_by_business_line': 1, 'search_default_group_by_status': 1},
            'domain': [('id', 'in', show)],
            'type': 'ir.actions.act_window',
        }

    # def action_view_logistic_gantt(self):
    #     self.ensure_one()
    #     active_id = self._context.get('active_id')
    #     active_model = self._context.get('active_model')
    #     sale_id = 0
    #     if active_model == 'sale.order':
    #         sale_id = active_id
    #         print(sale_id, 'sale 1')
    #     elif active_model == 'plan.calendar':
    #         sale_id = self.env['plan.calendar'].search([('id', '=', active_id)]).sale_id.id
    #         print(sale_id, 'sale 2')
    #     # business_line = self.delivery.picking_type_id.business_line
    #     # vals = {'delivery': self.delivery.id, 'status': self.status, 'period': self.period,
    #     #         'delivery_items': self.delivery_items}
    #     # self.write(vals)
    #     # print('inventory any write')
    #     return {
    #         'name': _('Logistic'),
    #         'res_model': 'delivery.reminder',
    #         'view_mode': 'form',
    #         'views': [
    #             (self.env.ref('pabs_logistics_extra.delivery_reminder_form_view').id, 'form'),
    #         ],
    #         'target': 'inline',
    #         'context': {"active_model": 'sale.order', "active_id": sale_id},
    #         # 'domain': [('id', 'in', show)],
    #         'type': 'ir.actions.act_window',
    #     }

    # < field
    # name = "search_view_id"
    # ref = "plan_calendar_search_view" / >
    # < field
    # name = "context" > {"search_default_avail": 1} < / field >
