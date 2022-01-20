odoo.define('show_form_view_after_search.AbstractController', function (require) {
    "use strict";

    var AbstractController = require('web.AbstractController');
    var SearchFacet = require('web.SearchFacet');
    console.log(SearchFacet, 'SearchFacet')

     var includeDict = {
        reload: async function (params) {
            var res = await this._super.apply(this, arguments);
            if (this.viewType === "kanban" || this.viewType === "list"){
                //if (this.renderer.state !== undefined && this.renderer.state.count === 1 && this.modelName === "product.template") {
              if (this.modelName === "sale.order" && this.viewId === 908 || this.viewId === 905){
                var filter = document.getElementsByClassName("o_facet_remove");
                if (filter.length !== 0 && filter.length !== 1){
                    console.log(filter)
                    filter[0].click()
                } else if (filter.length !== 1) {

                  var Mainfilter = document.getElementsByClassName("o_filters_menu_button");
                  Mainfilter[0].click()
                  var menuitem = document.getElementsByClassName("o_menu_item");
                  menuitem[0].click()
                  document.body.click()
                }
                }
                if (this.renderer.state !== undefined && this.renderer.state.count === 1) {
                    var $o_record = this.renderer.$el.find('.o_data_row,.o_kanban_record').not( ".o_kanban_ghost" );


//                    if ($o_record.length === 1) {
//                        $o_record.trigger("click");
//                    }
                }
            }
            return res;
        },
    };

    AbstractController.include(includeDict);

});
