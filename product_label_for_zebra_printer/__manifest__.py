# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
################################################################################
{
  "name"                 :  "Print Product Label Directly Via Zebra Printer",
  "summary"              :  "The module allows you to configure the Product Label properties like height, width, size, etc",
  "category"             :  "Extra Tools",
  "version"              :  "1.0.0",
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/",
  "description"          :  "The module allows you to configure the Product Label properties like height, width, size, etc",
  "live_test_url"        :  "http://odoodemo.webkul.com/demo_feedback",
  "depends"              :  [
                             'product',
                             'wk_odoo_directly_print_reports',
                            ],
  "data"                 :  [
                              'security/ir.model.access.csv',
                              'views/product_label_configure.xml',
                              'views/product_label_zpl_report.xml',
                              'data/zpl_template_data.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "price"                :  50,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}
