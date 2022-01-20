from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning
from random import choice
from string import digits
from odoo.osv import expression
import re
import phonenumbers
from lxml import etree


# from odoo.addons.phone_validation.tools import phone_validation


class ResPartner(models.Model):
    _inherit = 'res.partner'
    # name = fields.Char(compute='get_partner_name_test', string="name", store=True, index=True)
    # overriding old fields
    property_payment_term_id = fields.Many2one('account.payment.term', company_dependent=True,
                                               string='Customer Payment Terms', tracking="1", domain=[('payment_term_type', 'in', ['so', 'both'])],
                                               help="This payment term will be used instead of the default one for sales orders and customer invoices")
    property_purchase_currency_id = fields.Many2one(
        'res.currency', string="Supplier Currency", company_dependent=True, tracking="1",
        default=lambda self: self.env['res.currency'].search([('name', '=', 'BHD')]),
        help="This currency will be used, instead of the default one, for purchases from the current partner")
    industry_id = fields.Many2one('res.partner.industry', 'Industry', tracking="1")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', tracking="1")
    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'), ('company', 'Company')],
                                    compute='_compute_company_type', inverse='_write_company_type', tracking="1")
    street_number = fields.Char('House', compute='_split_street', help="House Number",
                                inverse='_set_street', store=True, tracking="1")
    city_id = fields.Many2one('res.city', string='City of Address', tracking="1")
    street_name = fields.Char('Street Name', compute='_split_street',
                              inverse='_set_street', store=True, tracking="1")
    vat = fields.Char(string='Tax ID', tracking="1",
                      help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.")
    email = fields.Char(tracking="1")
    phone = fields.Char(tracking="1")
    x_whatsapp_mobile = fields.Char(string='Mobile', tracking="1")
    mobile = fields.Char(tracking="1", string='Whatsapp Number')
    name = fields.Char(index=True, tracking="1")
    credit_limit = fields.Float(string='Credit Limit', tracking="1")
    property_supplier_payment_term_id = fields.Many2one('account.payment.term', company_dependent=True,
                                                        string='Vendor Payment Terms', tracking="1", domain=[('payment_term_type', 'in', ['po', 'both'])],
                                                        help="This payment term will be used instead of the default one for purchase orders and vendor bills")
    title = fields.Many2one('res.partner.title', tracking="1")
    type = fields.Selection(
        [('contact', 'Contact'),
         ('invoice', 'Invoice Address'),
         ('delivery', 'Delivery Address'),
         ('other', 'Other Address'),
         ("private", "Private Address"),
         ], string='Address Type',
        default='contact', tracking="1",
        help="Invoice & Delivery addresses are used in sales orders. Private addresses are only visible by authorized users.")
    # zone = fields.Char('Zone', tracking="1")
    # adding new fields
    x_first_name = fields.Char(string="First Name")
    x_mid_name = fields.Char(string="Middle Name")
    x_last_name = fields.Char(string="Last Name")

    x_tax_treatment = fields.Boolean(string="Registered For VAT ?", tracking="1")
    x_third_party = fields.Boolean(string="Third party")

    x_mobile = fields.Char(string="Mobile2", tracking="1")  # method to accept no only

    x_cpr = fields.Char(string="CPR", size=9, tracking="1")  # constrains to check for uniqunce
    x_cr = fields.Char(string="CR", tracking="1")  # constrains to check for uniqunce

    x_is_vendor = fields.Boolean(string="Vendor", compute="is_vendor", force_save=True, readonly=False, tracking="1")
    x_is_customer = fields.Boolean(string="Customer", compute="is_customer", force_save=True, readonly=False,
                                   tracking="1")
    # x_is_employee = fields.Boolean(string="Employee", tracking="1")

    x_credit_customer = fields.Boolean(string="Credit Customer", tracking="1")

    x_credit_limit = fields.Float(string="Vendor Credit Limit", tracking="1")

    x_code = fields.Char(string="Code")  # auto generate code
    x_flat = fields.Char(string="Flat", tracking="1")
    x_gate = fields.Char(string="Gate", tracking="1")
    x_address_road = fields.Many2one('city.road', string="Road", tracking="1")
    x_address_block = fields.Many2one('city.block', string="Block", tracking="1")
    x_zone_id = fields.Many2one('res.zone', string='Zone')
    x_block_area = fields.Char(related="x_address_block.block_area")
    x_other_address = fields.Char(string="Other Address")
    x_delivery_count = fields.Integer('Deliveries', compute='_compute_delivery_count')

    _sql_constraints = [
        ('unique_cpr', 'UNIQUE(x_cpr)', 'Cannot accept the CPR No. because the same No. already created'),
        ('unique_cr', 'UNIQUE(x_cr)', 'Cannot accept the CR No. because the same No. already created'),
        ('unique_code', 'UNIQUE(x_code)', 'Code already created')
    ]

    # @api.constrains('email')
    # def show_email_warning(self):
    #     for partner in self:
    #        if not partner.email:
    #           return {'warning': {'title': "Warning", 'message': "You Are Saving Without Email !!"}}

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ResPartner, self).create(vals_list)
        random = "".join(choice(digits) for i in range(6))
        if not res.x_code:
            res.x_code = random
        # if self.x_is_customer:
        #     if self.x_credit_customer:
        #         if self.credit_limit == 0.0:
        #             raise UserError(_('The Amount Of Credit Limit is Zero'))
        return res

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        # if self.x_is_customer:
        #     if self.x_credit_customer:
        #         if self.credit_limit == 0.0:
        #             raise UserError(_('The Amount Of Credit Limit is Zero'))
        return True

    @api.onchange('x_credit_customer')
    def set_default_payment_term_credit(self):
        if self.x_credit_customer:
            self.property_payment_term_id = 0
        else:
            self.property_payment_term_id = self.env['account.payment.term'].search([('name', '=', 'Immediate Payment'), ('payment_term_type', 'in', ['so', 'both'])])

    # if self.company_type == 'person' and self.x_credit_customer:
    #     self.industry_id = self.env['res.partner.industry'].search([('name', '=', 'Individual')])

    @api.onchange('is_company')
    def reset_on_company_type_change(self):
        # self.name = None
        self.x_first_name = None
        self.x_mid_name = None
        self.x_last_name = None
        # if self.is_company:
        #     self.industry_id = None

    @api.onchange('x_first_name', 'x_mid_name', 'x_last_name')
    def get_partner_name_test(self):
        if not self.is_company:
            self.name = (self.x_first_name or '') + ' ' + (self.x_mid_name or '') + ' ' + (self.x_last_name or '')

    @api.onchange('x_credit_customer', 'company_type')
    def set_industry_if_company_change(self):
        if self.company_type == 'person':
            if self.x_credit_customer:
                self.industry_id = self.env['res.partner.industry'].search([('name', '=', 'Individual')])
            elif not self.x_credit_customer:
                self.industry_id = None
        # elif self.company_type == 'person' and not self.x_credit_customer:
        #     self.industry_id = None

        if self.is_company and self.industry_id == self.env['res.partner.industry'].search(
                [('name', '=', 'Individual')]):
            self.industry_id = None

    # @api.constrains('x_mobile','phone','mobile')
    # def _check_mobile(self):
    #     validate = re.compile(r'[0-9()+ ]*$')
    #     for partner in self:
    #         if partner.x_mobile:
    #             if not validate.match(partner.x_mobile):
    #                 raise ValidationError(_("Mobile2 No. must contains only digits"))
    #         if partner.mobile:
    #             if not validate.match(partner.mobile):
    #                 raise ValidationError(_("Mobile No. must contains only digits"))
    #         if partner.phone:
    #             if not validate.match(partner.phone):
    #                 raise ValidationError(_("Phone No. must contains only digits"))

    @api.constrains('x_mobile', 'phone', 'mobile')
    def _check_mobile(self):
        for partner in self:
            if partner.x_mobile:
                partner.phone_check(partner.x_mobile)
            if partner.mobile:
                partner.phone_check(partner.mobile)
            if partner.phone:
                partner.phone_check(partner.phone)

    def phone_check(self, number):
        country_code = self.country_id.code if self.country_id and self.country_id.code else None
        try:
            phone_nbr = phonenumbers.parse(number, region=country_code, keep_raw_input=True)
        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise UserError(_('Unable to parse %s: %s') % (number, str(e)))
        if not phonenumbers.is_possible_number(phone_nbr):
            raise UserError(_('Impossible number %s: probably invalid number of digits') % number)
        if not phonenumbers.is_valid_number(phone_nbr):
            raise UserError(_('Invalid number %s') % number)

    @api.constrains('vat')
    def _check_vat(self):
        for partner in self:
            if partner.vat:
                if not partner.vat.isdigit():
                    raise ValidationError(_("VAT No. must contains only digits"))
                print(len(partner.vat))
                if len(partner.vat) > 15 or len(partner.vat) < 15:
                    raise ValidationError(_("Invalid VAT No., must contains only 15 digits only"))

    def code_generator(self):
        for partner in self:
            random = "".join(choice(digits) for i in range(6))
            partner.x_code = random

    # @api.onchange('x_address_block')
    # def onchange_block(self):
    #     for partner in self:
    #         partner['city'] = partner.x_address_block.state_id.name

    @api.onchange('name', 'company_type')
    def default_country(self):
        for country in self:
            if country.company_type == 'person':
                country.country_id = country.env['res.country'].search([('name', '=', 'Bahrain')])

    @api.depends('supplier_rank', 'x_is_vendor')
    def is_vendor(self):
        for all in self:
            if all.supplier_rank != 0:
                all.x_is_vendor = True
            else:
                all.x_is_vendor = False

    @api.depends('customer_rank', 'x_is_customer')
    def is_customer(self):
        for all in self:
            if all.customer_rank != 0:
                all.x_is_customer = True
            else:
                all.x_is_customer = False

    @api.onchange('x_is_customer', 'x_is_vendor', )
    def onchange_rank(self):
        for test in self:
            if test.x_is_customer == False and test.customer_rank == 1:
                test.customer_rank = 0
            elif test.x_is_customer == True and test.customer_rank == 0:
                test.customer_rank = 1
            if test.x_is_vendor == False and test.supplier_rank == 1:
                test.supplier_rank = 0
            elif test.x_is_vendor == True and test.supplier_rank == 0:
                test.supplier_rank = 1

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            number = False
            if ' ' not in name:
                number = name[:4] + ' ' + name[4:]
            domain = ['|', '|', '|', '|', '|', '|', '|', ('name', operator, name), ('phone', operator, number or name),
                      ('mobile', operator, number or name), ('x_mobile', operator, name),
                      ('email', operator, name), ('x_code', operator, name), ('x_cpr', operator, number or name),
                      ('x_cr', operator, name)]
        partner_id = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(partner_id).name_get()

    def _display_address(self, without_company=False):

        address_format = self._get_address_format()
        args = {
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self._get_country_name(),
            'company_name': self.commercial_company_name or '',
            'x_flat': self.x_flat or '',
            'x_gate': self.x_gate or '',
            'x_block_area': self.x_block_area or '',
            'x_zone_id': self.x_zone_id.name or '',
            'x_other_address': self.x_other_address or '',
            'x_code': self.x_code or '',
        }
        for field in self._formatting_address_fields():
            args[field] = getattr(self, field) or ''
        if without_company:
            args['company_name'] = ''
        elif self.commercial_company_name:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args

    @api.onchange('x_address_block', 'x_address_road')
    def address_combine(self):
        res = {}
        for address in self:
            city = self.env['res.city'].search([('x_block_id', '=', address.x_address_block.id)], limit=1)
            address.city_id = city.id
            address.x_zone_id = city.x_zone_id.id
            address.street_name = 'Rd %s, B %s' % (address.x_address_road.name, address.x_address_block.name)
            res['domain'] = {'x_address_road': [('id', 'in', address.x_address_block.road_id.ids)]}

            if address.x_address_road.id not in address.x_address_block.road_id.ids:
                address.x_address_road = False
        return res

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ResPartner, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                       submenu=submenu)
        if view_type == 'form' and view_id == self.env.ref('base.view_partner_form').id:
            print(view_id)
            doc = etree.XML(res['arch'])
            node = doc.xpath("//field[@name='city_id']")[0]
            print(node)
            node.set('options', "{'no_create': True}")
            res['arch'] = etree.tostring(doc)

        return res

    def action_view_delivery(self):
        delivery = self.env['stock.picking'].search([('partner_id', '=', self.id)])
        return {
            'name': _('Delivery'),
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('stock.vpicktree').id, 'tree'),
                (self.env.ref('stock.view_picking_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', delivery.ids)],
        }

    def _compute_delivery_count(self):
        for picking in self:
            picking.x_delivery_count = self.env['stock.picking'].search_count([('partner_id', '=', self.id)])


