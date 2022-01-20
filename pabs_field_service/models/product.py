# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import Warning
from lxml import etree
from lxml.builder import E


class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_fields_price = fields.Float(string="Unit Price")
    x_show_price = fields.Float(string="Unit Price")


    def add_price(self):
        price = 0.0
        if self.fsm_quantity:
            price = self.x_show_price
            print(price, 'price if')
        else:
            if self.list_price:
                price = self.list_price
            else:
                price = self.x_fields_price
                
        return {
            'name': ('Unit Price'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'service.price',
            'target': 'new',
            'context': {'default_product_id': self.id, 'default_name': price}
            }

    def fsm_add_quantity(self):
        task_id = self.env.context.get('fsm_task_id')
        if task_id:
            task = self.env['project.task'].browse(task_id)
            if not task.sale_order_id:
                  task._fsm_create_sale_order_custom()
            # don't add material on confirmed SO to avoid inconsistence with the stock picking
            if task.fsm_done:
                return False


            # project user with no sale rights should be able to add materials
            SaleOrderLine = self.env['sale.order.line']
            if self.user_has_groups('project.group_project_user'):
                task = task.sudo()
                SaleOrderLine = SaleOrderLine.sudo()

            sale_line = SaleOrderLine.search([('order_id', '=', task.sale_order_id.id), ('product_id', '=', self.id)], limit=1)



            if sale_line:  # existing line: increment ordered qty (and delivered, if delivered method)
                vals = {
                    'product_uom_qty': sale_line.product_uom_qty + 1
                }
                if sale_line.qty_delivered_method == 'manual':
                    vals['qty_delivered'] = sale_line.qty_delivered + 1
                sale_line.with_context(fsm_no_message_post=True).write(vals)
            else:  # create new SOL
                vals = {
                    'order_id': task.sale_order_id.id,
                    'product_id': self.id,
                    'product_uom_qty': 1,
                    'product_uom': self.uom_id.id,
                    'route_id': task.x_route_id.id,
                    'price_unit': self.x_fields_price,
                }
                if task.sale_order_id.partner_invoice_id.id == task.sale_order_id.company_id.partner_id.id:
                    vals['tax_id'] = [(6, 0, [19])]

                if self.service_type == 'manual':
                    vals['qty_delivered'] = 1

                # Note: force to False to avoid changing planned hours when modifying product_uom_qty on SOL
                # for materials. Set the current task for service to avoid re-creating a task on SO cnofirmation.
                if self.type == 'service':
                    vals['task_id'] = task_id
                else:
                    vals['task_id'] = False

                sale_line = SaleOrderLine.create(vals)

        self.x_fields_price = 0.0

        return True


    def fsm_unit_price_change(self):
        task_id = self.env.context.get('fsm_task_id')
        if task_id:
            task = self.env['project.task'].browse(task_id)

            if task.fsm_done:
                return False

            # project user with no sale rights should be able to remove materials
            SaleOrderLine = self.env['sale.order.line']
            if self.user_has_groups('project.group_project_user'):
                task = task.sudo()
                SaleOrderLine = SaleOrderLine.sudo()

            sale_line = SaleOrderLine.search([('order_id', '=', task.sale_order_id.id), ('product_id', '=', self.id)], limit=1)
            if sale_line:
                vals = {
                    'price_unit': self.x_show_price
                }
                sale_line.with_context(fsm_no_message_post=True).write(vals)

        return True

class SalesOrder(models.Model):
    _inherit = 'sale.order'

    x_task_id = fields.Many2one('project.task', string="Helpdesk task")


class PriceProduct(models.TransientModel):
    _name = 'service.price'
    _description = 'Service Price'

    name = fields.Float(string="Unit Price", digits=(16, 3))
    product_id = fields.Many2one('product.product', string="product")

    def add_price(self):
       for product in self:
           product.product_id.x_fields_price = product.name
           product.product_id.x_show_price = product.name
           if not product.product_id.fsm_quantity:
              product.product_id.fsm_add_quantity()
           else:
              product.product_id.fsm_unit_price_change()

