# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.http import request
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"


    @api.onchange('partner_id', 'user_id', 'team_id')
    def onchage_user_statement(self):
        for statement in self:
            statement.update({'user_statement_id': self.env['account.user.statement'].search(
                [('user_id', '=', self.env.user.id), ('state', '=', 'open')]).id})

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    #x_allowed_sale_team = fields.Many2many('crm.team', string='Allowed Sale Teams')
    x_bill_journal = fields.Boolean(string="Bill Journal", store=True)
    x_master_cashier = fields.Many2many('res.users', string="Master Cashier", relation="ref_master_cashier", domain="[('groups_id.category_id.name','=', 'Sales')]")


    # @api.onchange('x_allowed_sale_team', 'type')
    # def onchange_x_allowed_sale_team(self):
    #     for journal in self:
    #         if journal.type == 'cash' and len(journal.x_allowed_sale_team) > 1:
    #             raise UserError(_('one sales team only'))

