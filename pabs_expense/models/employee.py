# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import email_split, float_is_zero

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    x_bank_account = fields.Many2one('account.journal', relation='bank_journal_rel', string="Bank Account")
    x_cash_account = fields.Many2one('account.journal', relation='cash_journal_rel', string="Cash Account")