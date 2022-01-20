# Copyright 2009 NetAndCo (<http://www.netandco.net>).
# Copyright 2011 Akretion Benoît Guillot <benoit.guillot@akretion.com>
# Copyright 2014 prisnet.ch Seraphine Lantible <s.lantible@gmail.com>
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2018 Daniel Campos <danielcampos@avanzosc.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = "Product Brand"
    _order = 'name'

    name = fields.Char('Brand Name', required=True)
    description = fields.Text(translate=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        help='Select a partner for this brand if any.',
        ondelete='restrict'
    )
    logo = fields.Binary('Logo File', attachment=True)
    product_ids = fields.One2many(
        'product.template',
        'product_brand_id',
        string='Brand Products',
    )
    products_count = fields.Integer(
        string='Number of products',
        compute='_compute_products_count',
    )

    #@api.multi
    @api.depends('product_ids')
    def _compute_products_count(self):
        for brand in self:
            brand.products_count = len(brand.product_ids)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_brand_id = fields.Many2one(
        'product.brand',
        string='Brand',
        help='Select a brand for this product',  compute="_compute_get_brand_compute", inverse='_compute_set_brand_inverse', store=True
    )

    def _compute_get_brand_compute(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.product_brand_id = template.product_variant_ids.product_brand_id

    def _compute_set_brand_inverse(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.product_brand_id = template.product_brand_id


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_brand_id = fields.Many2one(
        'product.brand',
        string='Brand',
        help='Select a brand for this product', store=True
    )

class sale(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _autopost_draft_quote(self):
        ''' This method is called from a cron job.
        It is used to post entries such as those created by the module
        account_asset.
        '''
        records = self.search([
            ('state', '=', 'draft')
        ])
        records.action_confirm()

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    virtual_available = fields.Float(related="product_id.virtual_available", store=True, group_operator="sum")
    x_product_brand_id = fields.Many2one('product.brand', string='Brand Template', help='Select a brand for this product', compute="_get_product_brand")
    x_product_brands = fields.Many2one('product.brand', string='Brand', help='Select a brand for this product', store=True)
    x_categ_id = fields.Many2one('product.category', 'Product Category', store=True)
    x_free_qty = fields.Float(string='Free to use Qty', compute='compute_x_free_qty', store=True)

    @api.depends('quantity', 'reserved_quantity')
    def compute_x_free_qty(self):
        for rec in self:
            rec.x_free_qty = rec.quantity - rec.reserved_quantity

    def update_all_x_free_qty(self):
        recs = self.env['stock.quant'].search([])
        if recs:
            recs.compute_x_free_qty()

    def _get_product_brand(self):
        for stock in self:
            stock.x_product_brands = stock.product_id.product_brand_id.id
            stock.x_categ_id = stock.product_id.categ_id.id
            stock.x_product_brand_id = stock.product_id.product_brand_id.id

