odoo.define('stock_check.QtyAtDateWidgetEdit', function (require) {
"use strict";

var core = require('web.core');
var QWeb = core.qweb;

var Widget = require('web.Widget');
var Context = require('web.Context');
var data_manager = require('web.data_manager');
var widget_registry = require('web.widget_registry');
var config = require('web.config');
var QtyAtDateWidget = require('sale_stock.QtyAtDateWidget');
var proto = QtyAtDateWidget.prototype;

console.log(proto, 'proto');

var _t = core._t;
var time = require('web.time');

QtyAtDateWidget.include({


    get_vals: function (){
       var self = this;
       return this._rpc({
                    model: 'sale.order.line',
                    method: 'get_stock_location_vals',
                    args: [[this.data.x_related_stock_quant_ids.res_ids]]
                }).then(function(res) {
                        console.log(res)
//                        for (let i = 0; i < 2; i++) {
//                            self.data.x_related_stock_quant_ids.data = res
//                        }
                        self.data.x_related_stock_quant_ids['res_ids'] = res.display_name
                        console.log(self.data, 'hhhh')
                        console.log(res.display_name, 'aaaaaa')

                        });



    },

    _setPopOver: function () {
        var self = this;
        if (!this.data.scheduled_date) {
            return;
        }
        this.data.delivery_date = this.data.scheduled_date.clone().add(this.getSession().getTZOffset(this.data.scheduled_date), 'minutes').format(time.getLangDateFormat());
        // The grid view need a specific date format that could be different than
        // the user one.
        this.data.delivery_date_grid = this.data.scheduled_date.clone().add(this.getSession().getTZOffset(this.data.scheduled_date), 'minutes').format('YYYY-MM-DD');
        this.data.debug = config.isDebug();
        var values = this._rpc({
            model: 'sale.order.line',
            method: 'get_stock_location_vals',
            args: [[this.data.x_related_stock_quant_ids.res_ids]]
        }).then(function(res) {
          console.log(res)
//                        for (let i = 0; i < 2; i++) {
//                            self.data.x_related_stock_quant_ids.data = res
//                        }
          self.data.x_related_stock_quant_ids['locations'] = res

          var $content = $(QWeb.render('sale_stock.QtyDetailPopOver', {
            data: self.data,
           }));

           var $forecastButton = $content.find('.action_open_forecast');
        $forecastButton.on('click', function(ev) {
            ev.stopPropagation();
            data_manager.load_action('stock.report_stock_quantity_action_product').then(function (action) {
              var reportname = 'stock_check.report_product_product_replenishment?docids=' +
                          self.data.product_id.data.id +
                          '&report_type=qweb-html&model_name=product.product';
              var action = {
            'name': 'Forecast',
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': reportname,
            'report_file': 'stock_check.report_product_product_replenishment',
            };
              return self.do_action(action);
            });
        });

           var options = {
            content: $content,
            html: true,
            placement: 'left',
            title: _t('Availability'),
            trigger: 'focus',
            delay: {'show': 0, 'hide': 100 },
        };
        self.$el.popover(options);

        });

    }

});

});
