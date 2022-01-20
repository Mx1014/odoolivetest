from odoo import fields, models, api, _
from twilio.rest import Client



class WhatsappAPI(models.Model):
    _name = 'whatsapp.api'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'WhatsApp Integration'


    def send_media(self, body, attachment, ids, phone):
        account_sid = 'AC7a0f0d1cff035856fb72691c129df7f2'
        auth_token = 'cd04c2fadcfe43fb5adddfb9d2fb0417'
        client = Client(account_sid, auth_token)

        if body:
            message = client.messages.create(
                from_='whatsapp:+14155238886',
                body='%s' %(body),
                to='whatsapp:+97332340110'
            )

        if attachment:
            for id in ids:
                request = 'http://193.188.118.45:8069/report/pdf/sale_coupon.report_coupon_i18n/?value=%s' % id
                client.messages.create(
                    media_url=[request],
                    from_='whatsapp:+14155238886',
                    to='whatsapp:%s' %phone.replace(" ", "")

                )