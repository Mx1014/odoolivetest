# Copyright 2020 Creu Blanca
# Copyright 2020 Ecosoft Co., Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from io import BytesIO

from odoo import _, fields, models, api
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)
try:
    from PyPDF2 import PdfFileReader, PdfFileWriter
except ImportError as err:
    _logger.debug(err)


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    encrypt = fields.Selection(
        [("manual", "Manual Input Password"), ("auto", "Auto Generated Password")],
        string="Encryption",
        help="* Manual Input Password: allow user to key in password on the fly. "
        "This option available only on document print action.\n"
        "* Auto Generated Password: system will auto encrypt password when PDF "
        "created, based on provided python syntax.",
    )
    encrypt_password = fields.Char(
        help="Python code syntax to gnerate password.",
    )

    x_is_encrypt = fields.Boolean(string='Encrypt ?')

    def render_qweb_pdf(self, res_ids=None, data=None):
        if not self.env.context.get("res_ids"):
            return super(IrActionsReport, self.with_context(res_ids=res_ids)).render_qweb_pdf(
                res_ids=res_ids, data=data
            )
        return super(IrActionsReport, self).render_qweb_pdf(res_ids=res_ids, data=data)

    # def _get_pdf_password(self, res_id):
    #     encrypt_password = False
    #     if self.encrypt == "manual":
    #         # If use document print action, report_download() is called,
    #         # but that can't pass context (encrypt_password) here.
    #         # As such, file will be encrypted by report_download() again.
    #         # --
    #         # Following is used just in case when context is passed in.
    #         encrypt_password = '' #self._context.get("encrypt_password", False)
    #     elif self.encrypt == "auto" and self.encrypt_password:
    #         obj = self.env[self.model].browse(res_id)
    #         try:
    #             encrypt_password = safe_eval(self.encrypt_password, {"object": obj})
    #         except Exception:
    #             raise ValidationError(
    #                 _("Python code used for encryption password is invalid.\n%s")
    #                 % self.encrypt_password
    #             )
    #     return encrypt_password

    def _encrypt_pdf(self, data, password):
        if not password:
            return data
        output_pdf = PdfFileWriter()
        # print(data)
        in_buff = BytesIO(data)
        pdf = PdfFileReader(in_buff)
        output_pdf.appendPagesFromReader(pdf)
        output_pdf.encrypt(password)
        buff = BytesIO()
        output_pdf.write(buff)
        return buff.getvalue()

    def _get_readable_fields(self):
        return super()._get_readable_fields() | {"encrypt"}


    @api.model
    def _run_wkhtmltopdf(
            self,
            bodies,
            header=None,
            footer=None,
            landscape=False,
            specific_paperformat_args=None,
            set_viewport_size=False,
    ):
        result = super(IrActionsReport, self)._run_wkhtmltopdf(
            bodies,
            header=header,
            footer=footer,
            landscape=landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size,
        )

        if self.x_is_encrypt and self.model == 'hr.payslip':
            obj = self.env[self.model].browse(self.env.context.get("res_ids"))
            document = self._encrypt_pdf(result, obj.employee_id.identification_id)
            return document
        else:
            return result
