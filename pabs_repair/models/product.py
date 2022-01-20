from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_service_category = fields.Many2one('service.category', string="Service Category", compute="_compute_get_service_compute", inverse='_compute_set_service_inverse', store=True)


    def _compute_get_service_compute(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.x_service_category = template.product_variant_ids.x_service_category

    def _compute_set_service_inverse(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.x_service_category = template.x_service_category


class ProductProduct(models.Model):
    _inherit = "product.product"

    x_service_category = fields.Many2one('service.category', string="Service Category", store=True)

class ServiceCategory(models.Model):
    _name = 'service.category'
    _description = 'Service Category'

    name = fields.Char(string="Category")
    project_id = fields.Many2one('project.project', string="Default Project", domain=[('is_fsm', '=', True)])