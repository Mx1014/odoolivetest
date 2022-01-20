from ast import literal_eval
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
import json
import logging
import pytz
import uuid

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class SplitServiceWorksheet(models.Model):
    _name = 'split.service.worksheet'
    _description = 'Split Service Worksheet Template'
    # _order = 'start_datetime,id desc'
    # _rec_name = 'status'

    def _x_compute_name(self):
        for rec in self:
            if rec.x_task_id.sale_order_id:
                rec.name = 'Worksheet Of ' + rec.x_task_id.sale_order_id.name
            else:
                rec.name = 'No S.O. Worksheet'

    name = fields.Char('SO', related="x_task_id.sale_order_id.name", store=True)
    x_task_id = fields.Many2one('project.task', string="Task", copy=False)
    x_product_id = fields.Many2one('product.product', string='Product', help="Product concerned by the ticket", related='x_task_id.x_product_id', store=True)
    x_product_default_code = fields.Char('Internal Reference', related='x_product_id.default_code', store=True)
    x_product_brand = fields.Many2one('product.brand', string='Brand', related='x_product_id.product_brand_id', store=True)
    x_product_serial = fields.Char('Product Serial No.')
    x_warranty_id = fields.Many2one('warranty.line', string='Warranty Reference', related='x_task_id.x_warranty_id', store=True)
    x_warranty_expiry_date = fields.Date(string='Warranty End Date', related='x_warranty_id.date_done', store=True)
    x_warranty_extended_expiry_date = fields.Date(string='Extended Warranty End Date',
                                                  related='x_warranty_id.extended_end_date', store=True)
    x_warranty_state = fields.Selection([('Running', 'Running'), ('Extended', 'Extended'), ('Expired', 'Expired')], string='Warranty Status', related='x_warranty_id.state', store=True)
    x_technician_id = fields.Many2one('logistics.team', string="Technician", related='x_task_id.x_team_id', store=True)
    x_technician_Supervisor_id = fields.Many2one('res.users', string="Supervisor", related='x_task_id.user_id', store=True)
    x_date_repaired = fields.Date(string='Date Repaired', default=fields.Date.today())
    x_diagnosis = fields.Text(string='Diagnosis')

    # x_problem_ids = fields.Many2many('repair.problem', string="Problems")
    # x_solution_ids = fields.Many2many('repair.solution', string="Recommended Solutions")
    x_problem_suggested_solution_line = fields.One2many('problem.recommended.solution.line', 'x_worksheet_id', string='Problems & Recommended Solutions')


class ProblemSuggestedSolutionLine(models.Model):
    _name = 'problem.recommended.solution.line'

    x_worksheet_id = fields.Many2one('split.service.worksheet', string="Worksheet")
    x_repair_id = fields.Many2one('repair.order', string="Repair Order")
    x_problem_id = fields.Many2one('repair.problem', string="Problems", requered=1)
    x_problem_solution_ids = fields.Many2many('repair.solution', string="Solutions", related='x_problem_id.x_solution_ids')
    x_solution_ids = fields.Many2many('repair.solution', string="Recommended Solutions", domain="[('id', 'in', x_problem_solution_ids)]")
    x_qty = fields.Float(string="QTY")
