from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StatementPaymentMethod(models.Model):
    _name = "statement.payment.methods"
    _description = "User Statement Payment Methods"

    name = fields.Char(string="Payment Method", required=True)
    journal_account_id = fields.Many2one('account.journal', string='Journal', required=True, domain="[('type', 'in', ['cash', 'bank'])]")
    tid_ids = fields.Many2many('bank.card.readers', string="TID")
    bank_type = fields.Selection(related="journal_account_id.x_bank_type")
    journal_type = fields.Selection(related="journal_account_id.type")

    def name_get(self):
        res = []
        for method in self:
            res.append((method.id, "%s (%s)" % (method.name, method.journal_account_id.name)))
        return res


