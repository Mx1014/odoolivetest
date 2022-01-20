from odoo import models, fields, api, _
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    # def action_save_attachment_pabs_hr(self):
    #     x = self.env['hr.employee'].search([('id', '=', self.res_id)]).test(self.id)
    #     y = self.env['documents.document'].search([('attachment_id', '=', self.id)])
    #     print(x, "xxxx")
    #     print(y, "yyyyy")
    #     x.emp_cpr = y
    #     return self
    #     vals = {'res_model': self.res_model,
    #             'res_id': self.res_id,
    #             'name': self.name}
    #     saved = self.create(vals)
    #     x = self.env['hr.employee'].search([('id', '=', saved.res_id)])
    #     print(x, "xxxxxxx")
    #
    #     print(x.emp_cpr, "cppppppp")
    #     print(saved, "ssssss")
    #     x.emp_cpr = saved.id