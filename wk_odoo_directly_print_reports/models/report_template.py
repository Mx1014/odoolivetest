# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class ReportTemplate(models.Model):

    _name = 'report.template'

    name = fields.Char(string="Name", required=True)
    model_id = fields.Many2one(comodel_name="ir.model", string="Model", required="True")
    template_text = fields.Text(string="Report Template")

    def validate_template(self):
        pass
