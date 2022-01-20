from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_is_zero
from odoo.tools import float_compare, float_round, float_repr
from odoo.tools.misc import formatLang, format_date
from odoo.exceptions import UserError, ValidationError


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"
    x_users = fields.Many2many('res.users', string="Allowed Users")
