odoo.define('pabs_online_booking.signature_form_custom', function (require) {
'use strict';

var core = require('web.core');
var publicWidget = require('web.public.widget');
var NameAndSignature = require('web.name_and_signature').NameAndSignature;
var PortalSignature = require('portal.signature_form').SignatureForm;

var qweb = core.qweb;

var _t = core._t;

PortalSignature = PortalSignature.include({

    _onClickSignSubmit: function (ev) {
        var self = this;
        ev.preventDefault();

        if (!this.nameAndSignature.validateSignature()) {
            return;
        }

        var name = this.nameAndSignature.getName();
        var signature = this.nameAndSignature.getSignatureImage()[1];

        return this._rpc({
            route: this.callUrl,
            params: _.extend(this.rpcParams, {
                'name': name,
                'signature': signature,
            }),
        }).then(function (data) {
            console.log(data)
            if (data.error) {
                self.$('.o_portal_sign_error_msg').remove();
                self.$controls.prepend(qweb.render('portal.portal_signature_error', {widget: data}));
            } else if (data.success) {
                var $success = qweb.render('pabs_online_booking.calender_form_date', {widget: data});
                self.$el.empty().append($success);
            }
            if (data.force_refresh) {
                console.log(data.redirect_url)
                if (data.redirect_url) {
                   window.location = data.redirect_url;
                } else {
                    window.location.reload();
                }
                // no resolve if we reload the page
                return new Promise(function () { });
            }
        });
    },

});
});
