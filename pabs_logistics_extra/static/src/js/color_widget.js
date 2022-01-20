odoo.define('pabs_logistics_extra.colorWidget', function (require) {
"use strict";
var Widget = require('web.Widget');
var core = require('web.core');
var dom = require('web.dom');
var session = require('web.session');

var FieldMonetary = require('web.basic_fields').FieldMonetary;
var fieldRegistry = require('web.field_registry');
var CustomFieldChar = FieldMonetary.extend({
    _renderReadonly: function () {
         console.log(this, 'THISSSSSSSSSSSSS');
         this._super.apply(this, arguments);
    },
});
fieldRegistry.add('color_widget', CustomFieldChar);
//var totalColorWidget = Widget.extend({
//    init: function (parent) {
//            this._super.apply(this, arguments);
//            console.log(this, 'THISSSSSSSSSSSSS');
//            }
//
//
//});
});
