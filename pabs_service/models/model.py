from odoo import models, fields, api


class Repair(models.Model):
    _inherit = 'repair.order'

    @api.onchange('product_id', 'partner_id')
    def onchange_ticket(self):
        res = {}
        ids = self.env['helpdesk.ticket'].search(
            ['&', ('partner_id', '=', self.partner_id.id), ('product_id', '=', self.product_id.id)])
        prod_ids = []
        print(prod_ids)
        print(ids)
        for rec in ids:
            prod_ids.append(rec.id)
        res["domain"] = {'ticket': [("id", "in", prod_ids)]}

        return res

    ticket = fields.Many2one('helpdesk.ticket', string='Ticket', index=True)
