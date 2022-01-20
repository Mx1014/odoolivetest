from odoo import api, fields, models, _


# from odoo.exceptions import AccessError, UserError, ValidationError, Warning


class OtherTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    name = fields.Char("Other Ticket")
    other_list = fields.Many2one(string='other ticket')


class newduplicateticket(models.Model):
    _inherit = 'helpdesk.ticket'

    new_ticket_list = fields.One2many('helpdesk.ticket', 'other_list', readonly=True,
                                      compute='onchange_warranty_reference')
    is_is_close = fields.Boolean(related="stage_id.is_close")

    @api.model
    @api.onchange('partner_id')
    def onchange_warranty_reference(self):
        res = {}
        ids = self.env['helpdesk.ticket'].search(
            [('partner_id', '=', self.partner_id.id)])
        self.new_ticket_list = ids

        # return res

    # @api.constrains('id', 'product_id')
    # def compare_product(self):
    #     res = {}
    #     if self.env['helpdesk.ticket'].search(
    #             [('id', '!=', self.id), ('id', '!=', False), ('product_id', '=', self.product_id.id),
    #              ('stage_id', "!=", "Solved"), ('stage_id', "!=", "Cancelled"), ('stage_id', "!=", "Closed"),
    #              ('sale_order_id', '=', self.sale_order_id.id)]):
    #         # raise UserError('This customer already have ticket for this product.')
    #     return res
