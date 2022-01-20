from odoo import fields, models, api


class BusinessLine(models.Model):
    _name = "business.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Business Line"

    def _compute_operations(self):
        operations = self.env['stock.picking.type'].search([('business_line', '=', self.id), ('business_line', '!=', False)])
        print(operations, 'OPS')
        self.operations = operations

    def _inverse_operations(self):
        for record in self:
            print(self.operations,'OPPPPPP')
            print(self.env['stock.picking.type'].search([('business_line', '=', self.id)]),'OOO')
            for operation in self.operations:
                for op in self.env['stock.picking.type'].search([('id', 'in', self.operations.ids)]):
                    if operation.id == op.id and op.business_line != record.id:
                        op.business_line = record.id

            for op in self.env['stock.picking.type'].search([('business_line', '=', self.id)]):
                if op.id not in self.operations.ids and op.business_line.id == self.id:
                    print('deletion happened')
                    op.business_line = None

    name = fields.Char('Name')
    operations = fields.Many2many(comodel_name='stock.picking.type', relation='rel_business_line_operation',
                                  compute=_compute_operations, inverse=_inverse_operations, domain="['|', ('business_line', '=', False), ('business_line', '=', id)]", string='Operations')
    no_days = fields.Char(string="Show Reserve Slot After")


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"


    business_line = fields.Many2one('business.line', 'Business Line')
