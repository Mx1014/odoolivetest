from odoo import models, fields, _


class CreateTaskCrm(models.TransientModel):
    _inherit = 'crm.create.fsm.task'

    def _domain_project_id(self):
        active_ids = self._context.get('active_id')
        lead = self.env['crm.lead'].browse(active_ids)
        return [('is_fsm', '=', True), ('id', 'in', lead.x_opportunity_type_id.project_ids.ids)]

    project_id = fields.Many2one('project.project', string='Project', help='Project in which to create the task',
                                 required=True, domain=_domain_project_id)