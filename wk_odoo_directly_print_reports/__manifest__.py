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
#################################################################################
{
  "name"                 :  "Print Odoo Reports via Zebra Printer",
  "summary"              :  "The module allows you to directly print the Odoo reports such as sale quotations, invoices, etc. using QZ Tray Client and eliminate the need to first download it as a PDF.",
  "category"             :  "Extra Tools",
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Print-Odoo-Reports-via-Zebra-Printer.html",
  "description"          :  """Odoo Print Odoo Reports via Zebra Printer
Print sale reports with network printer
Connect network printer with Odoo
Use network printer for reports
Print PDf reports with network printer
Zebra printer connection in Odoo
Odoo connect with printer""",
  "depends"              :  ['base'],
  "data"                 :  [
                             'security/ir.model.access.csv',
                             'views/ir_actions_report_xml_view.xml',
                             'views/report_template_view.xml',
                             'views/printers_view.xml',
                             'views/templates.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "price"                :  129,
  "currency"             :  "EUR",
  "external_dependencies":  {'python': ['zplgrf']},
}
