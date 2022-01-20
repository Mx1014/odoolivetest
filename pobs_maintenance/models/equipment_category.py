from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning


class equipment_category(models.Model):
    _inherit = 'maintenance.equipment.category'
    _parent_name = "parent_id"
    _parent_store = True

    parent_id = fields.Many2one('maintenance.equipment.category', 'Parent Category', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_id = fields.One2many('maintenance.equipment.category', 'parent_id', 'Child Categories')
    is_ip = fields.Boolean(string='IP Address Applicable')
    is_login = fields.Boolean(string='Username & Password Applicable')
    issue = fields.Many2many('maintenance.issue', string='Issue')

    completeName = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)

    @api.depends('name', 'parent_id.completeName')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.completeName = '%s / %s' % (category.parent_id.completeName, category.name)
            else:
                category.completeName = category.name

