
odoo.define('pabs_hr.TO', function (require) {
"use strict";

var rpc = require('web.rpc')
var ListView = require('web.ListView')
var ListController = require('web.ListController');

var JsTocallWizard = ListController.include({
  renderButtons: function($node){
    this._super.apply(this, arguments);
    if (this.$buttons) {
      this.$buttons.on('click', '.o_list_button_salaries', this.action_to_call_wizard.bind(this));
      this.$buttons.appendTo($node);
    }
  },
  action_to_call_wizard: function(event) {
    event.preventDefault();
    var self = this;
    self.do_action({
        name: "Increment Wagess",
        type: 'ir.actions.act_window',
        res_model: 'increment.wages',
        view_mode: 'form',
        view_type: 'form',
        views: [[false, 'form']],
        target: 'new',
     });
//     action_to_call_wizard: function(event) {
//    event.preventDefault();
//    var self = this;
//    rpc.query({
//       model: 'hr.contract',
//       method:'increment_wage',
//     });

  },
});
});