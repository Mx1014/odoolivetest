odoo.define('stock_check.StockOrderpointListView', function (require) {
"use strict";

var ListView = require('web.ListView');
var StockOrderpointListController = require('stock_check.StockOrderpointListController');
var StockOrderpointListModel = require('stock_check.StockOrderpointListModel');
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
