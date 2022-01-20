from odoo import models, fields, api, _


class LeadType(models.Model):
    _name = "crm.lead.type"

    name = fields.Char(string="Name")
    project_ids = fields.Many2many('project.project', string="Default Project", domain=[('is_fsm', '=', True)])
    short_name = fields.Char(string="Short Code")
    sequence_number_next = fields.Integer(string='Next Number', compute='_compute_seq_number_next',
                                          inverse='_inverse_seq_number_next')
    sequence_id = fields.Many2one('ir.sequence', string='Sequence', required=True, copy=False)

    @api.depends('sequence_id.use_date_range', 'sequence_id.number_next_actual')
    def _compute_seq_number_next(self):
        '''Compute 'sequence_number_next' according to the current sequence in use,
        an ir.sequence or an ir.sequence.date_range.
        '''
        for terminal in self:
            if terminal.sequence_id:
                sequence = terminal.sequence_id._get_current_sequence()
                terminal.sequence_number_next = sequence.number_next_actual
            else:
                terminal.sequence_number_next = 1

    def _inverse_seq_number_next(self):
        '''Inverse 'sequence_number_next' to edit the current sequence next number.
        '''
        for terminal in self:
            if terminal.sequence_id and terminal.sequence_number_next:
                sequence = terminal.sequence_id._get_current_sequence()
                sequence.sudo().number_next = terminal.sequence_number_next

    @api.model
    def create(self, vals):
        if 'name' in vals:
            vals['sequence_id'] = self.env['ir.sequence'].sudo().create({
                'name': vals['name'],
                'implementation': 'standard',
                'padding': 4,
                'number_increment': 1,
                #'company_id': self.company_id.id,
                'use_date_range': True,
                'prefix': '%(range_y)s/',
            }).id
        return super(LeadType, self).create(vals)