from ast import literal_eval
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
import json
import logging
import pytz
import uuid

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from lxml import etree


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    x_dn_check = fields.Many2one('stock.picking', string="Delivery")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        if self.env.user.id not in self.location_id.x_user_ids.ids or self.env.user.id not in self.location_dest_id.x_user_dest_ids.ids:
            raise UserError(_("You are not authorised to validate this delivery"))
        res = super(StockPicking, self).button_validate()
        # if self.batch_id and self.batch_id.state == 'draft':
        #     self.batch_id.confirm_picking()

        return res

    # @api.depends('state')
    # def action_start_batch(self):
    #     if self.batch_id and self.batch_id.state == 'draft':
    #         # if self.state == 'done':
    #             self.batch_id.state = 'in_progress'

    def action_done(self):
        res = super(StockPicking, self).action_done()
        self.user_id = self.env.uid
        # self.x_slot.status = 'available'
        # self.x_slot.delivery = None
        # self.x_slot.note = ''
        # self.x_slot.period = None
        # self.x_slot.x_priority = '1'
        # self.x_slot.delivery_items = False
        #self.x_slot = False
        return res
        # if self.batch_id and self.x_logistics_team.team_type == 'subcontractor':
        #     consumable_line_ids = []
        #     for move_line in self.move_line_ids_without_package:
        #         if move_line.product_id.type == 'consu' and move_line.product_id.purchase_ok and move_line.product_id.subcontractor_service:
        #             consumable_line_ids.append(move_line)
        #     if consumable_line_ids:
        #         if self.transfer_purchase:
        #             # self.transfer_purchase = po
        #             # product = self.env['product.product'].search([('name', '=', 'Subcontractor Fees')])
        #             # print(product)
        #             for consumable_line_id in consumable_line_ids:
        #                 unit_price = 0
        #                 for seller_id in consumable_line_id.product_id.seller_ids:
        #                     if seller_id.name == self.x_logistics_team.team_owner:
        #                         unit_price = seller_id.price
        #
        #                 found = False
        #                 if self.transfer_purchase.order_line:
        #                     for order_line in self.transfer_purchase.order_line:
        #                         if order_line.x_delivery_order.id == self.id and order_line.product_id.id == consumable_line_id.product_id.id:
        #                             order_line.product_qty += consumable_line_id.qty_done
        #                             found = True
        #                             break
        #                 if not found:
        #                     self.transfer_purchase.order_line = [(0, 0, {'product_id': consumable_line_id.product_id.id,
        #                                                                  'name': consumable_line_id.product_id.name,
        #                                                                  'x_delivery_order': self.id,
        #                                                                  'x_stock_move_line_id': consumable_line_id.id,
        #                                                                  'product_qty': consumable_line_id.qty_done,
        #                                                                  'date_planned': self.scheduled_date,
        #                                                                  'product_uom': consumable_line_id.product_uom_id.id,
        #                                                                  'price_unit': unit_price})]
        #
        # if not self.batch_id and self.src_picking_id:
        #     consumable_line_ids = []
        #     for move_line in self.move_line_ids_without_package:
        #         if move_line.product_id.type == 'consu' and move_line.product_id.purchase_ok and move_line.product_id.subcontractor_service:
        #             consumable_line_ids.append(move_line)
        #
        #     if consumable_line_ids and self.src_picking_id.transfer_purchase:
        #         for consumable_line_id in consumable_line_ids:
        #             count = consumable_line_id.qty_done
        #             for order_line in self.src_picking_id.transfer_purchase.order_line:
        #                 if order_line.x_delivery_order.id == self.src_picking_id.id and order_line.product_id.id == consumable_line_id.product_id.id:
        #                     if order_line.qty_received >= count:
        #                         order_line.qty_received -= count
        #                         count = 0
        #                     else:
        #                         count -= order_line.qty_received
        #                         order_line.qty_received = 0

        # self.src_picking_id.batch_id.x_batch_po

    def _create_backorder(self):

        """ This method is called when the user chose to create a backorder. It will create a new
        picking, the backorder, and move the stock.moves that are not `done` or `cancel` into it.
        """
        backorders = self.env['stock.picking']
        for picking in self:
            moves_to_backorder = picking.move_lines.filtered(lambda x: x.state not in ('done', 'cancel'))
            if moves_to_backorder:
                backorder_picking = picking.copy({
                    'name': '/',
                    'move_lines': [],
                    'move_line_ids': [], 'x_slot': False,
                    'backorder_id': picking.id
                })
                picking.message_post(
                    body=_(
                        'The backorder <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> has been created.') % (
                             backorder_picking.id, backorder_picking.name))
                moves_to_backorder.write({'picking_id': backorder_picking.id})
                moves_to_backorder.mapped('package_level_id').write({'picking_id': backorder_picking.id})
                moves_to_backorder.mapped('move_line_ids').write({'picking_id': backorder_picking.id})
                backorder_picking.action_assign()
                backorders |= backorder_picking
        return backorders

    @api.depends('x_slot.period')
    def _compute_period(self):
        for rec in self:
            if rec.x_slot.period:
                rec.period = rec.x_slot.period
            else:
                rec.period = 0

    @api.depends('move_ids_without_package')
    def _compute_x_total_qty_done(self):
        for rec in self:
            sale_line_ids = []
            qty_sum = 0
            for move in rec.move_ids_without_package:
                if move.sale_line_id not in sale_line_ids:
                    sale_line_ids.append(move.sale_line_id)
            # mrp.bom
            if sale_line_ids:
                for sale_line_id in sale_line_ids:
                    bom_count = 0
                    qty_sub_sum = 0
                    bom_line_ids = self.env['sale.order.line'].search(
                        [('id', '=', sale_line_id.id)]).product_id.variant_bom_ids.bom_line_ids
                    if bom_line_ids:
                        for bom_line_id in bom_line_ids:
                            bom_count += bom_line_id.product_qty
                    for move in rec.move_ids_without_package:
                        if move.sale_line_id == sale_line_id:
                            qty_sub_sum += move.quantity_done
                    if bom_count > 0:
                        qty_sum += (qty_sub_sum / bom_count)
                    else:
                        qty_sum += qty_sub_sum
            rec.x_total_qty_done = qty_sum

    @api.depends('move_ids_without_package')
    def _compute_x_total_qty_demand(self):
        for rec in self:
            sale_line_ids = []
            qty_sum = 0
            for move in rec.move_ids_without_package:
                if move.sale_line_id not in sale_line_ids:
                    sale_line_ids.append(move.sale_line_id)
            # mrp.bom
            if sale_line_ids:
                for sale_line_id in sale_line_ids:
                    bom_count = 0
                    qty_sub_sum = 0
                    bom_line_ids = self.env['sale.order.line'].search(
                        [('id', '=', sale_line_id.id)]).product_id.variant_bom_ids.bom_line_ids
                    if bom_line_ids:
                        for bom_line_id in bom_line_ids:
                            bom_count += bom_line_id.product_qty
                    for move in rec.move_ids_without_package:
                        if move.sale_line_id == sale_line_id:
                            qty_sub_sum += move.product_uom_qty
                    if bom_count > 0:
                        qty_sum += (qty_sub_sum / bom_count)
                    else:
                        qty_sum += qty_sub_sum
            rec.x_total_qty_demand = qty_sum

    @api.depends('move_ids_without_package')
    def _compute_x_total_qty_reserved(self):
        for rec in self:
            sale_line_ids = []
            qty_sum = 0
            for move in rec.move_ids_without_package:
                if move.sale_line_id not in sale_line_ids:
                    sale_line_ids.append(move.sale_line_id)
            # mrp.bom
            if sale_line_ids:
                for sale_line_id in sale_line_ids:
                    bom_count = 0
                    qty_sub_sum = 0
                    bom_line_ids = self.env['sale.order.line'].search(
                        [('id', '=', sale_line_id.id)]).product_id.variant_bom_ids.bom_line_ids
                    if bom_line_ids:
                        for bom_line_id in bom_line_ids:
                            bom_count += bom_line_id.product_qty
                    for move in rec.move_ids_without_package:
                        if move.sale_line_id == sale_line_id:
                            qty_sub_sum += move.reserved_availability
                    if bom_count > 0:
                        qty_sum += (qty_sub_sum / bom_count)
                    else:
                        qty_sum += qty_sub_sum
            rec.x_total_qty_reserved = qty_sum

    # @api.depends('sale_id.x_amount_residual')
    # def _compute_total_amount(self):
    #     for rec in self:
    #         total = 0
    #         if rec.sale_order_type == 'paid_on_delivery':
    #             total = rec.sale_id.x_amount_residual
    #         rec.x_total_amount = total
    @api.depends('sale_id.x_amount_residual', 'sale_order_type')
    def _compute_total_amount(self):
        for rec in self:
            total = 0
            if rec.sale_order_type != 'credit_sale':
                total = rec.sale_id.x_amount_residual
            rec.x_total_amount = total

    # def _compute_purchase_narration(self):
    #     for rec in self:
    #         if rec.purchase_id.narration:
    #             rec.narration = rec.purchase_id.narration
    #         else:
    #             rec.narration = ''

    def _compute_sale_narration(self):
        for rec in self:
            if rec.sale_id.narration:
                rec.x_narration = rec.sale_id.narration
            else:
                rec.x_narration = ''

    def _compute_return_picking_ids(self):
        for rec in self:
            return_pickings = self.env['stock.picking'].search(
                [('src_picking_id', '=', rec.id)])
            rec.return_picking_ids = return_pickings

    # narration = fields.Char(string='Purchase Narration', track_visibility="always", compute=_compute_purchase_narration,
    #                         help="Purchase Narration")
    x_narration = fields.Char(string='Sale Narration', track_visibility="always", compute=_compute_sale_narration,
                              help="Sale Narration")
    x_salesperson = fields.Many2one(
        'res.users', string='Salesperson', index=True, tracking=2, default=False, related='sale_id.user_id', store=True)
    x_salesteam = fields.Many2one(related='sale_id.team_id', store=True)
    transfer_narration = fields.Char(string='Transfer Narration', track_visibility="always")
    received_by = fields.Char(string='Received By', track_visibility="always")
    reference = fields.Char(string='Reference', track_visibility="always")
    code = fields.Selection(related="picking_type_id.code", store=1)
    x_total_qty_done = fields.Float('Total Done Qty', compute=_compute_x_total_qty_done, store=1)
    x_total_qty_demand = fields.Float('Demand Qty', compute=_compute_x_total_qty_demand, store=1)
    x_total_qty_reserved = fields.Float('Reserved Qty', compute=_compute_x_total_qty_reserved, store=1)
    x_logistics_team = fields.Many2one('logistics.team', string='Transfer Team', related='batch_id.x_team', store=1,
                                       tracking=True)
    x_logistics_team_returns = fields.Many2one('logistics.team', string='Transfer Team',
                                               compute='_compute_x_logistics_team_returns', store=1)
    period = fields.Selection(string='Preferred Period',
                              selection=[('morning', 'Morning'), ('evening', 'Evening')], compute=_compute_period,
                              store=1)
    x_slot = fields.Many2one('plan.calendar', string="Calendar Slot")
    x_business_line = fields.Many2one('business.line', string="Business Line", related='picking_type_id.business_line',
                                      store=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    x_total_amount = fields.Monetary(string='Amount Due', compute='_compute_total_amount')
    x_invoice_address = fields.Many2one('res.partner', string='Invoice Address', related='sale_id.partner_invoice_id')
    sequence = fields.Integer(string='Sequence', default=10)
    x_is_delivered = fields.Boolean(string="Is Delivered", copy=False)
    transfer_purchase = fields.Many2one('purchase.order', related='batch_id.x_batch_po', string='Transfer Purchase')
    src_picking_id = fields.Many2one('stock.picking', string='Source Picking', copy=False)
    return_picking_ids = fields.Many2many('stock.picking', string='Return Pickings',
                                          compute=_compute_return_picking_ids)
    return_picking_ids_count = fields.Integer(string='Return Deliveries count',
                                              compute='_compute_return_picking_ids_count')
    x_batch_id_state = fields.Selection([('draft', 'Draft'),
                                         ('in_progress', 'In Progress'),
                                         ('done', 'Done'),
                                         ('cancel', 'Cancelled')], default='draft', copy=False,
                                        related='batch_id.state')
    x_client_order_ref = fields.Char(string='Customer Reference', related='sale_id.client_order_ref', store=True,
                                     copy=False)
    x_team_mobile = fields.Char(string='Team Mobile', related='x_logistics_team.x_team_mobile_no')
    x_delivery_state = fields.Selection([
        ('delivered', 'Delivered'),
        ('partial', 'Partially Delivered'),
        ('returned', 'Returned')],
        string='Delivery Status', compute='_compute_x_delivery_state')
    state = fields.Selection(selection_add=[('out_delivery', 'Out For Delivery'), ('done',)])
    x_backorder_ids_count = fields.Integer(string='Back orders count', compute='_compute_x_backorder_ids_count')
    x_is_overloaded = fields.Boolean(related="batch_id.x_is_overloaded", store=True)
    x_dn_status = fields.Selection([('reserved', 'Reserved'), ('normal', 'Normal')], string="Slot Delivery Type", store=True)
    x_reschedule_count = fields.Integer(string="Reschedule History", compute="_compute_reschedule_history")
    x_care_of_state = fields.Selection([('request', 'Requested'), ('approve', 'Approved'), ('refuse', 'Refused')], string="Status")
    x_approval_user = fields.Many2one('res.users', string="Care Of By", store=True, domain=lambda self: [('groups_id', 'in', self.env.ref('pabs_logistics_extra.group_care_of').id)])
    x_ticket_count = fields.Integer(string="Ticket")
    x_reschedule_confirm = fields.Selection([('confirm', 'Confirmed'), ('pending', 'Pending')], string="Reschedule Confirmation")
    x_urgent_request = fields.Selection([('urgent', 'Urgent')], string="Urgency")

    def _compute_x_backorder_ids_count(self):
        for rec in self:
            rec.x_backorder_ids_count = len(rec.backorder_ids)

    def action_view_backorder_picking(self):
        return {
            'name': _('Back Orders'),
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('stock.vpicktree').id, 'tree'),
                (self.env.ref('stock.view_picking_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.backorder_ids.ids)],
        }


    def _compute_x_delivery_state(self):
        for rec in self:
            order_qty = sum(rec.move_line_ids_without_package.mapped('qty_done'))
            returns = rec.return_picking_ids.filtered(lambda p: p.state == 'done')
            returns_qty = sum(rec.return_picking_ids.filtered(lambda p: p.state == 'done').move_line_ids_without_package.mapped('qty_done'))
            print(returns, returns_qty)
            if rec.backorder_ids or returns:
                if rec.backorder_ids:
                    rec.x_delivery_state = 'partial'
                if returns:
                    if returns_qty >= order_qty:
                        rec.x_delivery_state = 'returned'
                    else:
                        rec.x_delivery_state = 'partial'
            else:
                if rec.x_is_delivered:
                    rec.x_delivery_state = 'delivered'
                else:
                    rec.x_delivery_state = 0



    @api.depends('src_picking_id', 'x_logistics_team')
    def _compute_x_logistics_team_returns(self):
        for rec in self:
            if rec.x_logistics_team:
                rec.x_logistics_team_returns = rec.x_logistics_team
            else:
                if rec.src_picking_id and rec.src_picking_id.x_logistics_team:
                    rec.x_logistics_team_returns = rec.src_picking_id.x_logistics_team
                else:
                    rec.x_logistics_team_returns = None

    def _compute_return_picking_ids_count(self):
        for rec in self:
            rec.return_picking_ids_count = len(rec.return_picking_ids)


    def create_ticket(self):
        return {
            "name": "Ticket",
            "view_mode": "form",
            "res_model": "helpdesk.ticket",
            "type": "ir.actions.act_window",
            "target": "current",
            "context": {'default_sale_order_id': self.sale_id.id, "default_partner_id": self.partner_id.id,
                        'default_x_dn_check': self.id,
                        'default_ticket_type_id': self.env.ref('pabs_repair.product_cancellation').id,
                        'default_team_id': self.env.ref('pabs_repair.product_cancellation_ticket_team').id,
                        }
        }

    def action_view_tickets(self):
        vals = self.env['helpdesk.ticket'].search([('x_dn_check', 'in', self.ids)]).ids
        return {
            'name': _('Tickets'),
            'res_model': 'helpdesk.ticket',
            'view_mode': 'kanban,form',
            'views': [
                (self.env.ref('helpdesk.helpdesk_ticket_view_kanban').id, 'kanban'),
                (self.env.ref('helpdesk.helpdesk_ticket_view_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', vals or self.move_ids_without_package.mapped('sale_line_id.x_ticket_cancel').ids)],
        }

    # def test(self):
    #     delivery_id = self._context.get('delivery_id')
    #     business_line = self.env['stock.picking'].search([('id', '=', delivery_id)]).picking_type_id.business_line.id
    #     self.ensure_one()
    #     sale_id = self.env['stock.picking'].search([('id', '=', delivery_id)]).sale_id.id
    #     moves = self.env['stock.picking'].search([('id', '=', delivery_id)]).move_ids_without_package
    #     product_ids = []
    #     for move in moves:
    #         product_ids.append(move.product_id.id)
    #     forecast_dates = []
    #     for product_id in product_ids:
    #         first_forecast_id = self.env['report.stock.quantity'].search([('product_id', '=', product_id)],
    #                                                                      order='id desc', limit=1).id
    #         product_forecast_ids = self.env['report.stock.quantity'].search([('product_id', '=', product_id)]).ids
    #         count = 0
    #         if product_forecast_ids:
    #             for product_forecast_id in product_forecast_ids:
    #                 q = """SELECT COUNT(*) FROM report_stock_quantity WHERE id = (%s)"""
    #                 self._cr.execute(q % product_forecast_id)
    #                 c = self._cr.dictfetchall()
    #                 if c[0]['count'] > count:
    #                     count = c[0]['count']
    #                     first_forecast_id = product_forecast_id
    #         forecast_ids = self.env['report.stock.quantity'].search(
    #             [('product_id', '=', product_id), ('id', '!=', first_forecast_id)]).ids
    #         product_first_forecasts = False
    #         product_forecasts = False
    #
    #         if first_forecast_id:
    #             query_product_first_forecasts = """SELECT * FROM report_stock_quantity WHERE id = (%s)"""
    #             self._cr.execute(query_product_first_forecasts % first_forecast_id)
    #             product_first_forecasts = self._cr.dictfetchall()
    #
    #         if forecast_ids:
    #             tuple_forecast_ids = tuple(forecast_ids)
    #             placeholder = '%s'
    #             placeholders = ', '.join(placeholder for _ in tuple_forecast_ids)
    #             query_product_forecasts = """SELECT * FROM report_stock_quantity WHERE id IN (%s)""" % placeholders
    #             self._cr.execute(query_product_forecasts % tuple_forecast_ids)
    #             product_forecasts = self._cr.dictfetchall()
    #         if product_first_forecasts and product_forecasts:
    #             for product_first_forecast in product_first_forecasts:
    #                 for product_forecast in product_forecasts:
    #                     if product_first_forecast['state'] == 'forecast' and product_forecast['state'] == 'forecast':
    #                         if product_first_forecast['date'] == product_forecast['date']:
    #                             if product_first_forecast['product_qty'] and product_forecast['product_qty']:
    #                                 product_first_forecast['product_qty'] += product_forecast['product_qty']
    #         if product_first_forecasts:
    #             for product_first_forecast in product_first_forecasts:
    #                 if product_first_forecast['product_qty'] < 0:
    #                     forecast_dates.append(product_first_forecast['date'].strftime("%y-%m-%d"))
    #     available_slots = self.env['plan.calendar'].search(
    #         [('status', '=', 'available'), ('business_line', '=', business_line)])
    #     exclude_ids = []
    #     if available_slots and forecast_dates:
    #         for available_slot in available_slots:
    #             if available_slot.start_datetime:
    #                 if available_slot.start_datetime.strftime("%y-%m-%d") in forecast_dates:
    #                     exclude_ids.append(available_slot.id)
    #     return {
    #         'name': _('Logistic'),
    #         'res_model': 'plan.calendar',
    #         'view_mode': 'gantt',
    #         'views': [
    #             (self.env.ref('pabs_logistics_extra.plan_calendar_view_gantt').id, 'gantt'),
    #         ],
    #         'target': 'main',
    #         'context': {"active_model": 'sale.order', "active_id": sale_id, 'search_default_group_by_business_line': 1, 'search_default_group_by_status': 1},
    #         'domain': [('business_line', '=', business_line), ('status', '=', 'available'),
    #                    ('id', 'not in', exclude_ids),('start_datetime', '>=', fields.Date.today())],
    #         'type': 'ir.actions.act_window',
    #     }

    # def test(self):
    #     delivery_id = self._context.get('delivery_id')
    #     business_line = self.env['stock.picking'].search([('id', '=', delivery_id)]).picking_type_id.business_line.id
    #     self.ensure_one()
    #     sale_id = self.env['stock.picking'].search([('id', '=', delivery_id)]).sale_id.id
    #     moves = self.env['stock.picking'].search([('id', '=', delivery_id)]).move_ids_without_package
    #     product_ids = []
    #     for move in moves:
    #         product_ids.append(move.product_id.id)
    #     latest_negative_forecast = False
    #     for product_id in product_ids:
    #         for day in reversed(range(45)):
    #             q = """SELECT SUM(product_qty) FROM report_stock_quantity WHERE product_id = (%s) AND date = (%s) AND state = 'forecast' AND product_qty IS NOT NULL"""
    #             forecast_date = fields.Date.today() + timedelta(days=day)
    #             forecast_date_str = "'" + str(forecast_date.strftime("%Y-%m-%d")) + "'"
    #             self._cr.execute(q % (product_id, forecast_date_str))
    #             c = self._cr.dictfetchall()
    #             if c[0]['sum'] < 0:
    #                 if not latest_negative_forecast:
    #                     latest_negative_forecast = forecast_date
    #                     break
    #                 else:
    #                     if latest_negative_forecast < forecast_date:
    #                         latest_negative_forecast = forecast_date
    #                         break
    #     if not latest_negative_forecast:
    #         latest_negative_forecast = fields.Date.today() - timedelta(days=1)
    #     return {
    #         'name': _('Logistic'),
    #         'res_model': 'plan.calendar',
    #         'view_mode': 'gantt',
    #         'views': [
    #             (self.env.ref('pabs_logistics_extra.plan_calendar_view_gantt').id, 'gantt'),
    #         ],
    #         'target': 'main',
    #         'context': {"active_model": 'sale.order', "active_id": sale_id, 'search_default_group_by_business_line': 1,
    #                     'search_default_group_by_status': 1},
    #         'domain': [('business_line', '=', business_line), ('status', '=', 'available'),
    #                    ('start_datetime', '>', latest_negative_forecast), ('start_datetime', '>=', fields.Date.today())],
    #         'type': 'ir.actions.act_window',
    #     }

    # LATEST FORECAST UPSATE
    # def test(self):
    #     delivery_id = self._context.get('delivery_id')
    #     business_line = self.env['stock.picking'].search([('id', '=', delivery_id)]).picking_type_id.business_line.id
    #     self.ensure_one()
    #     sale_id = self.env['stock.picking'].search([('id', '=', delivery_id)]).sale_id.id
    #     moves = self.env['stock.picking'].search([('id', '=', delivery_id)]).move_ids_without_package
    #     product_ids = []
    #     for move in moves:
    #         product_ids.append(move.product_id.id)
    #     earliest_positive_forecast_date = False
    #     for product_id in product_ids:
    #         q = """SELECT SUM(product_qty), date FROM report_stock_quantity
    #                 WHERE product_id = (%s) AND state = 'forecast' AND date BETWEEN (%s) AND (%s)
    #                 GROUP BY date HAVING SUM(product_qty) >= 0
    #                 ORDER BY date LIMIT 1"""
    #         today_str = "'" + str(fields.Date.today().strftime("%Y-%m-%d")) + "'"
    #         forecast_date = fields.Date.today() + timedelta(days=60)
    #         forecast_date_str = "'" + str(forecast_date.strftime("%Y-%m-%d")) + "'"
    #         self._cr.execute(q % (product_id, today_str, forecast_date_str))
    #         c = self._cr.dictfetchall()
    #         if c:
    #             if not earliest_positive_forecast_date:
    #                 earliest_positive_forecast_date = c[0]['date']
    #             else:
    #                 if earliest_positive_forecast_date < c[0]['date']:
    #                     earliest_positive_forecast_date = c[0]['date']
    #     if earliest_positive_forecast_date:
    #         show = []
    #         for i in range(35):
    #             day = datetime.combine(fields.Date.today() + timedelta(days=i), datetime.min.time())
    #             slot = self.env['plan.calendar'].search(
    #                 [('business_line', '=', business_line), ('status', '=', 'available'),
    #                  ('start_datetime', '>=', day), ('start_datetime', '<', day + timedelta(days=1))], limit=10).ids
    #             if slot:
    #                 show = show + slot
    #             # if slot:
    #             #     for s in slot:
    #             #         show.append(s)
    #         return {
    #             'name': _('Logistic'),
    #             'res_model': 'plan.calendar',
    #             'view_mode': 'gantt',
    #             'views': [
    #                 (self.env.ref('pabs_logistics_extra.plan_calendar_view_gantt').id, 'gantt'),
    #             ],
    #             'target': 'main',
    #             'context': {"active_model": 'sale.order', "active_id": sale_id,
    #                         'search_default_group_by_business_line': 1,
    #                         'search_default_group_by_status': 1},
    #             'domain': [('business_line', '=', business_line), ('status', '=', 'available'),
    #                        ('start_datetime', '>=', earliest_positive_forecast_date),
    #                        ('start_datetime', '>=', fields.Date.today() + timedelta(days=1)), ('id', 'in', show)],
    #             'type': 'ir.actions.act_window',
    #         }
    #     else:
    #         return {
    #             'name': _('Logistic'),
    #             'res_model': 'plan.calendar',
    #             'view_mode': 'gantt',
    #             'views': [
    #                 (self.env.ref('pabs_logistics_extra.plan_calendar_view_gantt').id, 'gantt'),
    #             ],
    #             'target': 'main',
    #             'context': {"active_model": 'sale.order', "active_id": sale_id,
    #                         'search_default_group_by_business_line': 1,
    #                         'search_default_group_by_status': 1},
    #             'domain': [('status', '=', False)],
    #             'type': 'ir.actions.act_window',
    #         }

    # ON OFF WAY SIMPLE AND FAST BUT NOT ACCURATE

    def test(self):
        delivery_id = self._context.get('delivery_id')
        business_line = self.env['stock.picking'].search([('id', '=', delivery_id)]).picking_type_id.business_line.id
        self.ensure_one()
        sale_id = self.env['stock.picking'].search([('id', '=', delivery_id)]).sale_id
        moves = self.env['stock.picking'].search([('id', '=', delivery_id)]).move_ids_without_package
        product_ids = sale_id.order_line.mapped('product_id').filtered(lambda p: p.type == 'product')
        lead_times = product_ids.mapped('sale_delay')
        max_lead = 0
        if lead_times:
            max_lead = max(lead_times)
        print(product_ids, 'PROD')
        print(lead_times, 'DELAY')
        print(max_lead, 'MAX DELAY')
        prod_dict = {}
        for move in moves:
            if move.product_id.type == 'product':
                if move.product_id.id in prod_dict:
                    prod_dict[move.product_id.id] += move.product_uom_qty
                else:
                    prod_dict[move.product_id.id] = move.product_uom_qty
        print(prod_dict)
        stock_available = True
        if prod_dict:
            for prod, qty in prod_dict.items():
                product = self.env['product.product'].browse(prod)
                if (product.virtual_available + qty) < 0:
                    stock_available = False
                    break
                print(product.name, ' ', product.virtual_available, ' ', qty)
        print(stock_available, 'STOCK')
        if stock_available:
            show = []
            for i in range(35):
                day = datetime.combine(fields.Date.today() + timedelta(days=i), datetime.min.time())
                slot = self.env['plan.calendar'].search(
                    [('business_line', '=', business_line), ('status', '=', 'available'),
                     ('start_datetime', '>=', day), ('start_datetime', '<', day + timedelta(days=1))], limit=10).ids
                if slot:
                    show = show + slot
            return {
                'name': _('Logistic'),
                'res_model': 'plan.calendar',
                'view_mode': 'gantt',
                'views': [
                    (self.env.ref('pabs_logistics_extra.plan_calendar_view_gantt').id, 'gantt'),
                ],
                'target': 'main',
                'context': {"active_model": 'sale.order', "active_id": sale_id.id,
                            'search_default_group_by_business_line': 1,
                            'search_default_group_by_status': 1},
                'domain': [('business_line', '=', business_line), ('status', '=', 'available'),
                           ('start_datetime', '>=', fields.Date.today() + timedelta(days=1)), ('id', 'in', show)],
                'type': 'ir.actions.act_window',
            }
        else:
            if max_lead:
                show = []
                for i in range(35 - int(max_lead)):
                    day = datetime.combine(fields.Date.today() + timedelta(days=max_lead + i), datetime.min.time())
                    slot = self.env['plan.calendar'].search(
                        [('business_line', '=', business_line), ('status', '=', 'available'),
                         ('start_datetime', '>=', day), ('start_datetime', '<', day + timedelta(days=1))], limit=10).ids
                    if slot:
                        show = show + slot
                return {
                    'name': _('Logistic'),
                    'res_model': 'plan.calendar',
                    'view_mode': 'gantt',
                    'views': [
                        (self.env.ref('pabs_logistics_extra.plan_calendar_view_gantt').id, 'gantt'),
                    ],
                    'target': 'main',
                    'context': {"active_model": 'sale.order', "active_id": sale_id.id,
                                'search_default_group_by_business_line': 1,
                                'search_default_group_by_status': 1},
                    'domain': [('business_line', '=', business_line), ('status', '=', 'available'),
                               ('start_datetime', '>=', fields.Date.today() + timedelta(days=1)), ('id', 'in', show)],
                    'type': 'ir.actions.act_window',
                }
            else:
                return {
                    'name': _('Logistic'),
                    'res_model': 'plan.calendar',
                    'view_mode': 'gantt',
                    'views': [
                        (self.env.ref('pabs_logistics_extra.plan_calendar_view_gantt').id, 'gantt'),
                    ],
                    'target': 'main',
                    'context': {"active_model": 'sale.order', "active_id": sale_id.id,
                                'search_default_group_by_business_line': 1,
                                'search_default_group_by_status': 1},
                    'domain': [('status', '=', False)],
                    'type': 'ir.actions.act_window',
                }

    def reserve_slots(self):
        delivery_id = self._context.get('delivery_id')
        business_line = self.env['stock.picking'].search([('id', '=', delivery_id)]).picking_type_id.business_line
        self.ensure_one()
        sale_id = self.env['stock.picking'].search([('id', '=', delivery_id)]).sale_id
        moves = self.env['stock.picking'].search([('id', '=', delivery_id)]).move_ids_without_package
        product_ids = sale_id.order_line.mapped('product_id').filtered(lambda p: p.type == 'product')
        lead_times = product_ids.mapped('sale_delay')
        max_lead = 0
        if lead_times:
            max_lead = max(lead_times)
        prod_dict = {}
        for move in moves:
            if move.product_id.type == 'product':
                if move.product_id.id in prod_dict:
                    prod_dict[move.product_id.id] += move.product_uom_qty
                else:
                    prod_dict[move.product_id.id] = move.product_uom_qty
        stock_available = True
        if prod_dict:
            for prod, qty in prod_dict.items():
                product = self.env['product.product'].browse(prod)
                if (product.virtual_available + qty) < 0:
                    stock_available = False
                    break
        if stock_available:
            show = []
            for i in range(35):
                day = datetime.combine(fields.Date.today() + timedelta(days=i), datetime.min.time())
                slot = self.env['plan.calendar'].search(
                    [('business_line', '=', business_line.id), ('status', '=', 'available'),
                     ('start_datetime', '>=', day), ('start_datetime', '<', day + timedelta(days=1))], limit=10).ids
                if slot:
                    show = show + slot
            return {
                'name': _('Logistic'),
                'res_model': 'plan.calendar',
                'view_mode': 'gantt',
                'views': [
                    (self.env.ref('pabs_logistics_extra.plan_calendar_view_gantt').id, 'gantt'),
                ],
                'target': 'main',
                'context': {"active_model": 'sale.order', "active_id": sale_id.id,
                            'search_default_group_by_business_line': 1,
                            'search_default_group_by_status': 1},
                'domain': [('business_line', '=', business_line.id), ('status', '=', 'available'),
                           ('start_datetime', '>=', fields.Date.today() + timedelta(days=int(business_line.no_days) or 1)), ('id', 'in', show)],
                'type': 'ir.actions.act_window',
            }
        else:
            if max_lead:
                show = []
                for i in range(35 - int(max_lead)):
                    day = datetime.combine(fields.Date.today() + timedelta(days=max_lead + i), datetime.min.time())
                    slot = self.env['plan.calendar'].search(
                        [('business_line', '=', business_line.id), ('status', '=', 'available'),
                         ('start_datetime', '>=', day), ('start_datetime', '<', day + timedelta(days=1))], limit=10).ids
                    if slot:
                        show = show + slot
                return {
                    'name': _('Logistic'),
                    'res_model': 'plan.calendar',
                    'view_mode': 'gantt',
                    'views': [
                        (self.env.ref('pabs_logistics_extra.plan_calendar_view_gantt').id, 'gantt'),
                    ],
                    'target': 'main',
                    'context': {"active_model": 'sale.order', "active_id": sale_id.id,
                                'search_default_group_by_business_line': 1,
                                'search_default_group_by_status': 1},
                    'domain': [('business_line', '=', business_line.id), ('status', '=', 'available'),
                               ('start_datetime', '>=', fields.Date.today() + timedelta(days=int(business_line.no_days) or 1)), ('id', 'in', show)],
                    'type': 'ir.actions.act_window',
                }
            else:
                return {
                    'name': _('Logistic'),
                    'res_model': 'plan.calendar',
                    'view_mode': 'gantt',
                    'views': [
                        (self.env.ref('pabs_logistics_extra.plan_calendar_view_gantt').id, 'gantt'),
                    ],
                    'target': 'main',
                    'context': {"active_model": 'sale.order', "active_id": sale_id.id,
                                'search_default_group_by_business_line': 1,
                                'search_default_group_by_status': 1},
                    'domain': [('status', '=', False)],
                    'type': 'ir.actions.act_window',
                }

    def action_plan_calendar_transfer(self):
        business_line = self._context.get('business_line')
        delivery_id = self._context.get('delivery_id')
        show = []
        for i in range(35):
            day = datetime.combine(fields.Date.today() + timedelta(days=i), datetime.min.time())
            slot = self.env['plan.calendar'].search(
                [('business_line', '=', business_line), ('status', '=', 'available'),
                 ('start_datetime', '>=', day), ('start_datetime', '<', day + timedelta(days=1))], limit=10).ids
            if slot:
                for s in slot:
                    show.append(s)
        return {
            'name': _('Logistic'),
            'res_model': 'plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_logistics_extra.plan_calendar_transfer_view_gantt').id, 'gantt'),
            ],
            'target': 'new',
            # 'context': {"active_model": 'sale.order', "active_id": sale_id},
            'domain': [('business_line', '=', business_line), ('status', '=', 'available'), ('id', 'in', show)],
            'type': 'ir.actions.act_window',
            'context': {'x_dn_status': self.x_dn_status}
        }

    def action_plan_calendar_shift_transfer(self):
        business_line = self._context.get('business_line')
        delivery_id = self._context.get('delivery_id')
        slot = self._context.get('slot')
        show = []
        for i in range(35):
            day = datetime.combine(fields.Date.today() + timedelta(days=i), datetime.min.time())
            slot = self.env['plan.calendar'].search(
                [('business_line', '=', business_line), ('status', '=', 'available'),
                 ('start_datetime', '>=', day), ('start_datetime', '<', day + timedelta(days=1))], limit=10).ids
            if slot:
                for s in slot:
                    show.append(s)
        return {
            'name': _('Logistic'),
            'res_model': 'plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_logistics_extra.plan_calendar_shift_transfer_view_gantt').id, 'gantt'),
            ],
            'target': 'new',
            # 'context': {"active_model": 'sale.order', "active_id": sale_id},
            'domain': [('business_line', '=', business_line), ('status', '=', 'available'), ('id', 'in', show)],
            'type': 'ir.actions.act_window',
            'context': {'x_dn_status': self.x_dn_status}
        }

    def action_view_history_reschedule(self):
        return {
            'name': _('History'),
            'res_model': 'delivery.reschedule',
            'view_mode': 'list',
            'domain': [('name', '=', self.id)],
            'type': 'ir.actions.act_window',
        }

    def _compute_reschedule_history(self):
        for pick in self:
            pick.x_reschedule_count = self.env['delivery.reschedule'].search_count([('name', '=', self.id)])

    def action_delivered(self):
        self.x_is_delivered = True

    def action_batch_done_delivered(self):
        if self.batch_id and self.x_logistics_team.team_type == 'subcontractor':
            consumable_line_ids = []
            for move_line in self.move_line_ids_without_package:
                if move_line.product_id.type == 'consu' and move_line.product_id.purchase_ok and move_line.product_id.subcontractor_service:
                    consumable_line_ids.append(move_line)
            if consumable_line_ids:
                if self.transfer_purchase:
                    # self.transfer_purchase = po
                    # product = self.env['product.product'].search([('name', '=', 'Subcontractor Fees')])
                    # print(product)
                    for consumable_line_id in consumable_line_ids:
                        unit_price = 0
                        for seller_id in consumable_line_id.product_id.seller_ids:
                            if seller_id.name == self.x_logistics_team.team_owner:
                                unit_price = seller_id.price

                        found = False
                        if self.transfer_purchase.order_line:
                            for order_line in self.transfer_purchase.order_line:
                                if order_line.x_delivery_order.id == self.id and order_line.product_id.id == consumable_line_id.product_id.id:
                                    order_line.product_qty += consumable_line_id.qty_done
                                    found = True
                                    break
                        if not found:
                            self.transfer_purchase.order_line = [(0, 0, {'product_id': consumable_line_id.product_id.id,
                                                                         'name': consumable_line_id.product_id.name,
                                                                         'x_delivery_order': self.id,
                                                                         'x_stock_move_line_id': consumable_line_id.id,
                                                                         'product_qty': consumable_line_id.qty_done,
                                                                         'date_planned': self.scheduled_date,
                                                                         'product_uom': consumable_line_id.product_uom_id.id,
                                                                         'price_unit': unit_price})]
        if self.batch_id and self.x_logistics_team.team_type == 'subcontractor':
            for line in self.transfer_purchase.order_line:

                if line.x_delivery_order.id == self.id:
                    line.qty_received = line.product_qty

                    returned_ids = self.env['stock.picking'].search(
                        [('src_picking_id', '=', self.id), ('code', '=', 'incoming')])
                    if returned_ids:
                        for returned_id in returned_ids:
                            consumable_line_ids = []
                            for move_line in returned_id.move_line_ids_without_package:
                                if move_line.product_id.type == 'consu' and move_line.product_id.purchase_ok and move_line.product_id.subcontractor_service:
                                    consumable_line_ids.append(move_line)

                            if consumable_line_ids:
                                for consumable_line_id in consumable_line_ids:
                                    count = consumable_line_id.qty_done
                                    if line.x_delivery_order.id == returned_id.src_picking_id.id and line.product_id.id == consumable_line_id.product_id.id:
                                        if line.qty_received >= count:
                                            line.qty_received -= count
                                            count = 0
                                        else:
                                            count -= line.qty_received
                                            line.qty_received = 0

        if not self.batch_id and self.src_picking_id:
            consumable_line_ids = []
            for move_line in self.move_line_ids_without_package:
                if move_line.product_id.type == 'consu' and move_line.product_id.purchase_ok and move_line.product_id.subcontractor_service:
                    consumable_line_ids.append(move_line)

            if consumable_line_ids and self.src_picking_id.transfer_purchase:
                for consumable_line_id in consumable_line_ids:
                    count = consumable_line_id.qty_done
                    for order_line in self.src_picking_id.transfer_purchase.order_line:
                        if order_line.x_delivery_order.id == self.src_picking_id.id and order_line.product_id.id == consumable_line_id.product_id.id:
                            if order_line.qty_received >= count:
                                order_line.qty_received -= count
                                count = 0
                            else:
                                count -= order_line.qty_received
                                order_line.qty_received = 0

        if self.batch_id and self.transfer_purchase.order_line:
            picking_po_lines = self.transfer_purchase.order_line.filtered(lambda p: p.x_delivery_order.id == self.id)
            print(picking_po_lines, 'PO LINES')
            if picking_po_lines:
                for line in picking_po_lines:
                    if line.qty_received == 0:
                        print(line, 'DELETE THIS')
                        line.unlink()

        # if self.x_logistics_team.team_type == 'subcontractor':
        #     po = self.env['purchase.order'].search([('partner_id', '=', self.x_logistics_team.team_owner.id),
        #                                             ('x_is_delivery_expense', '=', True),
        #                                             ('state', 'in', ['draft', 'sent'])])
        #     consumable_line_ids = []
        #     for move_line in self.move_line_ids_without_package:
        #         if move_line.product_id.type == 'consu' and move_line.product_id.purchase_ok and move_line.product_id.subcontractor_service:
        #             consumable_line_ids.append(move_line)
        #     print(consumable_line_ids, 'CONSU')
        #     if consumable_line_ids:
        #         if po:
        #             self.transfer_purchase = po
        #             # product = self.env['product.product'].search([('name', '=', 'Subcontractor Fees')])
        #             # print(product)
        #             for consumable_line_id in consumable_line_ids:
        #                 unit_price = 0
        #                 for seller_id in consumable_line_id.product_id.seller_ids:
        #                     if seller_id.name == self.x_logistics_team.team_owner:
        #                         unit_price = seller_id.price
        #
        #                 print(unit_price, 'unit_price')
        #                 po.order_line = [(0, 0, {'product_id': consumable_line_id.product_id.id,
        #                                          'name': self.name,
        #                                          'product_qty': consumable_line_id.qty_done,
        #                                          'date_planned': fields.Date.today(),
        #                                          'product_uom': consumable_line_id.product_uom_id.id,
        #                                          'price_unit': unit_price})]
        #         else:
        #             vals = {'partner_id': self.x_logistics_team.team_owner.id,
        #                     'x_is_delivery_expense': True,
        #                     'payment_term_id': self.env['account.payment.term'].search(
        #                         [('name', '=', 'Immediate Payment')]).id}
        #             purchase = self.env['purchase.order'].create(vals)
        #             self.transfer_purchase = purchase
        #             # product = self.env['product.product'].search([('name', '=', 'Subcontractor Fees')])
        #             # print(product)
        #             for consumable_line_id in consumable_line_ids:
        #                 unit_price = 0
        #                 for seller_id in consumable_line_id.product_id.seller_ids:
        #                     if seller_id.name == self.x_logistics_team.team_owner:
        #                         unit_price = seller_id.price
        #                 print(unit_price, 'unit_price')
        #                 purchase.order_line = [(0, 0, {'product_id': consumable_line_id.product_id.id,
        #                                                'name': self.name,
        #                                                'product_qty': consumable_line_id.qty_done,
        #                                                'date_planned': fields.Date.today(),
        #                                                'product_uom': consumable_line_id.product_uom_id.id,
        #                                                'product_uom': consumable_line_id.product_uom_id.id,
        #                                                'price_unit': unit_price})]

    def action_cancel_delivery_confirmation(self):
        self.x_is_delivered = False
        # if self.batch_id and self.x_logistics_team.team_type == 'subcontractor':
        #     for line in self.transfer_purchase.order_line:
        #
        #         if line.x_delivery_order.id == self.id:
        #             line.qty_received = 0

    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        self.x_slot.status = 'available'
        self.x_slot.delivery = None
        self.x_slot.note = ''
        self.x_slot.period = None
        self.x_slot.x_priority = '1'
        self.x_slot.delivery_items = False
        self.x_slot = False
        return res

    def action_view_returned_picking(self):
        self.ensure_one()
        picking_ids = self.return_picking_ids.ids
        return {
            'name': _('Returns'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'views': [
                (self.env.ref('stock.vpicktree').id, 'tree'),
                (self.env.ref('stock.view_picking_form').id, 'form')
            ],
            'domain': [('id', 'in', picking_ids)]
        }

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
            'domain': [('id', '=', self.id)],
        }

    def action_details_view(self):
        self.ensure_one()
        return {
            # 'name': _('Barcode'),
            'res_model': 'stock.picking',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [
                (self.env.ref('pabs_logistics_extra.pabs_logistics_extra_stock_picking_add_to_batch_details_form').id,
                 'form'),
            ],
            'type': 'ir.actions.act_window',
            # 'domain': [('id', '=', self.id)],
            'target': 'new',
            'flags': {'mode': 'readonly', 'no_create': True}
            # 'flags': {'mode': 'readonly'}
        }

    def action_add_to_batch(self, batch_id):
        if not self:
            raise UserError(_('Nothing to Add.'))
        else:
            for pick in self:
                pick.write({'batch_id': batch_id})
            return {
                'name': _('Add To Batch'),
                'res_model': 'stock.picking.batch',
                'res_id': batch_id,
                'view_mode': 'form',
                'view_type': 'form',
                'views': [(self.env.ref('stock_picking_batch.stock_picking_batch_form').id, 'form')],
                # 'views': [
                #     (self.env.ref('pabs_logistics_extra.pabs_logistics_extra_stock_picking_batch_add_views').id, 'form'),
                # ],
                'type': 'ir.actions.act_window',
                # 'target': 'main',
                # 'domain': [('id', '=', self.id)],
            }


    def _ticket_count(self):
        for batch in self:
            batch.x_ticket_count = self.env['helpdesk.ticket'].search_count([('x_dn_check', 'in', self.ids)]) or len(
                self.move_ids_without_package.mapped('sale_line_id.x_ticket_cancel').ids)


    def care_of_request(self):
        for pick in self:
            if not pick.x_approval_user:
                raise Warning('Please select a responsible')
            pick.x_care_of_state = 'request'
            activity = self.env['mail.activity'].sudo().create({
                'res_id': self.batch_id.id,
                'res_model_id': self.env['ir.model']._get('stock.picking.batch').id,
                'res_name': self.batch_id.name,
                #'activity_type_id': activity.id,
                'summary': 'Care Of Request',
                'user_id': pick.x_approval_user.id,
                'date_deadline': fields.Date.today(),
                'note': 'Care of request for %s - %s - Due: %s' %(pick.partner_id.name, pick.name, pick.x_total_amount),
            })
            self.batch_id.activity_ids = [(6, 0, activity.ids)]

    def care_of_approve(self):
        for pick in self:
            if pick.x_approval_user.id != self.env.user.id:
                raise Warning('You are not allowed to approve')
            pick.x_care_of_state = 'approve'
            self.batch_id.activity_ids.action_feedback(feedback="Request Approved")

    def care_of_refuse(self):
        for pick in self:
            if pick.x_approval_user.id != self.env.user.id:
                raise Warning('You are not allowed to refuse')
            pick.x_care_of_state = 'refuse'
            #self.batch_id.activity_ids.action_done()
            self.batch_id.activity_ids.action_feedback(feedback="Request Refused")
    def reschedule_confirmation_action(self):
        for pick in self:
            pick.x_reschedule_confirm = 'confirm'

    def urgency_action(self):
        for pick in self:
            if pick.x_urgent_request:
                pick.x_urgent_request = False
            else:
               pick.x_urgent_request = 'urgent'
