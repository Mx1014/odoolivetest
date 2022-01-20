# Copyright 2018 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    product_brand_id = fields.Many2one(
        comodel_name='product.brand',
        string='Brand',
    )

    # pylint:disable=dangerous-default-value
    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['product_brand_id'] = ", t.product_brand_id as product_brand_id"
        groupby += ', t.product_brand_id'
        return super(SaleReport, self)._query(
            with_clause, fields, groupby, from_clause
        )


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    product_brand_id = fields.Many2one(
        comodel_name='product.brand',
        string='Brand',
    )

    def _select(self):
       select_str = super()._select()
       select_str += """
           , t.product_brand_id as product_brand_id
           """
       return select_str

    def _sub_select(self):
       select_str = super()._sub_select()
       select_str += """
           , t.product_brand_id
           """
       return select_str

    def _group_by(self):
       group_by_str = super()._group_by()
       group_by_str += ", t.product_brand_id"
       return group_by_str


class StockReport(models.Model):
    _inherit = "stock.report"

    product_brand_id = fields.Many2one(
        comodel_name='product.brand',
        string='Brand',
    )

    def _select(self):
        select_str = super()._select()
        select_str += """
              , t.product_brand_id as product_brand_id
              """
        return select_str

    def _sub_select(self):
        select_str = super()._sub_select()
        select_str += """
              , t.product_brand_id
              """
        return select_str

    def _group_by(self):
        group_by_str = super()._group_by()
        group_by_str += ", t.product_brand_id"
        return group_by_str
