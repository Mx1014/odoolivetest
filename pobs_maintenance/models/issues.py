from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning


class issue(models.Model):
    _name = 'maintenance.issue'
    _description = 'Maintenance Issue'

    name = fields.Char()
    issue_name = fields.Char()
    categories = fields.Many2many('maintenance.equipment.category')
