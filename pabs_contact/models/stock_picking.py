from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning
from random import choice
from string import digits
from odoo.osv import expression


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _compute_x_address(self):
        for rec in self:
            address = ''
            if rec.partner_id:
                if rec.partner_id.street_number:
                    address += 'House: ' + rec.partner_id.street_number
                if rec.partner_id.x_address_block.name:
                    address += ', Block: ' + rec.partner_id.x_address_block.name
                if rec.partner_id.x_address_road.name:
                    address += ', Road: ' + rec.partner_id.x_address_road.name
                if rec.partner_id.x_block_area:
                    address += ', Area: ' + rec.partner_id.x_block_area
                if rec.partner_id.x_flat:
                    address += ', Flat: ' + rec.partner_id.x_flat
                if rec.partner_id.x_gate:
                    address += ', Gate: ' + rec.partner_id.x_gate
                if rec.partner_id.city:
                    address += ', City: ' + rec.partner_id.city
                if rec.partner_id.state_id.name:
                    address += ', State: ' + rec.partner_id.state_id.name
                if rec.partner_id.zip:
                    address += ', Zip: ' + rec.partner_id.zip
            if address:
                rec.x_address = address
            else:
                rec.x_address = False

    def _compute_x_mobile(self):
        for rec in self:
            mobile = ''
            if rec.partner_id:
                if rec.partner_id.phone:
                    mobile += str(rec.partner_id.phone) + '/ '
                if rec.partner_id.mobile:
                    mobile += str(rec.partner_id.mobile) + '/ '
                if rec.partner_id.x_mobile:
                    mobile += str(rec.partner_id.x_mobile)
            rec.x_mobile = mobile

    x_address = fields.Text('Address', compute=_compute_x_address)
    x_house = fields.Char(string='House', related='partner_id.street_number', store=1)
    x_road = fields.Many2one('city.road', string='Road', related='partner_id.x_address_road', store=1)
    x_block = fields.Many2one('city.block', string='Block', related='partner_id.x_address_block', store=1)
    x_city = fields.Char(string='City', related='partner_id.city', store=1)
    x_zone = fields.Many2one('res.zone', string='Zone', related='partner_id.x_zone_id', store=1)
    x_mobile = fields.Char(string='Mobile', compute=_compute_x_mobile)
