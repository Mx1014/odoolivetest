from odoo import fields, models, api, _
from odoo.exceptions import Warning, UserError, AccessError


class StockPickingBatchConfirm(models.TransientModel):
    _name = 'stock.picking.batch.confirm'
    _description = "Stock Picking Batch Confirm Wizard"

    def done(self):
        self.ensure_one()
        batch_id = self._context.get('batch_id')
        batch = self.env['stock.picking.batch'].search([('id', '=', batch_id)])
        print(batch)
        if batch.picking_ids:
            if not batch.x_batch_po and batch.x_vendor:
                batch_po = self.env['purchase.order'].search([('x_is_delivery_expense', '!=', False), ('x_team_id', '=', batch.x_team.id), ('partner_id', '=', batch.x_vendor.id), ('state', 'not in', ['done', 'cancel', 'purchase'])], limit=1)
                if batch_po:
                    batch_po.x_batch_ids = [(4, batch.id)]
                    batch.x_batch_po = batch_po
                else:
                    warehouse = self.env['stock.warehouse'].search([('code', '=', 'SP')], limit=1).id
                    print(warehouse, 'WAREHOUSE')
                    pick_type_id = self.env['stock.picking.type'].search([('name', '=', 'Goods Receipt Note'), ('warehouse_id', '=', warehouse)], limit=1).id
                    print(pick_type_id, 'PICK')
                    vals = {'partner_id': batch.x_vendor.id,
                            'x_is_delivery_expense': True,
                            'x_batch_ids': [batch.id],
                            'payment_term_id': self.env['account.payment.term'].search([('name', '=', 'Immediate Payment')]).id,
                            'picking_type_id': pick_type_id,
                            'fiscal_position_id': batch.x_vendor.property_account_position_id.id
                            }
                    batch_po = self.env['purchase.order'].create(vals)
                    batch.x_batch_po = batch_po
                    # warehouse = self.env['stock.warehouse'].search([('name', '=', 'split')], limit=1).id
                    # batch.x_batch_po.picking_type_id = self.env['stock.picking.type'].search([('name', '=', 'Goods Receipt Note'), ('warehouse_id', '=', warehouse)], limit=1).id

            for picking in batch.picking_ids:
                if picking.state != 'done':
                    raise UserError(_("Some Deliveries Are Not Done."))
                if not picking.x_is_delivered:
                    raise UserError(_("Some Orders Are Not Delivered."))
                picking.action_batch_done_delivered()

            # batch.x_batch_po.write({'state': 'done'})
            return batch.done()



