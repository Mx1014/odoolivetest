from odoo import fields, api, models, http
from odoo.http import request, route


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def reserve_slots(self):
        self.ensure_one()
        url = '%swebsite/calendar/%s/pickingdate/reserve' % (http.request.httprequest.url_root, self.sale_id.id)
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': url,
        }

    def test(self):
        self.ensure_one()
        url = '%swebsite/calendar/%s/pickingdate/normal' % (http.request.httprequest.url_root, self.sale_id.id)
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': url,
        }