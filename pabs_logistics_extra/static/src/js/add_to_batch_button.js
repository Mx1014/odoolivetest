
odoo.define('pabs_logistics_extra.ATB', function (require) {
"use strict";

var core = require('web.core');
var rpc = require('web.rpc');
var ListView = require('web.ListView');
var ListController = require('web.ListController');

//core.bus.on('barcode_scanned', this, function(){console.log('Barcode Scanned')});

var JsTocallWizard = ListController.include({
  renderButtons: function($node){
    this._super.apply(this, arguments);
    if (this.$buttons) {
      this.$buttons.on('click', '.o_list_button_add_to_batch', this.action_to_call_wizard.bind(this));
      this.$buttons.appendTo($node);
    }
  },

  action_to_call_wizard: function(event) {
    event.preventDefault();
    var self = this;
    console.log(self);
    console.log(self.getSelectedIds());
    if (self.getSelectedIds().length == 0) {
    self.do_warn((""), ("Nothing To Add"));
     } else {
             self._rpc({
                    'model': 'stock.picking',
                    'method': 'action_add_to_batch',
                    'args': [self.getSelectedIds(), self.initialState.context.active_id],
                    }).then(function (res){
                        console.log(res);
                        self.do_action(res);
                        });
//     self.do_action({
//        name: "Add To Batch",
//        type: 'ir.actions.act_window',
//        res_model: 'stock.picking.batch.add',
//        view_mode: 'form',
//        view_type: 'form',
//        views: [[false, 'form']],
//        target: 'new',
//        context: {ids_to_add: self.getSelectedIds(), batch_id: self.initialState.context.active_id},
     }
     }
// getSelectedRecords: function () {
//        var self = this;
//        return _.map(this.selectedRecords, function (db_id) {
//            return self.model.get(db_id, {raw: true});
//        });
//    },
//     return self._rpc({
//                    'model': 'stock.picking',
//                    'method': 'action_view_add_to_batch',
//                    'args': [[]],
//                }).then(function (res) {
//                   self.do_action(res)
//                    });
//     action_to_call_wizard: function(event) {
//    event.preventDefault();
//    var self = this;
//    rpc.query({
//       model: 'hr.contract',
//       method:'increment_wage',
//     });

});
});