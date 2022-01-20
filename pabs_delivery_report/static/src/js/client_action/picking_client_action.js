odoo.define('pabs_delivery_report.picking_client_action_extend', function (require) {
'use strict';

var core = require('web.core');
var ClientAction = require('stock_barcode.ClientAction');
var ViewsWidget = require('stock_barcode.ViewsWidget');

var _t = core._t;

var PickingClientAction = require('stock_barcode.picking_client_action');

PickingClientAction = PickingClientAction.include({
    _validate: function () {
        var self = this;
        this.mutex.exec(function () {
            return self._save().then(function () {
                return self._rpc({
                    'model': self.actionParams.model,
                    'method': 'button_validate',
                    'args': [[self.actionParams.pickingId]],
                }).then(function (res) {
                    var def = Promise.resolve();
                    console.log(res)
                    var successCallback = function(){
                        self.do_notify(_t("Success"), _t('The transfer has been validated'));
                        self.trigger_up('exit');
                    };
                    var exitCallback = function (infos) {
                        if ((infos === undefined || !infos.special) && this.dialog.$modal.is(':visible')) {
                            successCallback();
                        }
                        core.bus.on('barcode_scanned', self, self._onBarcodeScannedHandler);
                    };
                    //override is here
                    if (_.isObject(res)) {
                        if (res.type != 'ir.actions.report'){
                        var options = {
                            on_close: exitCallback,
                        };
                        return def.then(function () {
                            core.bus.off('barcode_scanned', self, self._onBarcodeScannedHandler);
                            return self.do_action(res, options);
                        });
                        } else {return def.then(function () {
                            core.bus.off('barcode_scanned', self, self._onBarcodeScannedHandler);
                            return self.do_action(res).then(successCallback);
                        });}
                    } else {
                        return def.then(successCallback);
                    }
                });
            });
        });
    },


});

});
