# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountTax(models.Model):
    _inherit = 'account.tax'

    is_paid_at_customs = fields.Boolean(string='Is Paid at Customs', default=False)

    @api.model
    def create(self, vals):
        res = super(AccountTax, self).create(vals)
        tax_ids = self.env['account.tax'].search_count([('is_paid_at_customs', '=', True)])
        if tax_ids > 1:
            raise UserError(_("You can not have two taxes with the option 'Is Paid at Customs' enabled!"))
        return res

    def write(self, vals):
        res = super(AccountTax, self).write(vals)
        tax_ids = self.env['account.tax'].search_count([('is_paid_at_customs', '=', True)])
        if tax_ids > 1:
            raise UserError(_("You can not have two taxes with the option 'Is Paid at Customs' enabled!"))
        return res

    @api.onchange('is_paid_at_customs')
    def _onchange_is_paid_at_customs(self):
        if self.type_tax_use != 'purchase':
            raise UserError(_("You can not enable this option while the 'Tax Scope' is not 'Purchase'!"))
