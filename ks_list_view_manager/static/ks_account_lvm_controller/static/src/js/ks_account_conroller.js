odoo.define('ks_account_lvm_controller.account_controller', function (require) {
    "use strict";

    var view_registry = require('web.view_registry');
    var ListView = require('web.ListView');
    var bill_data = view_registry.get('account_tree');
    var ks_list_controller = require('ks_list_view_manager.controller');
    var UploadBillMixin = require('account.upload.bill.mixin');
    var ImportViewMixin = require("base_import.import_buttons")

    if(bill_data) {
        //  make suitable with BillsListView
        var bill = bill_data.prototype.config.Controller.extend(_.extend({}, ks_list_controller.prototype,UploadBillMixin,ImportViewMixin, {

            buttons_template: 'BillsListView.buttons',
            events: _.extend({}, ks_list_controller.prototype.events, bill_data.prototype.config.Controller.prototype.events),
        }, {}));

        var BillsListView = ListView.extend({
            config: _.extend({}, ListView.prototype.config, {
                Controller: bill,
            }),
        });

        view_registry.add('account_tree', BillsListView);
    }

})