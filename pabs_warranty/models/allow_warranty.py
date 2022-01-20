from odoo import models, fields, api, _
from odoo.exceptions import Warning


class ProductProductWarranty(models.Model):
    _inherit = 'product.product'
    allow_warranty = fields.Boolean(string='Allow warranty')
    warranty_time = fields.Many2one('warranty.period', string='Warranty Period')
    extended_time = fields.Many2one('extended.warranty.period', string='Extended Period')
    allow_extended_warranty = fields.Boolean(string='Allow Extended warranty')
    is_extended = fields.Boolean(string='Is Extended Warranty')
    extended_warranty_agent = fields.Many2one('res.partner', string='Extended Warranty Agent')



class ProductWarranty(models.Model):
    _inherit = 'product.template'
    allow_warranty = fields.Boolean(string='Allow warranty')
    warranty_time = fields.Many2one('warranty.period', string='Warranty Period')
    extended_time = fields.Many2one('extended.warranty.period', string='Extended Period')
    extended_warranty_agent = fields.Many2one('res.partner', string='Extended Warranty Agent')
    allow_extended_warranty = fields.Boolean(string='Allow Extended warranty')
    is_extended = fields.Boolean(string='IS Extended Warranty')

    @api.model_create_multi
    def create(self, vals_list):
        templtes = super(ProductWarranty, self).create(vals_list)
        for temp in templtes:
            temp.product_variant_id.warranty_time = temp.warranty_time
            temp.product_variant_id.extended_time = temp.extended_time
            temp.product_variant_id.allow_warranty = temp.allow_warranty
            temp.product_variant_id.allow_extended_warranty = temp.allow_extended_warranty
            temp.product_variant_id.extended_warranty_agent = temp.extended_warranty_agent
            if temp.product_variant_ids:
                for variant in temp.product_variant_ids:
                    variant.warranty_time = temp.warranty_time
                    variant.extended_time = temp.extended_time
                    variant.allow_warranty = temp.allow_warranty
                    variant.allow_extended_warranty = temp.allow_extended_warranty
                    variant.extended_warranty_agent = temp.extended_warranty_agent
        return templtes

    @api.onchange('is_extended')
    def onchange_is_extended(self):
        self.allow_warranty = False
        self.warranty_time = False
        self.allow_extended_warranty = False
