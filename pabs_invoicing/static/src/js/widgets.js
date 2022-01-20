odoo.define('web_one2many_selectable_credit.form_widgets', function (require) {
	"use strict";

	var core = require('web.core');
	var utils = require('web.utils');
	var _t = core._t;
	var QWeb = core.qweb;
	var fieldRegistry = require('web.field_registry');
	var ListRenderer = require('web.ListRenderer');
	var rpc = require('web.rpc');
	var FieldOne2Many = require('web.relational_fields').FieldOne2Many;
	var FormController = require('web.FormController');


//    FormController.extend({
//        events: {
//			"click .button_credit_note": "get_selected_ids_one2many",
//		},
//
//        get_selected_ids_one2many: function () {
//            var self=this;
//            var ids =[];
//            this.$el.find('td.o_list_record_selector input:checked')
//                    .closest('tr').each(function () {
//                        ids.push(parseInt(self._getResId($(this).data('id'))));
//            });
//            console.log('--------------------')
//            return ids;
//        },
//
//        _getResId: function (recordId) {
//            var record;
//            utils.traverse_records(this.recordData[this.name], function (r) {
//                if (r.id === recordId) {
//                    record = r;
//                }
//            });
//            return record.res_id;
//        },
//
//        _barcodeSaleAddRecordId: function (barcode, activeBarcode) {
//            if (!activeBarcode.handle) {
//                return $.Deferred().reject();
//            }
//            var record = this.model.get(activeBarcode.handle);
//            if (record.data.state != 'draft' & record.data.sale_order_type == 'cash_memo') {
//                this.do_warn("Warning", 'SO should be in draft state');
//                this.play_sound('error');
//                return $.Deferred().reject();
//            }
//            this.play_sound('error');
//            return this._barcodeAddX2MQuantity(barcode, activeBarcode);
//        },
//
//
//    });


//	var One2ManySelectablecredit = FieldOne2Many.extend({
//		template: 'One2ManySelectableCredit',
//		events: {
//			"click .button_credit_note": "action_selected_lines",
//		},
//		start: function()
//	    {
//	    	this._super.apply(this, arguments);
//			var self=this;
//	   },
//		//passing ids to function
//		action_selected_lines: function()
//		{
//			var self=this;
//			var selected_ids = self.get_selected_ids_one2many();
//
//			if (selected_ids.length === 0)
//			{
//				this.do_warn(_t("You must choose at least one record."));
//				return false;
//			}
//            console.log('dddddddddddddd')
//			var context = this.recordData[this.name]
//			rpc.query({
//                'model': 'account.payment.register.custom',
//                'method': 'use_credit_note',
//                'args': [selected_ids],
//                'context': {'active_model': context.context.active_model, 'active_id': context.context.active_id}
//                }).then(function () {
//                    self.trigger_up('reload');
//                    return self.do_action({ type: 'ir.actions.act_window_close' });
//            });
//		},
//
//
//		_getRenderer: function () {
//            if (this.view.arch.tag === 'kanban') {
//                return One2ManyKanbanRenderer;
//            }
//            if (this.view.arch.tag === 'tree') {
//                return ListRenderer.extend({
//                    init: function (parent, state, params) {
//                        this._super.apply(this, arguments);
//                        this.hasSelectors = true;
//                    },
//                });
//            }
//            return this._super.apply(this, arguments);
//        },
//		//collecting the selected IDS from one2manay list
//		get_selected_ids_one2many: function () {
//            var self=this;
//            var ids =[];
//            this.$el.find('td.o_list_record_selector input:checked')
//                    .closest('tr').each(function () {
//                        ids.push(parseInt(self._getResId($(this).data('id'))));
//            });
//            return ids;
//        },
//
//        _getResId: function (recordId) {
//            var record;
//            utils.traverse_records(this.recordData[this.name], function (r) {
//                if (r.id === recordId) {
//                    record = r;
//                }
//            });
//            return record.res_id;
//        },
//	});

	// register unique widget, because Odoo does not know anything about it
	//you can use <field name="One2many_ids" widget="x2many_selectable"> for call this widget
//	fieldRegistry.add('one2many_selectable_credit', One2ManySelectablecredit);
});
