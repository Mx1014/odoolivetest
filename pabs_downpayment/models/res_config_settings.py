# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_x_completion_journal = fields.Many2one('account.journal', string="Completion Certificate", default_model='account.move')
    default_x_down_payment_journal = fields.Many2one('account.journal', string="Advance Payment", default_model='account.move')




