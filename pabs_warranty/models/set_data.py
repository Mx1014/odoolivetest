import dateutil
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from datetime import timedelta
from datetime import datetime


class Picking(models.Model):
    _inherit = 'stock.picking'

    def action_done(self):
        res = super(Picking, self).action_done()
        self.set_warranty_products()
        self.change_warranty_deliver_qty()
        return res

    def change_warranty_deliver_qty(self):
        for rec in self:
            for qty in rec.sale_id.order_line:
                if not qty.related_allow_extended:
                    if qty.related_order_line_id:
                        product_qty = qty.related_order_line_id.qty_delivered
                        if qty.product_uom_qty >= product_qty:
                            qty.qty_delivered = product_qty
                        elif qty.product_uom_qty < product_qty:
                            qty.qty_delivered = qty.product_uom_qty

    def set_warranty_products(self):
        res = {}
        for pick in self:
            if pick.code == 'outgoing':
                if pick.move_ids_without_package:
                    for rec in pick.move_ids_without_package:
                        for X in range(int(rec.quantity_done)):
                            if rec.product_id.allow_warranty:
                                ids = []
                                warranty_period = int(rec.product_id.warranty_time.period_countable)
                                warranty_end_date = fields.Date.today() + relativedelta(
                                    months=warranty_period)
                                ids.append((0, 0, {'product_id': rec.product_id.id,
                                                   'customer_name': rec.sale_line_id.order_id.partner_id.id,
                                                   'scheduled_date': fields.Date.today(),
                                                   'x_order_line': rec.sale_line_id.id,
                                                   'date_done': warranty_end_date,
                                                   'delivery_note': pick.id,
                                                   }))
                                pick.sale_id.warranty_line = ids
                        for record in rec.sale_line_id.order_id.order_line:
                            if record.related_order_line_id == rec.sale_line_id and record.product_id.is_extended:
                                extended_warranty_qty = record.product_uom_qty
                                period_countable = record.product_id.extended_time.period_countable
                                for warranty in rec.sale_line_id.order_id.warranty_line:
                                    if warranty.x_order_line == rec.sale_line_id and extended_warranty_qty != 0:
                                        warranty.extended_end_date = warranty.date_done + relativedelta(
                                            months=period_countable)
                                        extended_warranty_qty -= 1
