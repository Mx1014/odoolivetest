# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.http import request
from odoo.osv import expression
from odoo.exceptions import Warning
from random import choice
from string import digits


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # def _set_payment_type(self):
    #     if self.env['res.users'].has_group('pabs_product.group_storable'):
    #         if self.type != 'product':
    #             return
    #             raise UserError(_('Barcode does not match any product!'))

    sale_ok = fields.Boolean(tracking="1")
    purchase_ok = fields.Boolean('Can be Purchased', default=False, tracking="1")
    can_be_expensed = fields.Boolean(string="Can be Expensed",
                                     help="Specify whether the product can be selected in an expense.", tracking="1")
    # type = fields.Selection(tracking="1", selection=_get_product_type_selection)
    type = fields.Selection(string='Product Type', required=True, tracking="1", default='product')

    list_price = fields.Float(
        'Sales Price', default=1.0,
        digits='Product Price', tracking="1",
        help="Price at which the product is sold to customers.")
    expense_policy = fields.Selection(
        [('no', 'No'), ('cost', 'At cost'), ('sales_price', 'Sales price')],
        string='Re-Invoice Expenses',
        default='no', tracking="1",
        help="Expenses and vendor bills can be re-invoiced to a customer."
             "With this option, a validated expense can be re-invoice to a customer at its cost or sales price.")
    # categ_id = fields.Many2one(
    #     'product.category', 'Product Category',
    #     change_default=True, default=None, group_expand='_read_group_categ_id', help="Select category for the current product", tracking="1")
    default_code = fields.Char(
        'Internal Reference', compute='_compute_default_code', tracking="1",
        inverse='_set_default_code', store=True)
    barcode = fields.Char('Barcode', related='product_variant_ids.barcode', readonly=False, tracking="1")
    taxes_id = fields.Many2many('account.tax', 'product_taxes_rel', 'prod_id', 'tax_id',
                                help="Default taxes used when selling the product.", string='Customer Taxes',
                                domain=[('type_tax_use', '=', 'sale')], tracking="1",
                                default=lambda self: self.env.company.account_sale_tax_id)
    supplier_taxes_id = fields.Many2many('account.tax', 'product_supplier_taxes_rel', 'prod_id', 'tax_id',
                                         string='Vendor Taxes', help='Default taxes used when buying the product.',
                                         tracking="1",
                                         domain=[('type_tax_use', '=', 'purchase')],
                                         default=lambda self: self.env.company.account_purchase_tax_id)
    product_brand_id = fields.Many2one(
        'product.brand',
        string='Brand',
        help='Select a brand for this product', tracking="1"
    )
    recurring_invoice = fields.Boolean('Subscription Product', tracking="1",
                                       help='If set, confirming a sale order with this product will create a subscription')

    x_is_part = fields.Boolean('Is Spare Part', tracking="1", help='Is this product a spare part?')
    x_product_fit = fields.One2many("product.part.rel", 'prod', 'Spare Parts')
    x_part_fit = fields.One2many("product.part.rel", 'part', 'This Part Fits')

    # x_test_rel = fields.Many2many("product.part.rel", 'This Part Fits')
    x_test_re = fields.Many2many("product.part.rel", 'prod_rel', 'x_test_re', 'part', 'This Part Fits')
    is_less_than_cost = fields.Boolean(string='Low price', compute='check_if_less_than_cost')
    less_than_cost_condition = fields.Boolean(string='Low Price', store=True)
    x_last_purchase_price = fields.Monetary(string="Last Purchase Price", compute='last_purchase_price_in_po')

    def last_purchase_price_in_po(self):
        for rec in self:
            po = self.env['purchase.order.line'].search([('product_id.default_code', '=', rec.default_code), ('state', '=', 'purchase')], order='order_id asc', limit=1)
            rec.x_last_purchase_price = po.price_unit

    # @api.onchange('x_product_fit')
    # def set_prod(self):
    #     self.x_product_fit.prod = self.id

    # @api.depends('standard_price', 'list_price')
    def check_if_less_than_cost(self):
        for rec in self:
            if rec.standard_price >= rec.list_price:
                rec.is_less_than_cost = True
                print("sjdkfdjfk   Ture")
            else:
                print("sjdkfdjfk   False")
                rec.is_less_than_cost = False
            rec.less_than_cost_condition = rec.is_less_than_cost



    # @api.onchange('standard_price.new_price', 'list_price')
    # @api.depends('standard_price.new_price', 'list_price')
    # def check_if_less_than_cost(self):
    #     for rec in self:
    #         if rec.standard_price.new_price >= rec.list_price:
    #             print(rec.standard_price.new_price >= rec.list_price, "jhhkjhkjh")
    #             rec.is_less_than_cost = True
    #             print("sjdkfdjfk   Ture")
    #         else:
    #             print("sjdkfdjfk   False")
    #             rec.is_less_than_cost = False

    @api.model_create_multi
    def create(self, vals_list):
        ''' Store the initial standard price in order to be able to retrieve the cost of a product template for a given date'''
        templates = super(ProductTemplate, self).create(vals_list)
        if "create_product_product" not in self._context:
            templates._create_variant_ids()

        # This is needed to set given values to first variant after creation
        for template, vals in zip(templates, vals_list):
            related_vals = {}
            if vals.get('barcode'):
                related_vals['barcode'] = vals['barcode']
            if vals.get('default_code'):
                related_vals['default_code'] = vals['default_code']
            if vals.get('standard_price'):
                related_vals['standard_price'] = vals['standard_price']
            if vals.get('volume'):
                related_vals['volume'] = vals['volume']
            if vals.get('weight'):
                related_vals['weight'] = vals['weight']
            # Please do forward port
            if vals.get('packaging_ids'):
                related_vals['packaging_ids'] = vals['packaging_ids']
            if related_vals:
                template.write(related_vals)
            if self.env['res.users'].has_group('pabs_product.group_storable'):
                if self.type != 'product':
                    raise UserError(_('You have To Choose The correct  Product Type'))

        for temp in templates:
            temp.product_variant_id.product_brand_id = temp.product_brand_id
            if temp.product_variant_ids:
                for variant in temp.product_variant_ids:
                    variant.product_brand_id = temp.product_brand_id
            # if vals.get('purchase_ok') and not vals.get('seller_ids'):
            #     raise Warning(_('If the product can be purchased then at least one vendor needs to be added'))

        return templates

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if 'attribute_line_ids' in vals or vals.get('active'):
            self._create_variant_ids()
        if 'active' in vals and not vals.get('active'):
            self.with_context(active_test=False).mapped('product_variant_ids').write({'active': vals.get('active')})
        if 'image_1920' in vals:
            self.env['product.product'].invalidate_cache(fnames=[
                'image_1920',
                'image_1024',
                'image_512',
                'image_256',
                'image_128',
                'can_image_1024_be_zoomed',
            ])
        if 'type' in vals and vals['type'] != 'product':
            if self.env['res.users'].has_group('pabs_product.group_storable'):
                raise UserError(_('You have To Choose The correct  Product Type'))

        # if self.purchase_ok and not self.seller_ids:
        #     raise Warning(_('If the product can be purchased then at least one vendor needs to be added'))

        return res

    @api.onchange('type')
    def _onchange_type(self):
        # Do nothing but needed for inheritance
        return {}

    # @api.onchange('x_product_fit')
    # def x_prod_part_filter(self):
    #     print(self.mapped('x_product_fit').part.ids)
    #     res = {}
    #     all = self.env['product.template'].search([('id', 'not in', self.mapped('x_product_fit').part.ids)]).ids
    #     print(all)
    #     res['domain'] = {'part': [('id', 'in', all)]}
    #     return res


