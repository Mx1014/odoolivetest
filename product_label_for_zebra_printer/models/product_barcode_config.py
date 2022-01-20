# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################


from odoo import models, fields, api


class ProductLabelConfig(models.Model):
    _inherit = "report.template"

    barcode_height = fields.Float(string="Barcode Height")
    barcode_width = fields.Float(string="Barcode width")
    barcode_abscissa = fields.Float(string="Barcode Bottom Margin")
    barcode_ordinate = fields.Float(string="Barcode Left Margin")
    product_height = fields.Float(string="Product Name Height")
    product_width = fields.Float(string="Product Name width")
    product_abscissa = fields.Float(string="Product Name Bottom Margin")
    product_ordinate = fields.Float(string="Product Name Left Margin")
