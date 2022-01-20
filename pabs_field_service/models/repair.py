from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class Repair(models.Model):
    _inherit = 'repair.order'

    x_problem_suggested_solution_line = fields.One2many('problem.recommended.solution.line', 'x_repair_id',
                                                        string='Problems & Recommended Solutions')

    x_sale_service_type = fields.Selection([('cash', 'Cash Service'), ('credit', 'Credit Service')], string="Service Type",
                                      default="cash", tracking=1, copy=False)

    def service_type_action(self):
        for sale in self:
            sale.x_sale_service_type = 'credit'

    #x_user_statement_id = fields.Many2one('account.user.statement', copy=False, string="User Statement")

class AccountMoves(models.Model):
    _inherit = 'account.move'

    x_sale_service_type = fields.Selection([('cash', 'Cash Service'), ('credit', 'Credit Service')],
                                           string="Service Type", copy=False)
