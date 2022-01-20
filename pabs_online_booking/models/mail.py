# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class MailMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        res = super(MailMessage, self).action_send_mail()
        if self._context.get('active_model') == 'sale.order':
            so = self.env['sale.order'].search([('id', '=', self._context.get('active_id'))])
            if so.state == 'draft':
                so.state = 'sent'
        return res