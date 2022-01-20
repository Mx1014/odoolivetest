from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    x_helpdesk_team_id = fields.Many2one('helpdesk.team', string='Helpdesk Team')
    x_helpdesk_team_operation_ids = fields.Many2many('stock.picking.type', string='Team Return Operations',
                                                     compute='compute_x_helpdesk_team_operation_ids')
    x_operation_id = fields.Many2one('stock.picking.type', string='Return Operation')

    @api.onchange('x_helpdesk_team_id')
    def compute_x_helpdesk_team_operation_ids(self):
        for rec in self:
            rec.x_helpdesk_team_operation_ids = rec.x_helpdesk_team_id.x_operation_id

    @api.onchange('picking_id', 'x_operation_id')
    def onchange_picking_id_helpdesk(self):
        if self.x_operation_id:
            if self.x_operation_id.x_is_customer_service:
                if self.product_return_moves:
                    for move in self.product_return_moves:
                        move.to_refund = False
            else:
                if self.product_return_moves:
                    for move in self.product_return_moves:
                        move.to_refund = True

        if self.x_helpdesk_team_id and self.x_helpdesk_team_operation_ids:
            res = {'domain': {'location_id': [('id', '=', self.x_operation_id.default_location_dest_id.id)]}}
            self.location_id = self.x_operation_id.default_location_dest_id
            return res

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        move_dest_exists = False
        product_return_moves = [(5,)]
        if self.picking_id and self.picking_id.state != 'done':
            raise UserError(_("You may only return Done pickings."))
        # In case we want to set specific default values (e.g. 'to_refund'), we must fetch the
        # default values for creation.
        line_fields = [f for f in self.env['stock.return.picking.line']._fields.keys()]
        product_return_moves_data_tmpl = self.env['stock.return.picking.line'].default_get(line_fields)
        for move in self.picking_id.move_lines:
            if move.state == 'cancel':
                continue
            if move.scrapped:
                continue
            if move.move_dest_ids:
                move_dest_exists = True
            product_return_moves_data = dict(product_return_moves_data_tmpl)
            #for product return

            values = self._prepare_stock_return_picking_line_vals_from_move(move)
            if values:
                product_return_moves_data.update(values)
                product_return_moves.append((0, 0, product_return_moves_data))
        if self.picking_id and not product_return_moves:
            raise UserError(
                _("No products to return (only lines in Done state and not fully returned yet can be returned)."))
        if self.picking_id:
            self.product_return_moves = product_return_moves
            self.move_dest_exists = move_dest_exists
            self.parent_location_id = self.picking_id.picking_type_id.warehouse_id and self.picking_id.picking_type_id.warehouse_id.view_location_id.id or self.picking_id.location_id.location_id.id
            self.original_location_id = self.picking_id.location_id.id
            location_id = self.picking_id.location_id.id
            if self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
                location_id = self.picking_id.picking_type_id.return_picking_type_id.default_location_dest_id.id
            if not self.x_helpdesk_team_id:
                self.location_id = location_id

    def create_returns(self):
        res = super(ReturnPicking, self).create_returns()
        picking_id = False
        if 'res_id' in res:
            picking_id = self.env['stock.picking'].browse(res['res_id'])
        elif 'context' in res:
            if 'delivery_id' in res['context']:
                picking_id = self.env['stock.picking'].browse(res['context']['delivery_id'])
        if picking_id:
            if self.ticket_id:
                picking_id.write({'x_helpdesk_ticket_id': self.ticket_id.id})
            elif self.picking_id.x_helpdesk_ticket_id:
                picking_id.write({'x_helpdesk_ticket_id': self.picking_id.x_helpdesk_ticket_id.id})
        return res


# class StockReturnPickingLine(models.TransientModel):
#     _inherit = "stock.return.picking.line"
#
#     to_refund = fields.Boolean(string="Update quantities on SO/PO", default=False,
#                                help='Trigger a decrease of the delivered/received quantity in the associated Sale Order/Purchase Order')
