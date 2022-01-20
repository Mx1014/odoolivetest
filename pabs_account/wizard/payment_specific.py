from odoo import fields, models, api, _
from odoo.exceptions import Warning


class LinkSpecificPayment(models.TransientModel):
    _name = 'link.specific.payment'
    _description = "Link Specific Payment Amount"

    name = fields.Many2one('account.move.line', string="Move")
    move_id = fields.Many2one('account.move', string="Moves")
    amount = fields.Float(string="Amount", digits=(16, 3))

    @api.onchange('name')
    def amount_get(self):
        self.amount = self.name.credit

    def confirm_js_assign_outstanding_line(self):
        # active_id = self._context.get('active_id')
        # print(active_id)
        # move = self.env['account.move'].browse(active_id)
        # move.js_assign_outstanding_line(self.name.id)
        # self.ensure_one()
        # #lines = self.env['account.move.line'].browse(line_id)
        # #print(lines)
        lines = self.name
        #print(move)
        print(lines.credit)
        previous_amount = lines.credit
        lines.credit = self.amount
        lines += self.move_id.line_ids.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)
        lines.reconcile()
        print(lines)
        for line in lines:
            if line.id == self.name.id:
                  line.credit = previous_amount