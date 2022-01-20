odoo.define('pabs_invoicing.payment', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var core = require('web.core');
var field_registry = require('web.field_registry');
var field_utils = require('web.field_utils');
var rpc = require('web.rpc')
var AccountPayment = require('account.payment').ShowPaymentLineWidget

console.log('AccountPayment', AccountPayment)
//console.log('AccountPayment', AccountPayment.)

var QWeb = core.qweb;


AccountPayment.include({

//    _onOutstandingCreditAssign: function (event) {
//        event.stopPropagation();
//        event.preventDefault();
//        var self = this;
//        var id = $(event.target).data('id') || false;
//        this._rpc({
//                model: 'account.move',
//                method: 'js_assign_outstanding_line',
//                args: [JSON.parse(this.value).move_id, id],
//            }).then(function () {
//                self.trigger_up('reload');
//            });
//    },

     _onOutstandingCreditAssign: function (event) {
        event.preventDefault();
        var self = this;
        var id = $(event.target).data('id') || false;
        console.log(id)
        self.do_action({
        name: "Payment Link",
        type: 'ir.actions.act_window',
        res_model: 'link.specific.payment',
        view_mode: 'form',
        view_type: 'form',
        views: [[false, 'form']],
        context: {'default_name': id, 'default_move_id': JSON.parse(this.value).move_id},
        target: 'new',
     });

     },

    /**
     * @private
     * @override
     * @param {MouseEvent} event
     */

});

});
