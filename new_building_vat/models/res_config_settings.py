# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_enable_newbuilding = fields.Boolean("Enable", help="Enabling the new building process in sales.", implied_group='new_building_vat.group_enable_newbuilding')
    newbuilding_fasical_position_id = fields.Many2one('account.fiscal.position', string="Fiscal Position", help='The fiscal position that will be used for the new building in SO.', config_parameter='new_building_vat.newbuilding_fasical_position_id')
