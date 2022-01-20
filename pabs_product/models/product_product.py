from odoo import api, fields, models, _
from odoo.http import request
from odoo.osv import expression
from odoo.exceptions import Warning
from random import choice
from string import digits


class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_open_quants(self):
        domain = [('product_id', 'in', self.ids)]
        hide_location = not self.user_has_groups('stock.group_stock_multi_locations')
        hide_lot = all([product.tracking == 'none' for product in self])
        self = self.with_context(hide_location=hide_location, hide_lot=hide_lot)

        # If user have rights to write on quant, we define the view as editable.
        if self.user_has_groups('stock.group_stock_manager'):
            self = self.with_context(inventory_mode=True)
            # Set default location id if multilocations is inactive
            if not self.user_has_groups('stock.group_stock_multi_locations'):
                user_company = self.env.company
                warehouse = self.env['stock.warehouse'].search(
                    [('company_id', '=', user_company.id)], limit=1
                )
                if warehouse:
                    self = self.with_context(default_location_id=warehouse.lot_stock_id.id)
        # Set default product id if quants concern only one product
        if len(self) == 1:
            self = self.with_context(
                default_product_id=self.id,
                single_product=True
            )
        else:
            self = self.with_context(product_tmpl_id=self.product_tmpl_id.id)
        ctx = dict(self.env.context)
        ctx.update({'no_at_date': True, 'search_default_on_hand': True, 'search_default_internal_loc': True})
        return self.env['stock.quant'].with_context(ctx)._get_quants_action(domain)
