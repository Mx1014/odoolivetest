from odoo import models, fields, api, _
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class ResumeLineInherit(models.Model):
    _inherit = 'hr.resume.line'
    x_position = fields.Char(string='Position')
