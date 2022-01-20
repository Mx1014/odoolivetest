odoo.define('pabs_logistics_extra.StockOrderpointListView', function (require) {
"use strict";

var ListView = require('web.ListView');
var StockOrderpointListController = require('pabs_logistics_extra.StockOrderpointListController');
var StockOrderpointListModel = require('pabs_logistics_extra.StockOrderpointListModel');
var viewRegistry = require('web.view_registry');


var StockOrderpointListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: StockOrderpointListController,
        Model: StockOrderpointListModel,
    }),
});

viewRegistry.add('stock_orderpoint_list', StockOrderpointListView);

return StockOrderpointListView;

});
