# -*- coding: utf-8 -*-


from odoo import http
from odoo.http import request
import werkzeug
from werkzeug import url_encode
from odoo import _, SUPERUSER_ID
from odoo.tools import config


class Login(http.Controller):

    @http.route('/report/pdf/sale_coupon.report_coupon_i18n/', type='http', auth='none', methods=['GET'], csrf=False)
    def allow_twillo_access_pdf(self, value):
        uid = request.session.authenticate(request.db, 'admin', '123')
        urltest = '/report/pdf/sale_coupon.report_coupon_i18n/%s' % value
        return werkzeug.utils.redirect(urltest)
