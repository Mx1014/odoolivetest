from ast import literal_eval
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
import json
import logging
import pytz
import uuid

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    x_is_delivery_expense = fields.Boolean(string="Is Delivery Expense", default=False)
    x_batch = fields.Many2one('stock.picking.batch', string='Batch')
    x_batch_ids = fields.Many2many('stock.picking.batch', string='Batch_ids')
    x_team_id = fields.Many2one('logistics.team', string='Team', compute='_compute_x_team_id', store=1)
    x_industry_id = fields.Many2one('res.partner.industry', string='Industry', related='partner_id.industry_id', store=1)
    x_batch_count = fields.Integer(string='Industry', compute='_compute_x_batch_count')

    def _compute_x_batch_count(self):
        for rec in self:
            rec.x_batch_count = len(rec.x_batch_ids)
    # test = fields.Integer(string='test', compute='_compute_test')
    #
    # def _compute_test(self):
    #     print('TEEEEEST CALLED')
    #     po_ids = self.env['purchase.order'].search([('x_is_delivery_expense', '!=', False)])
    #     for po_id in po_ids:
    #         if po_id.x_batch not in po_id.x_batch_ids:
    #             po_id.x_batch_ids += po_id.x_batch
    #         po_id._compute_x_team_id()
    #     self.test = 1

    @api.depends('x_batch_ids')
    def _compute_x_team_id(self):
        for rec in self:
            team_id = None
            if rec.x_batch_ids:
                team_id = rec.x_batch_ids[0].x_team
            rec.x_team_id = team_id

    def button_approve(self, force=False):

        if self.x_is_delivery_expense:
            self.write({'state': 'purchase', 'date_approve': fields.Datetime.now()})
            self.filtered(lambda p: p.company_id.po_lock == 'lock').write({'state': 'done'})
            return {}
        else:
            result = super(PurchaseOrder, self).button_approve(force=force)
            self._create_picking()
            return result

    def action_view_batch_form(self):
        # self.ensure_one()
        return {
            'name': _('Batch From P.O.'),
            'res_model': 'stock.picking.batch',
            # 'res_id': self.x_batch.id,
            'view_mode': 'tree, form',
            'views': [
                (self.env.ref('stock_picking_batch.stock_picking_batch_tree').id, 'tree'),
                (self.env.ref('stock_picking_batch.stock_picking_batch_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.x_batch_ids.ids)],
        }

    def monthly_batch_purchase_confirm(self):
        po_ids = self.env['purchase.order'].search([('x_is_delivery_expense', '=', True), ('order_line', '!=', False)])
        if po_ids:
            for po in po_ids:
                print(po, 'Confirmed')
                po.button_confirm()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_delivery_order = fields.Many2one('stock.picking', string="D.N.")
    x_delivery_date = fields.Datetime(related="x_delivery_order.date_done", store=True)
    x_delivery_batch = fields.Many2one('stock.picking.batch', related="x_delivery_order.batch_id", store=True)
    x_batch_team = fields.Many2one('logistics.team', related="x_delivery_order.x_logistics_team", store=True)
    x_stock_move_line_id = fields.Many2one('stock.move.line', string="Move Line")
    x_sale_id = fields.Many2one('sale.order', string="Sale Order", related='x_delivery_order.sale_id')
    x_delivery_customer_id = fields.Many2one('res.partner', string="Customer", related='x_delivery_order.partner_id')
    # x_qty_to_bill = fields.Float(compute="get_total_to_bill")
    #
    # def get_total_to_bill(self):
    #     for line in self:
    #         if line.product_id.purchase_method == 'purchase':
    #             line.x_qty_to_bill = line.product_qty - line.qty_invoiced
    #         else:
    #             line.x_qty_to_bill = line.qty_received - line.qty_invoiced
    #
    #         if float_compare(line.x_qty_to_bill, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
    #             line.x_qty_to_bill = 0.0

    def name_get(self):
        result = []
        for po in self:
            name = po.name
            dn = po.x_delivery_order.name
            if dn:
                name += ' (' + dn + ')'
            if po.price_subtotal:
                name += ': ' + formatLang(self.env, po.price_subtotal, currency_obj=po.currency_id)
            result.append((po.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []

        if name:
                domain = ['|', '|', '|',('name', operator, name), ('x_delivery_order', operator, name), ('x_delivery_batch', operator, name), ('order_id', operator, name)]
        emp_id = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(emp_id).name_get()


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    x_delivery_order = fields.Many2one('stock.picking', string="D.N.")
    x_batch_id = fields.Many2one('stock.picking.batch', string="Tripsheet")
    x_team_id = fields.Many2one('logistics.team', string='Team')

    def _select(self):
       select_str = super()._select()
       select_str += """
           , l.x_delivery_order as x_delivery_order
           , po.x_batch as x_batch_id
           , po.x_team_id as x_team_id
           """
       return select_str

    # def _from(self):
    #     from_str = super()._from()
    #     from_str += """
    #        left join stock_picking dn on dn.id = l.x_delivery_order
    #        """
    #     return from_str

    def _group_by(self):
       group_by_str = super()._group_by()
       group_by_str += ", l.x_delivery_order, po.x_batch, po.x_team_id"
       return group_by_str
