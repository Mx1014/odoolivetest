from ast import literal_eval
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
import json
import logging
import pytz
import uuid
from odoo import tools
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockMove(models.Model):
    _inherit = 'stock.move'

    x_tax_id = fields.Many2many('account.tax', string='Taxes', related='sale_line_id.tax_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    # x_price_subtotal = fields.Monetary(string='Subtotal', related='sale_line_id.price_subtotal')
    x_team_id = fields.Many2one('logistics.team', related='picking_id.x_logistics_team', store=True)
    x_business_line_id = fields.Many2one('business.line', related='picking_type_id.business_line', store=True)

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    x_team_id = fields.Many2one('logistics.team', related='picking_id.x_logistics_team', store=True)
    x_picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type', related='picking_id.picking_type_id', store=True)
    x_business_line_id = fields.Many2one('business.line', related='x_picking_type_id.business_line', store=True)


class SaleReport(models.Model):
    _name = "stock.move.line.report"
    _description = "Stock Move Analysis Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    # @api.model
    # def _get_done_states(self):
    #     return ['sale', 'done', 'paid']

    date = fields.Date('Date Done', readonly=True)
    product_id = fields.Many2one('product.product', 'Product Variant', readonly=True)
    qty_done = fields.Float('Qty', readonly=True)
    location_id = fields.Many2one('stock.location', 'From', readonly=True)
    location_dest_id = fields.Many2one('stock.location', 'To', readonly=True)
    x_team_id = fields.Many2one('logistics.team', 'Team', readonly=True)
    x_team_owner = fields.Many2one('res.partner', 'Team Owner', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    picking_id = fields.Many2one('stock.picking', 'Transfer', readonly=True)
    src_picking_id = fields.Many2one('stock.picking', 'Source Transfer', readonly=True)
    code = fields.Selection([('incoming', 'Receipt'), ('outgoing', 'Delivery'), ('internal', 'Internal Transfer'), ('mrp_operation', 'Manufacturing')], 'Type of Operation', readonly=True)
    batch_date = fields.Date(string='Batch Date', readonly=True)
    product_categ_id = fields.Char(string='Product Category', readonly=True)
    total_count = fields.Float('Qty total count')
    x_business_line_id = fields.Many2one('business.line', 'Business Line', readonly=True)
    x_picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type', readonly=True)

    def _compute_total_count(self):
        for rec in self:
            if rec.code == 'incoming':
                rec.total_count = rec.qty_done * (-1)
            else:
                rec.total_count = rec.qty_done

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            l.id as id,
            l.product_id as product_id,
            l.qty_done as qty_done,
            l.location_id as location_id,
            l.location_dest_id as location_dest_id,
            l.x_business_line_id as x_business_line_id,
            l.x_picking_type_id as x_picking_type_id,
            s.x_logistics_team_returns as x_team_id,
            l.picking_id as picking_id,
            s.partner_id as partner_id,
            s.src_picking_id as src_picking_id,
            s.code as code,
            s.date_done as date,
            t.team_owner as x_team_owner,
            pc.name as product_categ_id,
            CASE
                WHEN s.code = 'incoming' THEN (l.qty_done*(-1))
                ELSE l.qty_done
            END AS total_count
        """

        for field in fields.values():
            select_ += field

        from_ = """
                stock_move_line l
                      left join stock_picking s on (l.picking_id=s.id)
                      left join logistics_team t on (s.x_logistics_team_returns=t.id)
                      left join stock_picking_batch b on (s.batch_id=b.id)
                      left join product_product p on (l.product_id=p.id)
                      left join product_template pt on (p.product_tmpl_id=pt.id)
                      left join product_category pc on (pt.categ_id=pc.id)
                %s
        """ % from_clause

        groupby_ = """%s""" % (groupby)

        return '%s (SELECT %s FROM %s WHERE l.product_id IS NOT NULL)' % (with_, select_, from_)

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))