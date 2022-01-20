from ast import literal_eval
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
import json
import logging
import pytz
import uuid
import math

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class SplitInspectionWorksheet(models.Model):
    _name = 'split.inspection.worksheet'
    _description = 'Split Inspection Worksheet Template'
    # _order = 'start_datetime,id desc'
    # _rec_name = 'status'

    def _x_compute_name(self):
        for rec in self:
            if rec.x_task_id.sale_order_id:
                rec.name = 'Worksheet Of ' + rec.x_task_id.sale_order_id.name
            else:
                rec.name = 'No S.O. Worksheet'

    name = fields.Char('Name', compute=_x_compute_name)
    x_task_id = fields.Many2one('project.task', string="Task", copy=False)
    x_crm_id = fields.Many2one('crm.lead', string="Opportunity", copy=False, related='x_task_id.x_crm_id')
    x_sale_id = fields.Many2one('sale.order', string="Sale Ref.", copy=False, related='x_task_id.sale_order_id')
    x_partner_id = fields.Many2one('res.partner', string="Customer", copy=False, related='x_task_id.partner_id')
    x_technician_id = fields.Many2one('logistics.team', string="Visited by", related='x_task_id.x_team_id')
    x_phone = fields.Char(string="Phone", related='x_partner_id.phone')
    x_mobile = fields.Char(string="Mobile", related='x_partner_id.mobile')
    x_technician_Supervisor_id = fields.Many2one('res.users', string="Sales Person", related='x_task_id.user_id')
    x_date_inspected = fields.Date(string='Date Of Inspection', default=fields.Date.today())
    x_split_tonnage_line = fields.One2many('split.tonnage.line', 'x_worksheet_id', string='Split tonnage needed')


class SplitTonnageLine(models.Model):
    _name = 'split.tonnage.line'
    _description = 'Split tonnage needed for each room'

    @api.depends('sequence')
    def _compute_x_product_id_domain(self):
        task_id = self._context.get('task_id')
        product_ids = self.env['project.task'].browse(task_id).project_id.x_product_ids
        self.x_product_id_domain = product_ids

    sequence = fields.Integer(default=10)
    x_worksheet_id = fields.Many2one('split.inspection.worksheet', string="Worksheet")
    x_room_id = fields.Many2one('location.room', string="Room")
    x_floor_id = fields.Many2one('location.floor', string="Floor")
    x_length = fields.Float(string="Length")
    x_width = fields.Float(string="Width")
    x_area = fields.Float(string="Area", compute='compute_x_area')
    x_tonnage = fields.Float(string="Tonnage", compute='compute_x_tonnage')
    x_recommended_tonnage = fields.Float(string="Recommended Tonnage", compute='compute_x_recommended_tonnage')
    x_product_id = fields.Many2one('product.product', string="Bracket Type")
    x_product_id_domain = fields.Many2many('product.product', string="Product", compute=_compute_x_product_id_domain)
    x_qty = fields.Integer('Qty')
    x_extra_pipe = fields.Float(string="Extra Pipe")


    @api.depends('x_length', 'x_width')
    def compute_x_area(self):
        for rec in self:
            rec.x_area = rec.x_length * rec.x_width

    @api.depends('x_area')
    def compute_x_tonnage(self):
        for rec in self:
            rec.x_tonnage = (rec.x_area * 105 * 10.7639)/12000

    @api.depends('x_tonnage')
    def compute_x_recommended_tonnage(self):
        for rec in self:
            tons = (math.ceil(rec.x_tonnage * 2))/2
            rec.x_recommended_tonnage = tons


class LocationRoom(models.Model):
    _name = 'location.room'
    _description = 'Room'

    name = fields.Char('Name')

class LocationFloor(models.Model):
    _name = 'location.floor'
    _description = 'Floor'

    name = fields.Char('Name')


