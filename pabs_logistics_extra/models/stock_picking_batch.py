from ast import literal_eval
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
import json
import logging
import pytz
import uuid

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    # picking_ids = fields.One2many(
    #     'stock.picking', 'batch_id', string='Transfers',
    #     domain="[('id', '=', False)]",
    #     help='List of transfers associated to this batch')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('delivery', 'Out For Delivery'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], default='draft',
        copy=False, tracking=True, required=True, readonly=True)
    picking_ids = fields.One2many(
        'stock.picking', 'batch_id', string='Transfers',
        domain="[('picking_type_id.business_line', '!=', False), ('picking_type_id.business_line', '=', x_business_line), ('state', 'in', ['assigned', 'waiting', 'confirmed', 'done']), ('batch_id', '=', False), ('code', 'in', ['incoming', 'outgoing'])]",
        help='List of transfers associated to this batch')
    x_business_line = fields.Many2one('business.line', string="Business Line")
    x_team = fields.Many2one('logistics.team', string="Team", domain="[('business_line', '=', x_business_line)]")
    x_vendor = fields.Many2one('res.partner', string="Team Vendor", related='x_team.team_owner', store=1)
    x_team_capacity = fields.Integer(string="Team Capacity")
    x_delivery_qty = fields.Integer(string="Orders Qty")
    x_remaining_qty = fields.Integer(string="Remaining Capacity")
    x_delivery_date = fields.Date("Delivery Date", default=datetime.today())
    x_zone = fields.Many2many('res.zone', string="Zone")
    x_products = fields.Many2many('stock.move', string='Products', compute='_compute_x_products')
    x_products_detailed = fields.Many2many('stock.move.line', string='Products', compute='_compute_x_products_detailed')
    x_batch_po = fields.Many2one('purchase.order', string="Batch PO", ondelete='cascade', copy=False)
    x_total_demand = fields.Integer(string="Total Demand", compute='_compute_x_total_demand')
    x_is_overloaded = fields.Boolean(string="Overloaded")
    x_ticket_count = fields.Integer(string="Ticket", compute="_ticket_count")
    x_stage = fields.Selection([
        ('to_submit', 'To Submit'),
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('bill', 'Billed'),
        ('pay', 'Paid')], default='to_submit',
        copy=False, tracking=True, readonly=True)
    # test = fields.Integer(string='test', compute='_compute_test')
    #
    # @api.depends('picking_ids.state')
    # def _compute_test(self):
    #     for rec in self:
    #         if rec.state == 'draft' and rec.picking_ids:
    #             if 'done' in rec.picking_ids.mapped('state') and 'cancel' not in rec.picking_ids.mapped('state'):
    #                 rec.confirm_picking()
    #                 # found = False
    #                 # for pick in rec.picking_ids:
    #                 #     if pick.state != 'done':
    #                 #         found = True
    #                 # if not found:
    #                 #     rec.state = 'delivery'
    #         if rec.state == 'in_progress' and rec.picking_ids:
    #             found = False
    #             for pick in rec.picking_ids:
    #                 if pick.state != 'done':
    #                     found = True
    #             if not found:
    #                 rec.state = 'delivery'
    #     # x = self.env['stock.picking.batch'].search([('state', '=', 'delivery')])
    #     # if x:
    #     #     for rec in x:
    #     #         rec.state = 'in_progress'
    #         rec.test = 1

    def stage_submitted(self):
        for batch in self:
            batch.x_stage = 'submitted'

    def stage_reviewed(self):
        for batch in self:
            batch.x_stage = 'reviewed'

    def stage_billed(self):
        for batch in self:
            batch.x_stage = 'bill'

    def stage_paid(self):
        for batch in self:
            batch.x_stage = 'pay'

    @api.onchange('picking_ids')
    def _compute_x_total_demand(self):
        for rec in self:
            total_demand = 0
            for line in rec.x_products:
                total_demand += line.product_uom_qty
            if rec.state == 'draft' and rec.picking_ids:
                if 'done' in rec.picking_ids.mapped('state') and 'cancel' not in rec.picking_ids.mapped('state'):
                    rec.confirm_picking()
                    found = False
                    for pick in rec.picking_ids:
                        if pick.state != 'done':
                            found = True
                    if not found:
                        rec.state = 'delivery'
            if rec.state == 'in_progress' and rec.picking_ids:
                found = False
                for pick in rec.picking_ids:
                    print(pick.state, 'pick.state', found)
                    if pick.state != 'done':
                        found = True
                print('pick.state', found)
                if not found:
                    rec.state = 'delivery'
            rec.x_total_demand = total_demand

    @api.onchange('x_zone', 'x_business_line')
    def onchange_x_zone(self):
        res = {}
        if self.x_zone:
            res['domain'] = {
                'picking_ids': [('x_zone', 'in', self.x_zone.ids), ('picking_type_id.business_line', '!=', False),
                                ('picking_type_id.business_line', '=', self.x_business_line.id),
                                ('state', 'in', ['assigned', 'waiting', 'confirmed', 'done']), ('batch_id', '=', False),
                                ('code', 'in', ['incoming', 'outgoing'])]}
            return res
        else:
            res['domain'] = {
                'picking_ids': [('picking_type_id.business_line', '!=', False),
                                ('picking_type_id.business_line', '=', self.x_business_line.id),
                                ('state', 'in', ['assigned', 'waiting', 'confirmed', 'done']),
                                ('batch_id', '=', False), ('code', 'in', ['incoming', 'outgoing'])]}
            return res

    @api.onchange('x_business_line')
    def onchange_business_line(self):
        self.x_team = None
        self.picking_ids = [(5, 0, 0)]
        self.x_delivery_qty = 0
        self.x_remaining_qty = 0

    @api.onchange('x_team')
    def onchange_x_team(self):
        if self.x_team:
            if self.x_delivery_date:
                delivery_day = self.x_delivery_date.strftime("%A").lower()
                for day in self.x_team.attendance_ids:
                    if day.dayofweek == delivery_day:
                        self.x_team_capacity = day.capacity_per_day
        else:
            self.x_team_capacity = 0

    @api.onchange('x_delivery_date')
    def onchange_delivery_date(self):
        if self.x_team and self.x_delivery_date:
            delivery_day = self.x_delivery_date.strftime("%A").lower()
            for day in self.x_team.attendance_ids:
                if day.dayofweek == delivery_day:
                    self.x_team_capacity = day.capacity_per_day
        else:
            self.x_team_capacity = 0

    @api.onchange('x_team_capacity')
    def onchange_x_team_capacity(self):
        self.x_remaining_qty = self.x_team_capacity - self.x_delivery_qty

    @api.onchange('picking_ids')
    def x_onchange_picking_ids(self):
        count = 0
        if self.picking_ids:
            for pick in self.picking_ids:
                count += 1
            self.x_delivery_qty = count
        self.x_remaining_qty = self.x_team_capacity - self.x_delivery_qty

    def _compute_x_products(self):
        for rec in self:
            ids = []
            for product in rec.picking_ids.move_ids_without_package:
                ids.append(product.id)
            rec.x_products = ids

    def _compute_x_products_detailed(self):
        for rec in self:
            ids = []
            for product in rec.picking_ids.move_line_ids_without_package:
                ids.append(product.id)
            rec.x_products_detailed = ids

    def action_stock_picking_batch_revert_to_draft(self):
        self.state = 'draft'

    def action_stock_picking_batch_confirm_done(self):
        return {
            'name': _('Confirm'),
            'res_model': 'stock.picking.batch.confirm',
            'view_mode': 'form',
            'views': [
                (self.env.ref('pabs_logistics_extra.stock_picking_batch_confirm_done').id, 'form'),
            ],
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_stock_picking_batch_out_for_delivery(self):
        if not self.picking_ids:
            raise Warning(_("Please add Some orders to deliver."))
        elif self.picking_ids:
            for picking in self.picking_ids:
                if picking.state != 'done':
                    raise Warning(_("Some orders are not done."))
            self.state = 'delivery'
            self.x_batch_po.button_confirm()

    def action_po_view(self):
        self.ensure_one()
        return {
            'name': _('P.O. From Batch Picking'),
            'res_model': 'purchase.order',
            'res_id': self.x_batch_po.id,
            'view_mode': 'form',
            'views': [
                (self.env.ref('purchase.purchase_order_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
        }

    def cancel_batch_picking(self):
        if self.picking_ids:
            for pick in self.picking_ids:
                if pick.state != 'cancel':
                    raise UserError(_(
                        'To be able to cancel, you have either to remove all deliveries or to individually cancel each.'))
        self.state = 'cancel'

    def confirm_picking(self):
        self._check_company()
        pickings_todo = self.env['stock.picking'].search([('id', 'in', self.mapped('picking_ids').ids), ('code', '!=', 'incoming'), ('state', 'not in', ['done', 'cancel'])])
        self.mapped('picking_ids')
        # self.write({'state': 'in_progress'})
        self.state = 'in_progress'
        if (not pickings_todo and not self.picking_ids) or pickings_todo:
            return pickings_todo.action_assign()

    # def confirm_picking(self):
    #     res = super(StockPickingBatch, self).confirm_picking()
    #     # print(vals_list)
    #
    #     if not self.x_batch_po and self.x_vendor:
    #         vals = {'partner_id': self.x_vendor.id,
    #                 'x_is_delivery_expense': True,
    #                 'payment_term_id': self.env['account.payment.term'].search([('name', '=', 'Immediate Payment')]).id}
    #         purchase = self.env['purchase.order'].create(vals)
    #         self.x_batch_po = purchase
    #
    #     return res

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(StockPickingBatch, self).create(vals_list)
    #     print(vals_list)
    #     if res.x_vendor:
    #         vals = {'partner_id': res.x_vendor.id,
    #                 'x_is_delivery_expense': True,
    #                 'x_batch': res.id,
    #                 'payment_term_id': self.env['account.payment.term'].search([('name', '=', 'Immediate Payment')]).id}
    #         purchase = self.env['purchase.order'].create(vals)
    #         res.x_batch_po = purchase
    #
    #     return res

    # def write(self, vals):
    #     print(vals, 'vals')
    #     if 'x_team' in vals:
    #         team = self.env['logistics.team'].browse(vals['x_team'])
    #         if self.x_batch_po:
    #             purchase = self.env['purchase.order'].search([('id', '=', self.x_batch_po.id)])
    #             self.x_batch_po = False
    #             if purchase:
    #                 purchase.x_batch = False
    #                 purchase.unlink()
    #         if team.team_type == 'subcontractor' and team.team_owner:
    #             values = {'partner_id': team.team_owner.id,
    #                       'x_is_delivery_expense': True,
    #                       'x_batch': self.id,
    #                       'payment_term_id': self.env['account.payment.term'].search(
    #                           [('name', '=', 'Immediate Payment')]).id}
    #             purchase = self.env['purchase.order'].create(values)
    #             self.x_batch_po = purchase
    #     res = super(StockPickingBatch, self).write(vals)
    #     return res

    # def unlink(self):
    #     if self.x_batch_po:
    #         if self.x_batch_po.state not in ['done', 'purchase']:
    #             self.x_batch_po.button_cancel()
    #         self.x_batch_po.unlink()
    #     res = super(StockPickingBatch, self).unlink()
    #     return res

    def action_view_business_line_stock_picking_batch(self):
        # self.ensure_one()
        my_user = self.env.user
        business_line_ids = my_user.x_business_line_ids.ids
        show = []
        for rec in self.env['stock.picking.batch'].search([]):
            if rec.x_business_line.id in business_line_ids or not rec.x_business_line:
                show.append(rec.id)
        return {
            'name': _('Batch Transfers'),
            'res_model': 'stock.picking.batch',
            # 'res_id': self.x_batch_po.id,
            'view_type': 'form',
            'view_mode': 'tree,kanban,form,pivot,graph',
            # 'target': 'main',
            # 'views': [
            #     (self.env.ref('stock_picking_batch.stock_picking_batch_tree').id, 'tree'),
            # ],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', show)],
        }

    def action_stock_picking_batch_add(self):
        batch_id = self._context.get('batch_id')
        delivery_date = self._context.get('delivery_date')
        batch = self.env['stock.picking.batch'].browse(batch_id)
        return {
            'name': _('Transfers To Add'),
            'res_model': 'stock.picking',
            # 'res_id': self.x_batch_po.id,
            # 'view_type': 'tree',
            'view_mode': 'tree',
            # 'target': 'current',
            'views': [
                (self.env.ref('pabs_logistics_extra.view_stock_picking_add_to_batch_tree').id, 'tree'),
                # (self.env.ref('stock.view_picking_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'context': {'show_add_button': True, 'search_default_before_today': 1},
            'domain': [('picking_type_id', 'in', batch.x_business_line.operations.ids), ('batch_id', '=', False), ('state', 'in', ['waiting', 'confirmed', 'assigned'])],
        }

    def action_view_tickets(self):
        vals = self.env['helpdesk.ticket'].search([('x_dn_check', 'in', self.picking_ids.ids)]).ids
        return {
            'name': _('Tickets'),
            'res_model': 'helpdesk.ticket',
            'view_mode': 'kanban,form',
            'views': [
                (self.env.ref('helpdesk.helpdesk_ticket_view_kanban').id, 'kanban'),
                (self.env.ref('helpdesk.helpdesk_ticket_view_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', vals)],
        }

    def _ticket_count(self):
        for batch in self:
            batch.x_ticket_count = self.env['helpdesk.ticket'].search_count([('x_dn_check', 'in', self.picking_ids.ids)])
