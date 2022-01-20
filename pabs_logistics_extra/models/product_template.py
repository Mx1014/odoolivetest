from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    subcontractor_service = fields.Boolean(string="Subcontractor Service", default=False)


    length = fields.Float(string='Length (L)')
    width = fields.Float(string='Width (W)')
    height = fields.Float(string='Height (H)')
    dimension_unit = fields.Selection([('cm', 'CM'), ('mm', 'MM')], string='Dimension Unit')


    @api.onchange('length', 'width', 'height', 'dimension_unit')
    @api.depends('length', 'width', 'height', 'dimension_unit')
    def compute_dimension(self):
        if self.dimension_unit == 'cm':
            self.volume = (self.length * self.width * self.height) / 1000000
        elif self.dimension_unit == 'mm':
            self.volume = (self.length * self.width * self.height) / 1000000000




class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.depends('product_tmpl_id.subcontractor_service')
    def _compute_subcontractor_service(self):
        for rec in self:
            rec.subcontractor_service = rec.product_tmpl_id.subcontractor_service

    subcontractor_service = fields.Boolean(string="Subcontractor Service", default=False,
                                           compute=_compute_subcontractor_service, store=1)


    @api.onchange('length', 'width', 'height', 'dimension_unit')
    @api.depends('length', 'width', 'height', 'dimension_unit')
    def compute_dimension(self):
        if self.dimension_unit == 'cm':
            self.volume = (self.length * self.width * self.height) / 1000000
        elif self.dimension_unit == 'mm':
            self.volume = (self.length * self.width * self.height) / 1000000000

