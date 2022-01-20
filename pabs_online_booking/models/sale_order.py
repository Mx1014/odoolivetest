# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_show_qrcode(self):
        self.ensure_one()
        return {
            'name': _('QRCODE'),
            'res_model': 'action.portal',
            'view_mode': 'form',
            'views': [
                (self.env.ref('pabs_online_booking.view_action_portal_qrcode').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'target': 'new',

        }


class ActionsPortal(models.TransientModel):
    _name = "action.portal"
    _description = "Action For Sales Portal"

    def get_url(self):
        ss = self.env['sale.order'].search([('id', '=', self._context.get('active_id'))]).get_portal_url()
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        if qrcode and base64:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(base_url+ss)
            qr.make(fit=True)

            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
        return qr_image

    url = fields.Binary(string="Url", default=get_url)

    def barcode_scanned(self):
        so = self.env['sale.order'].search([('id', '=', self._context.get('active_id'))])
        if so.state == 'draft':
            so.state = 'sent'


