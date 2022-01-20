from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # def action_view_invoice(self):
    #    res = super(PurchaseOrder, self).action_view_invoice()
    #    res['context']['default_x_bill_origin'] = self.name
    #    return res

