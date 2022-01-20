from odoo import api, fields, models


class ResumeLines(models.Model):
    _inherit = 'hr.resume.line'
    x_grade = fields.Float(string='Grade')
