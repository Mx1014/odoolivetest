from odoo import fields, models, api, _
from odoo.exceptions import Warning


class LinkSpecificPayment(models.TransientModel):
    _name = 'link.specific.payment'
    _description = "Link Specific Payment Amount"

    name = fields.Many2one('account.move.line', string="Move")
    move_id = fields.Many2one('account.move', string="Move Id")
    amount = fields.Float(string="Amount", digits=(16, 3))

    @api.onchange('name')
    def amount_get(self):
        line = self.name
        move = self.name.move_id
        amount_to_show = 0.0
        if line.currency_id and line.currency_id == move.currency_id:
            amount_to_show = abs(line.amount_residual_currency)
        else:
            currency = line.company_id.currency_id
            amount_to_show = currency._convert(abs(line.amount_residual), move.currency_id, move.company_id,
                                               line.date or fields.Date.today())
        self.amount = amount_to_show

    def confirm(self):
        for move in self:
            if move.amount <= 0:
                raise Warning(_("Wrong Amount"))
            move.move_id.js_assign_outstanding_line(self.name.id, self.amount)
        return {'type': 'ir.actions.client', 'tag': 'reload'}
            #move.move_id.auto_reconcile_lines(self.amount)