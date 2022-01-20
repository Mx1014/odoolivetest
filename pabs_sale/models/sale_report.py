from odoo import fields, models, api, _



class SaleReport(models.Model):
    _inherit = 'sale.report'

    sale_order_type = fields.Selection(string='Sale Order Type', selection=[('cash_memo', 'Cash Memo'),
                                                                            ('credit_sale', 'Credit Sale'),
                                                                            ('paid_on_delivery', 'Paid on Delivery'),
                                                                            ('advance_payment', 'Cash Invoice'),
                                                                            ('service', 'Service')], readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['sale_order_type'] = ", s.sale_order_type as sale_order_type"
        groupby += ', s.sale_order_type'
        return super(SaleReport, self)._query(
            with_clause, fields, groupby, from_clause
        )