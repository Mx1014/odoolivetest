# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError, Warning
from odoo.tools import float_compare, float_is_zero

class StockInventory(models.Model):
    _name = 'stock.inventory'
    _inherit = ['stock.inventory', 'mail.thread', 'mail.activity.mixin']

    x_user_id = fields.Many2one('res.users', string="Assign To", copy=False)
    x_adju_date = fields.Date(string="Stock Take Date")


    @api.model_create_multi
    def create(self, vals_list):
        res = super(StockInventory, self).create(vals_list)
        activity = self.env.ref('pabs_inventory_adjustments.mail_activity_stock_take')
        dd = self.env['mail.activity'].sudo().create({
            'res_id': res.id,
            'res_model_id': self.env['ir.model']._get('stock.inventory').id,
            'res_name': res.name,
            'activity_type_id': activity.id,
            'summary': activity.summary,
            'user_id': res.x_user_id.id,
            'date_deadline': res.x_adju_date,
        })
        return res


    #
    # def action_validate(self):
    #     if not self.env.user.has_group('pabs_product.group_inventory_manager'):
    #         raise Warning(_('You are not allow to validate a stock take. Please Contact Your Manager'))
    #     to_move = []
    #     for line in self.line_ids:
    #         if line.x_no_validate:
    #             to_move.append(line)
    #             line.inventory_id = False
    #
    #     if to_move:
    #         self.create({
    #             'name': self.name,
    #             'x_user_id': self.x_user_id.id,
    #             'location_ids': [(6, 0, self.location_ids.ids)],
    #             'x_adju_date': self.x_adju_date,
    #             'product_ids': [(6, 0, [product.product_id.id for product in to_move])]
    #         })
    #     return super(StockInventory, self).action_validate()

    def action_validate(self):
        if not self.exists():
            return
        self.ensure_one()
        if self.state == 'confirm':
            self.action_review()
        elif self.state == 'reviews':
            if not self.user_has_groups('stock.group_stock_manager'):
                raise UserError(_("Only a stock manager can validate an inventory adjustment."))
            if not self.env.user.has_group('pabs_product.group_inventory_manager'):
                raise Warning(_('You are not allow to validate a stock take. Please Contact Your Manager'))
            if self.state != 'reviews':
                raise UserError(_(
                    "You can't validate the inventory '%s', maybe this inventory " +
                    "has been already validated or isn't ready.") % (self.name))

            to_move = []
            for line in self.line_ids:
                if line.x_no_validate:
                    to_move.append(line)
                    line.inventory_id = False

            if to_move:
                self.create({
                    'name': self.name,
                    'x_user_id': self.x_user_id.id,
                    'location_ids': [(6, 0, self.location_ids.ids)],
                    'x_adju_date': self.x_adju_date,
                    'product_ids': [(6, 0, [product.product_id.id for product in to_move])]
                })

            inventory_lines = self.line_ids.filtered(lambda l: l.product_id.tracking in ['lot',
                                                                                         'serial'] and not l.prod_lot_id and l.theoretical_qty != l.product_qty)
            lines = self.line_ids.filtered(lambda l: float_compare(l.product_qty, 1,
                                                                   precision_rounding=l.product_uom_id.rounding) > 0 and l.product_id.tracking == 'serial' and l.prod_lot_id)
            if inventory_lines and not lines:
                wiz_lines = [(0, 0, {'product_id': product.id, 'tracking': product.tracking}) for product in
                             inventory_lines.mapped('product_id')]
                wiz = self.env['stock.track.confirmation'].create({'inventory_id': self.id, 'tracking_line_ids': wiz_lines})
                return {
                    'name': _('Tracked Products in Inventory Adjustment'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'views': [(False, 'form')],
                    'res_model': 'stock.track.confirmation',
                    'target': 'new',
                    'res_id': wiz.id,
                }
            self._action_done()
            self.line_ids._check_company()
            self._check_company()
            return True

    state = fields.Selection(tracking=True)
    
    def action_start(self):
        super(StockInventory, self).action_start()
        return self.action_client_action()

    def _track_subtype(self, init_values):
        self.ensure_one()
        if "state" in init_values and self.state == "confirm":
            return self.env.ref("pabs_inventory_adjustments.mt_inventory_confirmed")
        elif "state" in init_values and self.state == "done":
            return self.env.ref("pabs_inventory_adjustments.mt_inventory_done")
        return super(StockInventory, self)._track_subtype(init_values)




class StockInventoryAdd(models.Model):
    _inherit = 'stock.inventory'

    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'In Progress'),
        ('reviews', 'Review'),
        ('done', 'Validated')],
                             copy=False, index=True, readonly=True,
                             default='draft')

    def action_review(self):
        for take in self:
            activity = self.env.ref('pabs_inventory_adjustments.mail_activity_stock_take_review')
            take.state = 'reviews'
            dd = self.env['mail.activity'].sudo().create({
                'res_id': self.id,
                'res_model_id': self.env['ir.model']._get('stock.inventory').id,
                'res_name': self.name,
                'activity_type_id': activity.id,
                'summary': activity.summary,
                'user_id': self.create_uid.id,
                'date_deadline': self.x_adju_date,
            })

class InventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    x_no_validate = fields.Boolean(string="Move", default=False, copy=False)
