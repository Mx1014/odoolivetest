from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round
from datetime import datetime, timedelta


class ReturnPicking(models.TransientModel):
    _name = 'stock.collect.picking'
    _description = 'collect Picking'

    x_ticket_id = fields.Many2one('helpdesk.ticket', string='Helpdesk Ticket')
    x_partner_id = fields.Many2one('res.partner', string='Customer')
    x_product_id = fields.Many2one('product.product', string='Product')
    x_helpdesk_team_id = fields.Many2one('helpdesk.team', string='Helpdesk Team')
    x_helpdesk_team_operation_ids = fields.Many2many('stock.picking.type', string='Team Return Operations',
                                                     compute='compute_x_helpdesk_team_operation_ids')
    x_operation_id = fields.Many2one('stock.picking.type', string='Return Operation')

    @api.onchange('x_helpdesk_team_id')
    def compute_x_helpdesk_team_operation_ids(self):
        for rec in self:
            rec.x_helpdesk_team_operation_ids = rec.x_helpdesk_team_id.x_operation_id

    def create_collection_picking(self):
        new_picking = self.env['stock.picking'].create({'partner_id': self.x_partner_id.id,
                                                        'code': 'incoming',
                                                        'picking_type_id': self.x_operation_id.id,
                                                        'location_id': self.x_operation_id.default_location_src_id.id,
                                                        'location_dest_id': self.x_operation_id.default_location_dest_id.id})

        new_move = self.env['stock.move'].create({'product_id': self.x_product_id.id,
                                                  'name': self.x_product_id.name,
                                                  'product_uom': self.x_product_id.uom_id.id,
                                                  'picking_id': new_picking.id,
                                                  'location_dest_id': new_picking.location_dest_id.id,
                                                  'location_id': new_picking.location_id.id,
                                                  'product_uom_qty': 1,
                                                  })

        new_move_line = self.env['stock.move.line'].create({'product_id': self.x_product_id.id,
                                                            'picking_id': new_picking.id,
                                                            'move_id': new_move.id,
                                                            'product_uom_id': self.x_product_id.uom_id.id,
                                                            'product_uom_qty': 1,
                                                            'qty_done': 0,
                                                            'location_dest_id': new_picking.location_dest_id.id,
                                                            'location_id': new_picking.location_id.id
                                                            })
        new_picking.state = 'assigned'
        self.x_ticket_id.picking_ids = [(4, new_picking.id)]

        if self.x_ticket_id:
            new_picking.write({'x_helpdesk_ticket_id': self.x_ticket_id.id})
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
                'context': {"delivery_id": new_picking.id},
                'domain': [('business_line', '=', business_line), ('status', '=', 'available'), ('id', 'in', show)],
                'type': 'ir.actions.act_window',
            }
        else:
            return {
                'name': _('Returned Picking'),
                'view_mode': 'form',
                'res_model': 'stock.picking',
                'res_id': new_picking.id,
                'type': 'ir.actions.act_window',
            }

