from odoo import fields, models, api


class BusinessLine(models.Model):
    _inherit = 'business.line'

    def _compute_projects(self):
        projects = self.env['project.project'].search([('business_line', '=', self.id)])
        self.projects = projects

    def _inverse_projects(self):
        # for record in self:
        print(self.projects,'ssss')
        print(self.env['project.project'].search([('business_line', '=', self.id)]),'ssssoooo')
        for project in self.projects:
            for op in self.env['project.project'].search([('id', 'in', self.projects.ids)]):
                if project.id == op.id and op.business_line != self.id:
                    op.business_line = self.id
        for proj in self.env['project.project'].search([('business_line', '=', self.id)]):
            if proj.id not in self.projects.ids and proj.business_line.id == self.id:
                print('deletion happened')
                proj.business_line = None

    business_line_type = fields.Selection(string='Business Line Type',
                                          selection=[('delivery', 'Delivery'),
                                                     ('service', 'Service')],
                                          default='delivery', tracking="1")
    projects = fields.Many2many('project.project', string='Projects', domain="[('is_fsm', '=', True)]", compute=_compute_projects, inverse=_inverse_projects, tracking="1")

    @api.onchange('business_line_type')
    def onchange_business_line_type(self):
        operations = self.env['stock.picking.type'].search([('business_line', '=', self._origin.id), ('business_line', '!=', False)]).ids
        projects = self.env['project.project'].search([('business_line', '=', self._origin.id), ('business_line', '!=', False)]).ids
        if self.business_line_type == 'delivery':
            self.projects = None
            self.operations = [(6, 0, operations)]
            print(operations,'aaa')
        elif self.business_line_type == 'service':
            self.operations = None
            self.projects = [(6, 0, projects)]
            print(projects,'bbb')



