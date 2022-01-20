/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */


odoo.define('wk_odoo_directly_print_reports.action_manager_report', function(require) {
    'use strict';

    var ActionManager = require('web.ActionManager');
    var rpc = require('web.rpc')
    var core = require('web.core');
    var _t = core._t;

    ActionManager.include({
        find_printer: function(p_name){
            return qz.printers.find(p_name).then(function(found) {
                return true;
            }).catch(function(e){
                return false;
            });
        },
        get_all_printers: function(){
            return qz.printers.find().then(function(data) {
                return data
            });
        },
        get_model_popup: function(cause, list=[]){
            switch(cause){
                case 'error':
                    return '<div class="modal fade" id="myModalpopup" role="dialog">'+
                    '<div class="modal-dialog modal-sm">'+
                        '<div class="modal-content">'+
                            '<div class="modal-header">'+
                            '<button type="button" class="close" data-dismiss="modal">&times;</button>'+
                            '<h4 class="modal-title">Error</h4>'+
                            '</div>'+
                            '<div class="modal-body">'+
                            'Could Not Connect To QzTray.'+
                            '</div>'+
                            '<div class="modal-footer">'+
                            '<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>'+
                            '</div>'+
                        '</div>'+
                        '</div>'+
                    '</div>'+
                    '</div>'
                case 'listing':
                    var list_templ = '<select class="wk_select_printer">'
                    _.each(list, p_name => {
                        list_templ += '<option>' + p_name + '</option>'
                    });
                    list_templ += '</select>'

                    return '<div class="modal fade" id="myModalpopup" role="dialog">'+
                    '<div class="modal-dialog modal-sm">'+
                        '<div class="modal-content">'+
                            '<div class="modal-header">'+
                            '<button type="button" class="close" data-dismiss="modal">&times;</button>'+
                            '<h4 class="modal-title">Select Printer</h4>'+
                            '</div>'+
                            '<div class="modal-body">'+
                            list_templ +
                            '<br/>'+
                            // '<input class="wk_set_default" type="checkbox"> Set As Default'+
                            '</div>'+
                            '<div class="modal-footer">'+
                            '<button type="button" class="btn btn-default pull-right print_now">Print</button>'+
                            '</div>'+
                        '</div>'+
                        '</div>'+
                    '</div>'+
                    '</div>'
            }
        },
        _triggerDownload: function (action, options, type){
            var self = this;
            var reportUrls = this._makeReportUrls(action);
            var qweb_url = reportUrls.pdf;
            if(action.report_user_action == 'send_to_printer'){
                var printer_name = action.printer_id && action.printer_id[1] || false;
                qz.websocket.connect().then(function(){
                    self.find_printer(printer_name)
                    .then(function(printer_find_opr){
                        if(printer_find_opr){
                            self._rpc({
                                model:'ir.actions.report',
                                method:'get_zpl_data',
                                args: [qweb_url]})
                            .then(function(zpl_data){
                                console.log(zpl_data)
                                var config = qz.configs.create(printer_name,{ altPrinting: true });
                                qz.print(config, zpl_data).catch(function(e) { 
                                    console.error("--Printing Error---",e); 
                                }).finally(function(){
                                    qz.websocket.disconnect();
                                });
                            });
                            //.fail(function(){
                            //    qz.websocket.disconnect();
                            //});
                        }else{
                            self.get_all_printers().then(function(get_printers_opr){
                                var model_popup = self.get_model_popup("listing", get_printers_opr) 
                                $("#myModalpopup").remove();
                                $('body').append(model_popup);
                                $("#myModalpopup").modal();
                                $('.print_now').on("click", function(e){
                                    var printer_name = $("select.wk_select_printer option").filter(":selected").text();
                                    var args = [qweb_url];
                                    self._rpc({
                                        model:'ir.actions.report',
                                        method:'get_zpl_data',
                                        args: args})
                                    .then(function(zpl_data){
                                        var config = qz.configs.create(printer_name, { altPrinting: true });
                                        qz.print(config, zpl_data).catch(function(e) {
                                            console.error("--Printing Error---",e); 
                                        }).finally(function(){
                                            $(".close").trigger("click");
                                            qz.websocket.disconnect();
                                        });
                                    });
                                    //.fail(function(){
                                    //    qz.websocket.disconnect();
                                    //});
                                });
                            });
                        }
                    });
                }).catch(function(e){
                    qz.websocket.disconnect();
                    var model_popup = self.get_model_popup("error")
                    
                    $('body').append(model_popup);
                    $("#myModalpopup").modal();
                });
            }else
                return this._super(action, options, type);
        },
    });
});
