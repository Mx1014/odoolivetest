# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.http import request
from odoo.osv import expression
from odoo.exceptions import Warning
from random import choice
from string import digits


class ProductTemplate(models.Model):
    _inherit = "product.template"

    price_minimum = fields.Float(string="Minimum Sale Price", compute='_compute_msp', inverse='_set_msp_values')
    minimum_cal_type = fields.Selection([('bd', 'BD'), ('percent', '%')], default='percent', compute='_compute_msp', inverse='_set_msp_values')
    minimum_cal_number = fields.Float(string='Minimum Margin', compute='_compute_msp', inverse='_set_msp_values')
    # barcode_ids = fields.One2many(related='product_variant_ids.barcode_ids',readonly=False)
    barcode_ids = fields.One2many('multi.product.barcode', 'product_tmp_id', string="Barcodes", compute="_compute_get_barcode", inverse='_compute_set_barcode', store=True)
    x_exist_in_pos = fields.Boolean(string="Exist in POS", compute="_compute_get_exist_in_pos", inverse="_set_exist_in_pos")


    # _sql_constraints = [
    #     ('barcode_unique', 'unique(barcode_ids)', "A barcode can only be assigned to one product !"),
    # ]

    _sql_constraints = [
        ('reference_unique', 'unique(default_code)', "Internal reference can only be assigned to one product !"),
    ]

    def _compute_get_exist_in_pos(self):
        for product in self:
            product.x_exist_in_pos = product.product_variant_id.x_exist_in_pos

    def _set_exist_in_pos(self):
        for product in self:
            product.product_variant_id.x_exist_in_pos = product.x_exist_in_pos


    @api.onchange('minimum_cal_number', 'minimum_cal_type')
    def price_minimum_get(self):
        for template in self:
            if template.minimum_cal_type == 'bd':
                template.price_minimum = template.standard_price + template.minimum_cal_number
            elif template.minimum_cal_type == 'percent':
                template.price_minimum = template.standard_price + (
                        template.standard_price * (template.minimum_cal_number / 100))

    @api.depends('product_variant_ids', 'product_variant_ids.price_minimum', 'product_variant_ids.minimum_cal_type', 'product_variant_ids.minimum_cal_number')
    def _compute_msp(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.price_minimum = template.product_variant_ids.price_minimum
            template.minimum_cal_number = template.product_variant_ids.minimum_cal_number
            template.minimum_cal_type = template.product_variant_ids.minimum_cal_type
            template.price_minimum_get()
        for template in (self - unique_variants):
            template.price_minimum = 0.0
            template.minimum_cal_number = 0.0
            template.minimum_cal_type = 'percent'
            template.price_minimum_get()

    def _set_msp_values(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.price_minimum = template.price_minimum
                template.product_variant_ids.minimum_cal_number = template.minimum_cal_number
                template.product_variant_ids.minimum_cal_type = template.minimum_cal_type
                template.product_variant_ids.price_minimum_get()



    def _compute_get_barcode(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.barcode_ids = template.product_variant_ids.barcode_ids

    def _compute_set_barcode(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.barcode_ids = template.barcode_ids



    @api.constrains('barcode', 'barcode_ids')
    def unique_barcode(self):
        for record in self:
            base_barcode = record.barcode
            for bar in record.barcode_ids:
                if base_barcode == bar.name:
                    raise Warning('A barcode can only be assigned to one product !')
                product = self.env['product.template'].search([('barcode', '=', bar.name)])
                if len(product) > 0:
                    raise Warning('A barcode can only be assigned to one product !')
            bar_line = self.env['multi.product.barcode'].search([('name', '=', record.barcode)])
            if len(bar_line) > 0:
                raise Warning('A barcode can only be assigned to one product !')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('name', operator, name), ('default_code', operator, name), '|', '|',
                      ('barcode', operator, name), ('barcode_ids', operator, name),
                      ('product_variant_ids.barcode_ids', operator, name)]
        product_id = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(product_id).name_get()

    @api.onchange('barcode_ids')
    def validate_updated(self):
        for barcode in self.mapped('barcode_ids'):
            if barcode.check:
                if barcode.check != barcode.name:
                    raise Warning('you cannot edit a barcode. You have to erase it and add the new barcode')
            elif barcode.name:
                barcode.check = barcode.name

    def random_barcode_generate(self):
        for product in self:
            random = "".join(choice(digits) for i in range(6))
            product.barcode = '%s%s' % (product.categ_id.x_category_code or '', random)

    # def ask_barcode_generate(self):
    #     return 1


class ProductTemplate(models.Model):
    _inherit = "product.product"

    barcode_ids = fields.One2many('multi.product.barcode', 'product_id', string="Barcodes", store=True)
    price_minimum = fields.Float(string="Minimum Sale Price")
    minimum_cal_type = fields.Selection([('bd', 'BD'), ('percent', '%')], default='percent')
    minimum_cal_number = fields.Float(string='Minimum Margin')
    x_exist_in_pos = fields.Boolean(string="Exist in POS")

    # _sql_constraints = [
    #     ('product_barcode_unique', 'unique(barcode_ids)', "A barcode can only be assigned to one product !"),
    # ]

    @api.onchange('minimum_cal_number', 'minimum_cal_type')
    def price_minimum_get(self):
        for template in self:
            if template.minimum_cal_type == 'bd':
                template.price_minimum = template.standard_price + template.minimum_cal_number
            elif template.minimum_cal_type == 'percent':
                template.price_minimum = template.standard_price + (
                        template.standard_price * (template.minimum_cal_number / 100))

    @api.constrains('barcode', 'barcode_ids')
    def _check_something(self):
        for record in self:
            base_barcode = record.barcode
            for bar in record.barcode_ids:
                if base_barcode == bar.name:
                    raise Warning('A barcode can only be assigned to one product !')
                product = self.env['product.product'].search([('barcode', '=', bar.name)])
                if len(product) > 0:
                    raise Warning('A barcode can only be assigned to one product !')
            bar_line = self.env['multi.product.barcode'].search([('name', '=', record.barcode)])
            if len(bar_line) > 0:
                raise Warning('A barcode can only be assigned to one product !')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('name', operator, name), ('default_code', operator, name), '|', '|',
                      ('barcode', operator, name), ('barcode_ids', operator, name),
                      ('product_tmpl_id.barcode_ids', operator, name)]
        product_id = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(product_id).name_get()

    @api.onchange('barcode_ids')
    def validate_updated(self):
        for barcode in self.mapped('barcode_ids'):
            if barcode.check:
                if barcode.check != barcode.name:
                    raise Warning('you cannot edit a barcode. You have to erase it and add new barcode')
            elif barcode.name:
                barcode.check = barcode.name

    def random_barcode_generate(self):
        for product in self:
            random = "".join(choice(digits) for i in range(6))
            product.barcode = '%s%s' % (product.categ_id.x_category_code or '', random)

    # def ask_barcode_generate(self):
    #     return 1

    @api.model
    def get_all_products_by_barcode(self):
        products = self.env['product.product'].search_read(
            [('barcode', '!=', None), ('type', '!=', 'service')],
            ['barcode', 'display_name', 'uom_id', 'tracking']
        )
        products_ids = self.env['product.product'].search(
            [('barcode', '!=', None), ('type', '!=', 'service')])

        # product_tmp = self.env['product.template'].search_read(
        #     [('barcode', '!=', None), ('type', '!=', 'service')],
        #     ['barcode', 'display_name', 'uom_id', 'tracking']
        # )

        barcode = self.env['multi.product.barcode'].search(['|', ('product_tmp_id', 'in', products_ids.ids), ('product_id', 'in', products_ids.ids)])

        packagings = self.env['product.packaging'].search_read(
            [('barcode', '!=', None), ('product_id', '!=', None)],
            ['barcode', 'product_id', 'qty']
        )

        # for each packaging, grab the corresponding product data
        to_add = []
        to_read = []
        barcode_ids = []
        products_by_id = {product['id']: product for product in products}
        #print(products_by_id, 'products_by_id')
        for packaging in packagings:
            if products_by_id.get(packaging['product_id']):
                product = products_by_id[packaging['product_id']]
                to_add.append(dict(product, **{'qty': packaging['qty']}))
            # if the product doesn't have a barcode, you need to read it directly in the DB
            to_read.append((packaging, packaging['product_id'][0]))
        products_to_read = self.env['product.product'].browse(list(set(t[1] for t in to_read))).sudo().read(
            ['display_name', 'uom_id', 'tracking'])
        products_to_read = {product['id']: product for product in products_to_read}

        to_add.extend([dict(t[0], **products_to_read[t[1]]) for t in to_read])
        # for barcode in barcode:
        #     for product in products:
        #         if product['id'] == barcode.product_tmp_id.id or product['id'] == barcode.product_id.id:
        #             barcode_ids.append(
        #                 {'id': product['id'], 'barcode': barcode.name, 'display_name': product['display_name'],
        #                  'uom_id': product['uom_id'], 'tracking': product['tracking']})
        for barcode in barcode:
            if products_by_id.get(barcode['product_id']['id'] or barcode['product_tmp_id']['id']):
                parcode = products_by_id.get(barcode['product_id']['id'] or barcode['product_tmp_id']['id'])
                barcode_ids.append(
                    {'id': parcode['id'], 'barcode': barcode.name, 'display_name': parcode['display_name'],
                     'uom_id': parcode['uom_id'], 'tracking': parcode['tracking']})
            # for product_tmps in product_tmp:
            #     if product_tmps['id'] == barcode.product_tmp_id.id or product_tmps['id'] == barcode.product_id.id:
            #         barcode_ids.append(
            #             {'id': product_tmps['id'], 'barcode': barcode.name, 'display_name': product_tmps['display_name'],
            #              'uom_id': product_tmps['uom_id'], 'tracking': product_tmps['tracking']})
            # print(barcode_ids, 'barcode_ids')
        return {product.pop('barcode'): product for product in products + to_add + barcode_ids}


class MultiBarcode(models.Model):
    _name = 'multi.product.barcode'
    _description = 'Multi Product Barcode'

    name = fields.Char(string='Barcode')
    reference = fields.Char(string="Reference")
    check = fields.Char()
    product_id = fields.Many2one('product.product')
    product_tmp_id = fields.Many2one('product.template')

    _sql_constraints = [
        ('multi_barcode_unique', 'unique(name)', "A barcode can only be assigned to one product !"),
    ]


class ProductCategory(models.Model):
    _inherit = 'product.category'

    x_category_code = fields.Char(string="Code")
