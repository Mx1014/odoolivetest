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


class RepairProblem(models.Model):
    _name = 'repair.problem'
    _description = 'Problems with product'
    # _order = 'start_datetime,id desc'
    # _rec_name = 'status'

    @api.onchange('x_solution_line')
    def _compute_x_solution_ids(self):
        for rec in self:
            rec.x_solution_ids = rec.x_solution_line.mapped('x_solution_id')

    name = fields.Char('Name')
    x_problem_description = fields.Text(string='Problem Description')
    x_solution_line = fields.One2many('problem.solution.line', 'x_problem_id', string='Solutions')
    x_solution_ids = fields.Many2many('repair.solution', string='Solutions', compute=_compute_x_solution_ids)


class RepairSolution(models.Model):
    _name = 'repair.solution'
    _description = 'Solutions for product problems'
    # _order = 'start_datetime,id desc'
    # _rec_name = 'status'

    @api.onchange('x_problem_line')
    def _compute_x_problem_ids(self):
        for rec in self:
            rec.x_problem_ids = rec.x_problem_line.mapped('x_problem_id')

    name = fields.Char('Name')
    x_solution_description = fields.Text(string='Solution Description')
    x_problem_line = fields.One2many('problem.solution.line', 'x_solution_id', string='Problems')
    x_problem_ids = fields.Many2many('repair.problem', string='Problems', compute=_compute_x_problem_ids)



class ProblemSolutionLine(models.Model):
    _name = 'problem.solution.line'
    _description = 'Solutions for product problems'
    # _order = 'start_datetime,id desc'
    _rec_name = 'name'

    def _compute_name(self):
        for rec in self:
            rec.name = rec.x_problem_id.name + '/' + rec.x_solution_id.name

    name = fields.Char('Name', compute=_compute_name)
    x_problem_id = fields.Many2one('repair.problem', string='Problem')
    x_solution_id = fields.Many2one('repair.solution', string='Solution')
