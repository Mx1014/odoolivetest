from odoo import fields, models, api, _


class CallReasons(models.Model):
    _name = "call.reason"
    _description = "CRM Call Reasons"

    name = fields.Char(string="Reason")