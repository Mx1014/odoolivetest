# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning


class premises(models.Model):
    _name = 'permises.permises'

    premise_id = fields.Char(required=True, string="Premise ID")
    name = fields.Char(required=True, string="Name")
    area = fields.Char(string="Area")
    request_list3_counter = fields.Integer(compute='_display_count3', string="Request")
    equipments_list4_counter = fields.Integer(compute='_display_count4', string="Equipments")
    sub_location_list_counter = fields.Integer(compute='_display_count5', string="Sub Location")

    def _display_count3(self):
        for rel in self:
            count_id = self.env['maintenance.request'].search_count([('premise_related', '=', rel.id)])
            self.request_list3_counter = count_id

    def _display_count4(self):
        for rel in self:
            count_id = self.env['maintenance.equipment'].search_count([('premise', '=', rel.id)])
            self.equipments_list4_counter = count_id

    def _display_count5(self):
        for rel in self:
            count_id = self.env['sub.location'].search_count([('premise', '=', rel.id)])
            self.sub_location_list_counter = count_id

    def request_list(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Request'),
            'domain': [('premise_related.name', '=', self.name)],
            'res_model': 'maintenance.request',
            'view_mode': 'tree,form',
        }

    def equipments_list(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Equipments'),
            'domain': [('premise', '=', self.name)],
            'res_model': 'maintenance.equipment',
            'view_mode': 'tree,form',
        }

    def sub_location_list(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sub_locations'),
            'domain': [('premise', '=', self.name)],
            'res_model': 'sub.location',
            'view_mode': 'tree,form',
        }


class sublocation(models.Model):
    _name = 'sub.location'

    sublocation_name = fields.Char(required=True, string="Sub-Location name")
    name = fields.Char(string="Name", compute='compute_name', readonly=True, store=True)
    premise = fields.Many2one('permises.permises', required=True, string="Premise")
    x_floor = fields.Many2one('floor.list', required=True, string="Floor")
    room = fields.Char(string="Reference", required=True)
    request_list2_counter = fields.Integer(compute='_display_count', string="Request")
    equipments_list2_counter = fields.Integer(compute='_display_count2', string="Equipments")

    def compute_name(self):
        for rec in self:
            rec.name = str(rec.room) + " " + str(rec.x_floor.name) + " " + str(rec.sublocation_name)

    def _display_count(self):
        for rel in self:
            count_id = self.env['maintenance.request'].search_count([('sub_location_related', '=', rel.id)])
            self.request_list2_counter = count_id

    def _display_count2(self):
        for rel in self:
            count_id = self.env['maintenance.equipment'].search_count([('sub_location', '=', rel.id)])
            self.equipments_list2_counter = count_id

    def request_list2(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Request'),
            'domain': [('sub_location_related', '=', self.id)],
            'res_model': 'maintenance.request',
            'view_mode': 'tree,form',
        }

    def equipments_list2(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Equipments'),
            'domain': [('sub_location', '=', self.id)],
            'res_model': 'maintenance.equipment',
            'view_mode': 'tree,form',
        }


class pobs_maintenance(models.Model):
    _inherit = 'maintenance.equipment'

    reference = fields.Char(string='Reference', readonly=True, default='New')

    replaceable = fields.Boolean(string='Quantity applicable')
    quantity = fields.Integer(string='Quantity')
    premise = fields.Many2one('permises.permises', required=True)
    sub_location = fields.Many2one('sub.location', required=True)
    unit_cost = fields.Float(string='Unit Cost')

    ip_address = fields.Char(string="IP Address")
    username = fields.Char(string='Username / Email')
    password = fields.Char(string='Password')
    is_ip = fields.Boolean(related='category_id.is_ip')
    is_login = fields.Boolean(related='category_id.is_login')
    parent_category = fields.Many2one(related='category_id.parent_id', store=True)
    completeName = fields.Char(related='category_id.completeName', store=True)

    def create_maintenance_request(self):
        print(self._context.get('active_id'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.request',
            'view_mode': 'form',
            'context': {'default_equipment_id': self.id}
        }

    @api.onchange('premise')
    def onchange_premise_name(self):
        for each in self:
            return {"domain": {'sub_location': [('premise', '=', each.premise.id)]}}

    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            maintenance = self.env['maintenance.equipment.category'].browse(vals.get('category_id'))
            if maintenance and maintenance.sequence:
                vals['reference'] = maintenance.sequence.next_by_id() or _('New')
        result = super(pobs_maintenance, self).create(vals)
        return result

    @api.onchange('unit_cost', 'quantity')
    def compute_total(self):
        if self.quantity:
            self.cost = self.unit_cost * self.quantity

   # @api.constrains('quantity')
    #def check_quantity(self):
        #res = {}
        #if self.quantity_check < self.quantity:
            #raise UserError('The quantity is larger and the capacity of the place.')
        #elif self.quantity == 0:
            #raise UserError('Please add quantity.')
        #return res


class maintenance_edit(models.Model):
    _inherit = 'maintenance.request'

    name = fields.Char(string='Reference', readonly=True, default='New')

    premise_related = fields.Many2one(related='equipment_id.premise')
    sub_location_related = fields.Many2one(related='equipment_id.sub_location')
    quantity_check = fields.Integer(related='equipment_id.quantity')
    quantity = fields.Integer(string='Quantity')
    solution = fields.Char(string='Solution')
    issue = fields.Many2one('maintenance.issue', string='Issue')
    issue_list = fields.Many2many(related='category_id.issue', string='issue list')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            maintenance = self.env['maintenance.team'].browse(vals.get('maintenance_team_id'))
            if maintenance and maintenance.sequence:
                vals['name'] = maintenance.sequence.next_by_id() or _('New')
        result = super(maintenance_edit, self).create(vals)
        return result




class floor_list(models.Model):
    _name = 'floor.list'

    name = fields.Char(string="Floor", required=True)
