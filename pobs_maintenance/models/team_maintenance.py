# -*- coding: utf-8 -*-

from odoo import models, fields, api


class new_team(models.Model):
    _inherit = 'maintenance.team'

    sequence = fields.Many2one('ir.sequence', string="seq")


class new_equipment(models.Model):
    _inherit = 'maintenance.equipment.category'

    sequence = fields.Many2one('ir.sequence', string="Sequence")
    sequence_code = fields.Char(string='Sequence Code')


    @api.model
    def create(self, vals):
        res = super(new_equipment, self).create(vals)
        if not res['sequence']:
            vals = {
                'name': res.name,
                'prefix': str(res.sequence_code),
                'padding': 5,
            }
            sequence = self.env['ir.sequence'].create(vals)
            res['sequence'] = sequence.id
        return res