class Country(models.Model):
    _inherit = 'res.country'

    address_format = fields.Text(string="Layout in Reports",
                                 help="Display format to use for addresses belonging to this country.\n\n"
                                      "You can use python-style string pattern with all the fields of the address "
                                      "(for example, use '%(street)s' to display the field 'street') plus"
                                      "\n%(state_name)s: the name of the state"
                                      "\n%(state_code)s: the code of the state"
                                      "\n%(country_name)s: the name of the country"
                                      "\n%(country_code)s: the code of the country",
                                 default='%(x_zone_id)s\n%(street)s\n%(street2)s\n%(x_flat)s\n%(city)s/%(x_block_area)s %(state_code)s %(zip)s\n%(country_name)s\n%(x_other_address)s')


class Reszone(models.Model):
    _name = 'res.zone'
    _description = 'Zone Address'

    name = fields.Char(string="Zone")


class CityBlock(models.Model):
    _name = 'city.block'
    _description = 'City Block'

    name = fields.Char(string="Block")
    road_id = fields.Many2many('city.road', string="Road", widget="many2many_tags")
    block_area = fields.Char(string="Block Area")


class CityRoad(models.Model):
    _name = 'city.road'
    _description = 'City Road'

    name = fields.Char(string="Road")


class Rescity(models.Model):
    _inherit = 'res.city'

    x_zone_id = fields.Many2one('res.zone', string="Zone")
    x_block_id = fields.Many2many('city.block', string="Block")