class ProductPartRel(models.Model):
    _name = "product.part.rel"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']

    prod = fields.Many2one('product.template', 'Product', domain="[('x_is_part', '=', False)]")
    part = fields.Many2one('product.template', 'part', domain="[('x_is_part', '=', True)]")
    pr_name = fields.Char(string='Name', related='prod.name')
    pr_default_code = fields.Char(string='Internal Reference', related='prod.default_code')
    pa_name = fields.Char(string='Name', related='part.name')
    pa_default_code = fields.Char(string='Internal Reference', related='part.default_code')
    pa_list_price = fields.Float(string='Sales Price', related='part.list_price')
    # pr_image_1920 = fields.Image(compute='_compute_pr_image')
    pr_image_1920 = fields.Image(related='prod.image_1920')
    pa_image_1920 = fields.Image(related='part.image_1920')

    def _get_some_default(self):
        parent_id = self.env.context.get('parent_id')

        parent_model = self.env.context.get('parent_model')

        if parent_id and parent_model:
            parent_obj = self.env[parent_model].browse(parent_id)

            # now you have the parent obj to do what you want

            self.some_field = parent_obj.x_is_part

    some_field = fields.Boolean(compute='_get_some_default')

    # @api.onchange('prod')
    # def x_prod_part_filter(self):
    #     res = {}
    #     res['domain'] = {'part': [('id', 'not in', self.prod.x_part_fit.part.ids)]}
    #     return res
    #
    @api.onchange('part')
    def x_prod_part_filter(self):
        res = {}
        all = self.env['product.template'].search(
            [('id', 'not in', self.prod.mapped('x_product_fit').part.ids), ('x_is_part', '=', True)]).ids
        res['domain'] = {'part': [('id', 'in', all)]}
        return res

    @api.onchange('prod')
    def x_part_prod_filter(self):
        res = {}
        all = self.env['product.template'].search(
            [('id', 'not in', self.part.mapped('x_part_fit').prod.ids), ('x_is_part', '=', False)]).ids
        res['domain'] = {'prod': [('id', 'in', all)]}
        return res


class RepairLine(models.Model):
    _inherit = 'repair.line'
    product_id = fields.Many2one('product.product', 'Product')  # , domain="[('x_is_part', '=', True)]"

    @api.onchange('product_id')
    def dom_product_id(self):
        res = {}
        ids = []
        for rec in self.repair_id.product_id.product_tmpl_id.x_product_fit:
            for x in rec:
                ids.append(x.part.product_variant_id.id)
        print(ids)
        res['domain'] = {'product_id': [('id', 'in', ids)]}
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_last_purchase_price = fields.Monetary(string="Last Purchase Price", store=True,
                                            related="product_id.x_last_purchase_price")

    # @api.depends('partner_id')
    # def related_last_purchase_price(self):
    #     for rec in self:
    #         rec.x_last_purchase_price = rec.product_id.x_last_purchase_price
