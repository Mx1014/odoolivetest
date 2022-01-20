from odoo import models, fields, api, _
from odoo.exceptions import Warning


class HelpdeskIssueType(models.Model):
    _name = 'helpdesk.issue.type'
    _description = 'Helpdesk Issue Type'

    name = fields.Char(string='name')


class HelpdeskType(models.Model):
    _inherit = 'helpdesk.ticket.type'

    x_ticket_issue = fields.Many2many('helpdesk.issue.type', string="Issue Type")
    x_product_required = fields.Boolean(string="Product Required ?", default=False)