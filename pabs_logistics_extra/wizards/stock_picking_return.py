from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
from datetime import datetime, timedelta


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    x_delivery_operation_id = fields.Many2one('stock.picking.type', string='Delivery Return Operation')

    @api.onchange('x_delivery_operation_id')
    def onchange_x_delivery_operation_id(self):
        if self.x_delivery_operation_id:
            if self.x_delivery_operation_id.x_is_customer_service:
                if self.product_return_moves:
                    for move in self.product_return_moves:
                        move.to_refund = False

    def _create_returns(self):
        # TODO sle: the unreserve of the next moves could be less brutal
        for return_move in self.product_return_moves.mapped('move_id'):
            return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()
        # src_picking = None
        # if self.picking_id.batch_id:
        src_picking = self.picking_id.id
        # for move in self.picking_id.move_lines:
        #     move.move_dest_ids = None

        # create new picking for returned products
        picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id
        if self.x_helpdesk_team_id and self.x_operation_id:
            picking_type_id = self.x_operation_id.id
        new_picking = self.picking_id.copy({
            'move_lines': [],
            'picking_type_id': picking_type_id,
            'state': 'draft',
            'src_picking_id': src_picking,
            'origin': _("Return of %s") % self.picking_id.name,
            'location_id': self.picking_id.location_dest_id.id,
            'location_dest_id': self.location_id.id})
        new_picking.message_post_with_view('mail.message_origin_link',
                                           values={'self': new_picking, 'origin': self.picking_id},
                                           subtype_id=self.env.ref('mail.mt_note').id)
        returned_lines = 0
        for return_line in self.product_return_moves:
            if not return_line.move_id:
                raise UserError(_("You have manually created product lines, please delete them to proceed."))
            # TODO sle: float_is_zero?
            if return_line.quantity:
                returned_lines += 1
                vals = self._prepare_move_default_values(return_line, new_picking)
                r = return_line.move_id.copy(vals)
                vals = {}

                # +--------------------------------------------------------------------------------------------------------+
                # |       picking_pick     <--Move Orig--    picking_pack     --Move Dest-->   picking_ship
                # |              | returned_move_ids              ↑                                  | returned_move_ids
                # |              ↓                                | return_line.move_id              ↓
                # |       return pick(Add as dest)          return toLink                    return ship(Add as orig)
                # +--------------------------------------------------------------------------------------------------------+
                move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')
                move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
                vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link | return_line.move_id]
                # vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
                r.write(vals)
        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))

        new_picking.action_confirm()
        new_picking.action_assign()
        for move in new_picking.move_lines:
            return_picking_line = self.product_return_moves.filtered(
                lambda r: r.move_id == move.origin_returned_move_id)
            if return_picking_line and return_picking_line.to_refund:
                move.to_refund = True
        return new_picking.id, picking_type_id

    def create_returns(self):
        res = super(ReturnPicking, self).create_returns()
        if self.x_operation_id.business_line:
            business_line = self.x_operation_id.business_line.id
            show = []
            for i in range(35):
                day = datetime.combine(fields.Date.today() + timedelta(days=i), datetime.min.time())
                slot = self.env['plan.calendar'].search(
                    [('business_line', '=', business_line), ('status', '=', 'available'),
                     ('start_datetime', '>=', day), ('start_datetime', '<', day + timedelta(days=1))], limit=10).ids
                if slot:
                    for s in slot:
                        show.append(s)
            return {
                'name': _('Logistic'),
                'res_model': 'plan.calendar',
                'view_mode': 'gantt',
                'views': [
                    (self.env.ref('pabs_logistics_extra.plan_calendar_transfer_view_gantt').id, 'gantt'),
                ],
                'target': 'new',
                'context': {"delivery_id": res['res_id']},
                'domain': [('business_line', '=', business_line), ('status', '=', 'available'), ('id', 'in', show)],
                'type': 'ir.actions.act_window',
            }
        else:
            return res
