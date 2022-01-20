# -*- coding: utf-8 -*-

from odoo import models, fields, api


# class pabs_workshop_stock(models.Model):
#     _name = 'pabs_workshop_stock.pabs_workshop_stock'
#     _description = 'pabs_workshop_stock.pabs_workshop_stock'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

class Location(models.Model):
    _inherit = 'stock.location'

    x_service_type = fields.Selection([('out', 'Outdoor'), ('in', 'Indoor')], string="Service Type")
    x_team = fields.Many2one('logistics.team', string="Team", inverse='_compute_set_service_inverse')
    x_technician = fields.Many2one('hr.employee', string="Technician", inverse='_compute_set_service_tichn_inverse')
    x_route = fields.Many2one('stock.location.route', string="Default Route", inverse='_compute_set_route_inverse')

    def _compute_set_service_inverse(self):
        for template in self:
            template.x_team.x_location = self.id

    def _compute_set_service_tichn_inverse(self):
        for template in self:
            template.x_technician.x_location_id = self.id

    def _compute_set_route_inverse(self):
        for template in self:
            template.x_team.x_route_id = self.x_route.id

    @api.constrains('x_team')
    def _change_team_location(self):
        if self.x_team:
            locations = self.env['stock.location'].search([('id', '!=', self.id)])
            for location in locations:
                location.x_team = False

    @api.constrains('x_technician')
    def _change_team_location(self):
        if self.x_technician:
            locations = self.env['stock.location'].search([('id', '!=', self.id)])
            for location in locations:
                location.x_technician = False


class LogisticTeam(models.Model):
    _inherit = 'logistics.team'

    x_route = fields.Many2one('stock.location.route', string="Default Route")
    x_location = fields.Many2one('stock.location', string="Default Location")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_onhand_workshop_qty = fields.Float(string='On-Hand Qty', compute='_get_onhand_stock_workshop')
    x_onhand_workshop_qty_filter = fields.Float(string='On Hand')
    x_location_id = fields.Many2one('stock.location', string="Default Source Location")

    def _get_onhand_stock_workshop(self):
        for product in self:
            product.x_onhand_workshop_qty = 0.0
            task = self.env['project.task'].search([('id', '=', self._context.get('fsm_task_id'))])
            # for pro in task.x_product_id.x_product_fit.mapped('part').product_variant_id:
            #     print(pro.name, 'loc')
            #     location = self.env['stock.quant'].search([('product_id', '=', pro.id), ('location_id', '=', task.x_team_id.x_location.id)])
            #     print(location.inventory_quantity, 'inventory_quantity')
            #     if location:
            #         location.product_id.x_onhand_workshop_qty = location.inventory_quantity
            #     else:
            #         pro.x_onhand_workshop_qty = 0.0
            # print(task.x_product_id.x_product_fit.mapped('part.product_variant_id').ids)
            location = self.env['stock.quant'].search(
                [('product_id', 'in', task.project_id.mapped('x_product_ids').ids),
                 ('location_id', '=', task.x_team_id.x_location.id)])
            for loc in location:
                print("loading here ...")
                loc.product_id.x_onhand_workshop_qty = loc.x_free_qty
                loc.product_id.x_onhand_workshop_qty_filter = loc.x_free_qty


class ProjectTask(models.Model):
    _inherit = "project.task"

    def action_fsm_view_material(self):
        """Override to remove tracked products from the domain.
        """
        action = super(ProjectTask, self).action_fsm_view_material()
        ctx = self._context.copy()
        ctx.update({'team': self.x_team_id})
        action['context']['search_default_onhand_qty'] = 1
        return action


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    x_location_id = fields.Many2one('stock.location', string="Default Location")


class RepairLine(models.Model):
    _inherit = 'repair.line'

    @api.onchange('type', 'repair_id')
    def onchange_operation_type(self):
        res = super(RepairLine, self).onchange_operation_type()
        if self.type == 'add':
            if self.repair_id.technician.x_location_id:
                self.location_id = self.repair_id.technician.x_location_id.id
        return res


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_location_id = fields.Many2one('stock.location', string="Default Source Location",
                                    inverse='_inverse_set_workshop_location', compute="_get_workshop_location")

    def _inverse_set_workshop_location(self):
        for template in self:
            if len(template.product_variant_ids) != 1:
                for variant in template.product_variant_ids:
                    variant.x_location_id = template.x_location_id.id
            else:
                template.product_variant_id.x_location_id = template.x_location_id.id

    def _get_workshop_location(self):
        for template in self:
            template.x_location_id = template.product_variant_id.x_location_id.id


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.onchange('product_id')
    def onchange_product_source_location(self):
        for move in self:
            if move.product_id:
                move.location_id = move.product_id.x_location_id.id
