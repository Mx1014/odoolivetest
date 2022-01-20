# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
from babel.dates import format_datetime, format_date

from werkzeug.urls import url_encode

import binascii

from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request, route
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import get_records_pager
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.addons.sale_stock.controllers.portal import SaleStockPortal
from odoo.osv import expression
from odoo import exceptions
import werkzeug
from werkzeug import url_encode


time = {'Morning': 'morning', 'Afternoon': 'evening', 'Any Time': ''}
access_tok = ''


class PabsOnlineBooking(CustomerPortal):


    @http.route(['/my/orders/<int:order_id>'], type='http', auth="public", website=True)
    def portal_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            access_tok = access_token
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type,
                                     report_ref='pabs_sale_quotation.sale_quotation', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        # Log only once a day
        if order_sudo and request.session.get(
                'view_quote_%s' % order_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_quote_%s' % order_sudo.id] = now
            body = _('Quotation viewed by customer %s') % order_sudo.partner_id.name
            _message_post_helper('sale.order', order_sudo.id, body, token=order_sudo.access_token,
                                 message_type='notification', subtype="mail.mt_note")

        values = {
            'sale_order': order_sudo,
            'message': message,
            'token': access_token,
            'return_url': '/shop/payment/validate',
            'bootstrap_formatting': True,
            'partner_id': order_sudo.partner_id.id,
            'report_type': 'html',
            'action': order_sudo._get_portal_return_action(),
        }
        if order_sudo.company_id:
            values['res_company'] = order_sudo.company_id

        if order_sudo.has_to_be_paid():
            domain = expression.AND([
                ['&', ('state', 'in', ['enabled', 'test']), ('company_id', '=', order_sudo.company_id.id)],
                ['|', ('country_ids', '=', False), ('country_ids', 'in', [order_sudo.partner_id.country_id.id])]
            ])
            acquirers = request.env['payment.acquirer'].sudo().search(domain)

            values['acquirers'] = acquirers.filtered(
                lambda acq: (acq.payment_flow == 'form' and acq.view_template_id) or
                            (acq.payment_flow == 's2s' and acq.registration_view_template_id))
            values['pms'] = request.env['payment.token'].search([('partner_id', '=', order_sudo.partner_id.id)])
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(order_sudo.amount_total,
                                                                         order_sudo.currency_id,
                                                                         order_sudo.partner_id.country_id.id)

        if order_sudo.state in ('draft', 'sent', 'cancel'):
            history = request.session.get('my_quotations_history', [])
        else:
            history = request.session.get('my_orders_history', [])
        values.update(get_records_pager(history, order_sudo))


        # request.session['timezone'] = 'UTC'
        # Slots = request.env['plan.calendar'].sudo()._get_appointment_slots(request.session['timezone'], None)
        #
        # values['slots'] = Slots

        return request.render('sale.sale_order_portal_template', values)


    @http.route(['/my/orders/<int:order_id>/accept'], type='json', auth="public", website=True)
    def portal_quote_accept(self, order_id, access_token=None, name=None, signature=None):
        # get from query string if not on json param
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}

        if not order_sudo.has_to_be_signed():
            return {'error': _('The order is not in a state requiring customer signature.')}
        if not signature:
            return {'error': _('Signature is missing.')}

        try:
            order_sudo.write({
                'signed_by': name,
                'signed_on': fields.Datetime.now(),
                'signature': signature,
            })
        except (TypeError, binascii.Error) as e:
            return {'error': _('Invalid signature data.')}

        if not order_sudo.has_to_be_paid():
            order_sudo.action_confirm()
            order_sudo._send_order_confirmation_mail()

        pdf = request.env.ref('sale.action_report_saleorder').sudo().render_qweb_pdf([order_sudo.id])[0]

        _message_post_helper(
            'sale.order', order_sudo.id, _('Order signed by %s') % (name,),
            attachments=[('%s.pdf' % order_sudo.name, pdf)],
            **({'token': access_token} if access_token else {}))

        query_string = '&message=sign_ok'
        if order_sudo.has_to_be_paid(True):
            query_string += '#allow_payment=yes'

        url = '/website/calendar/%s/pickingdate/normal' % (order_sudo.id)

        return {
            'force_refresh': True,
            'redirect_url': url, #order_sudo.get_portal_url(suffix='/%s' % url, query_string=query_string),
        }

    @http.route(['/website/calendar/<int:order_id>/pickingdate/<string:type>'], type='http', auth="public", website=True)
    def calendar_picking_date_form(self, order_id, type=None, **kwargs):
        # try:
        #     order_sudo = self._document_check_access('sale.order', order_id, access_token=None)
        #
        # except (AccessError, MissingError):
        #     print('error******************')
        #     return {'error': _('Invalid order.')}

        order_sudo = request.env['sale.order'].sudo().search([('id', '=', order_id)])
        delivery = request.env['stock.picking'].sudo().search([('id', 'in', order_sudo.picking_ids.ids), ('state', 'not in', ['done', 'cancel']), ('x_slot', '=', False)], limit=1)
        request.session['timezone'] = 'UTC'
        Slots = request.env['plan.calendar'].sudo()._get_appointment_slots(request.session['timezone'], delivery.x_business_line, type, None)
        return request.render("pabs_online_booking.calender_form_date", {
            'slots': Slots,
            'order': order_sudo,
            'deliveries': delivery,

        })

    @http.route(['/my/orders/<int:order_id>/successful'], type='http', auth="public", website=True)
    def successful_picking(self, order_id, slot_id, delivery_id, prefered_time, date_time, report_type=None, access_token=None, message=False, download=False, **kw):
        # try:
        #     order_sudo = self._document_check_access('sale.order', order_id, access_token=str(uuid.uuid4()))
        # except (AccessError, MissingError):
        #     return request.redirect('/my')

        order_sudo = request.env['sale.order'].sudo().search([('id', '=', order_id)])
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type,
                                     report_ref='pabs_sale_quotation.sale_quotation', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        now = fields.Date.today()

        # Log only once a day
        if order_sudo and request.session.get(
                'view_quote_%s' % order_sudo.id) != now and request.env.user.share and access_token:
            request.session['view_quote_%s' % order_sudo.id] = now
            body = _('Quotation viewed by customer %s') % order_sudo.partner_id.name
            _message_post_helper('sale.order', order_sudo.id, body, token=order_sudo.access_token,
                                 message_type='notification', subtype="mail.mt_note")

        values = {
            'sale_order': order_sudo,
            'message': message,
            'token': access_token,
            'return_url': '/shop/payment/validate',
            'bootstrap_formatting': True,
            'partner_id': order_sudo.partner_id.id,
            'report_type': 'html',
            'action': order_sudo._get_portal_return_action(),
        }
        if order_sudo.company_id:
            values['res_company'] = order_sudo.company_id

        if order_sudo.has_to_be_paid():
            domain = expression.AND([
                ['&', ('state', 'in', ['enabled', 'test']), ('company_id', '=', order_sudo.company_id.id)],
                ['|', ('country_ids', '=', False), ('country_ids', 'in', [order_sudo.partner_id.country_id.id])]
            ])
            acquirers = request.env['payment.acquirer'].sudo().search(domain)

            values['acquirers'] = acquirers.filtered(
                lambda acq: (acq.payment_flow == 'form' and acq.view_template_id) or
                            (acq.payment_flow == 's2s' and acq.registration_view_template_id))
            values['pms'] = request.env['payment.token'].search([('partner_id', '=', order_sudo.partner_id.id)])
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(order_sudo.amount_total,
                                                                         order_sudo.currency_id,
                                                                         order_sudo.partner_id.country_id.id)

        if order_sudo.state in ('draft', 'sent', 'cancel'):
            history = request.session.get('my_quotations_history', [])
        else:
            history = request.session.get('my_orders_history', [])
        values.update(get_records_pager(history, order_sudo))

        #slot = request.env['plan.calendar'].sudo().search([('start_datetime', '>=', datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')), ('status', '=', 'available')], limit=1)
        slot = request.env['plan.calendar'].sudo().search([('id', '=', slot_id)], limit=1)
        picking = request.env['stock.picking'].sudo().search([('id', '=', delivery_id)], limit=1)
        slot.delivery = picking.id
        # picking.x_slot = slot.id
        picking.scheduled_date = slot.start_datetime
        picking.x_slot.status = 'booked'
        picking.period = time[prefered_time]
        #slot.x_delivery_temp = picking.id

        # slot.action_save_plan_calendar_transfer()vals = ['Morning', 'Afternoon', 'Any Time']

        if request.env['res.users'].sudo().search([('id', '=', request.env.user.id)]):
            url = "%s/web#active_id=%s&model=%s&view_type=form&cids=1&menu_id=204" % (http.request.httprequest.url_root, order_sudo.id, 'delivery.reminder')
            #return request.redirect(url)
            return http.redirect_with_hash(url)


        if request.env['stock.picking'].sudo().search([('id', 'in', order_sudo.picking_ids.ids), ('state','not in', ['done', 'cancel']), ('x_slot','=', False)]):
            return self.calendar_picking_date_form(order_sudo.id)
        else:
            values['display_date'] = True
            return request.render('sale.sale_order_portal_template', values)



class SaleStockPortals(SaleStockPortal):

    @route(['/my/picking/pdf/<int:picking_id>'], type='http', auth="public", website=True)
    def portal_my_picking_report(self, picking_id, access_token=None, **kw):
        """ Print delivery slip for customer, using either access rights or access token
        to be sure customer has access """
        try:
            picking_sudo = self._stock_picking_check_access(picking_id, access_token=access_token)
        except exceptions.AccessError:
            return request.redirect('/my')

        # print report as sudo, since it require access to product, taxes, payment term etc.. and portal does not have those access rights.
        pdf = request.env.ref('pabs_delivery_report.action_report_delivery_note_pabs_delivery_report').sudo().render_qweb_pdf([picking_sudo.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

