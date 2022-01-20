odoo.define('pabs_logistics_extra.StockOrderpointListModel', function (require) {
"use strict";

var core = require('web.core');
var ListModel = require('web.ListModel');

var qweb = core.qweb;


var StockOrderpointListModel = ListModel.include({

    // -------------------------------------------------------------------------
    // Public
    // -------------------------------------------------------------------------
    /**
     */
    replenish: function (records) {
       var self = this;
       var model = records[0].model;
       console.log(model, 'system work')
       var recordResIds = _.pluck(records, 'res_id');
       var context = records[0].getContext();
         this._rpc({
                    model: "stock.warehouse.orderpoint",
                    method: "launch_replenishment",
                    args: [recordResIds],
                    context: context,
                }).then(function () {
                self.trigger_up('reload');
            });
                },
//    replenish: function (records) {
//      var self = this;
//      console.log('system work')
//      var model = records[0].model;
//      var recordResIds = _.pluck(records, 'res_id');
//      var context = records[0].getContext();
//      return this._rpc({
//          model: model,
//          method: 'launch_replenishment',
//          args: [recordResIds],
//          context: context,
//      }).then(function () {
//          return self.do_action('pabs_logistics_extra.action_replenishment');
//      });
//    },

//    snooze: function (records) {
//      var recordResIds = _.pluck(records, 'res_id');
//      var self = this;
//      return this.do_action('pabs_logistics_extra.action_orderpoint_snooze', {
//          additional_context: {
//              default_orderpoint_ids: recordResIds
//          },
//          on_close: () => self.do_action('pabs_logistics_extra.action_replenishment')
//      });
//    },
});

return StockOrderpointListModel;

});
