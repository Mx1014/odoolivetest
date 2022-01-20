# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.http import request
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    default_x_customs_journal_id = fields.Many2one('account.journal', string="BOE Journal", default_model='account.move')
    default_x_overseas_journal_id = fields.Many2one('account.journal', string="Overseas Journal", default_model='account.move')