# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################


from odoo import fields, api, models
from odoo.exceptions import Warning, UserError
import logging
import re
from tempfile import mkstemp
_logger = logging.getLogger(__name__)
try:
    from zplgrf import GRF
except Exception as e:
    _logger.error("Library zplgrf not found!. Please install it using: 'pip install zplgrf'!!-- %r", e)

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'


    @api.model
    def get_zpl_data(self, qweb_url, printer_name=False):
        data = []
        qweb_source_parts = qweb_url.split('/')
        _logger.info("--------------%r"%qweb_source_parts)
        report = self.search([('report_name', '=', str(qweb_source_parts[-2]))])[0]
        if report.use_template:
            report_template_id = report.report_template_id
            if report_template_id:
                template_text = report_template_id.template_text or ""
                model_name = report.model
                model_id = qweb_source_parts[-1]
                if model_id.find(','):
                    model_ids = model_id.split(',')
                    model_ids = list(map(lambda x: int(x), model_ids))
                    for m_id in model_ids:
                        zpl_data = self.parse_template(template_text, model_name, m_id, report_template_id)
                        data.append(zpl_data)
            return data
        reportname = qweb_source_parts[-2]
        docids = qweb_source_parts[-1]
        document = self.report_routes(reportname, docids=docids, converter="pdf")
        pages = GRF.from_pdf(document, 'DEMO')
        fd, file_name = mkstemp()
        with open(file_name, "w+") as f:
            temp = ''
            for grf in pages:
                grf.optimise_barcodes()
                zpl_line = grf.to_zpl()
                try:
                    zpl_line = zpl_line.encode(encoding='UTF-8',errors='strict')
                except Exception as e:
                    _logger.info("---------encoding--EXCEPTION---2---%r", e)
                finally:
                    data.append(zpl_line)
        return data

    
    @api.model
    def parse_template(self, template_text, model_name, model_id, template_id):
        model_obj = self.env[str(model_name)].browse(model_id)
        _logger.info("==========%r    "%model_obj)
        try:
            elements = re.findall(r'{(.*?)}', template_text)
            for element in elements:
                if "self" in element:
                    ele = element.replace("self", 'model_obj').replace("{", "").replace("}", "")
                else:
                    ele = element
                value = eval(ele)
                template_text = template_text.replace(element, str(value))
                template_text = template_text.replace("{", "").replace("}", "")
            _logger.info("-----PARSED_template_text-------%r", template_text)
        except Exception as e:
            _logger.info("-----parse_template_EXCEPTION-------%r", e)
            raise UserError("Unable To Parse The Configured Report Template. Please Check The Template And Try Again!\n\nError: {}".format(e))
        else:
            try:
                template_text = template_text.encode(encoding='UTF-8',errors='strict')
            except Exception as e:
                _logger.info("---------encoding--EXCEPTION---1---%r", e)
            finally:
                return template_text