from datetime import timedelta

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.tools.misc import format_date


class Project(models.Model):
    _inherit = 'project.project'

    business_line = fields.Many2one('business.line', 'Business Line', domain="[('business_line_type', '=', 'service')]")
    x_sale_order_type = fields.Selection(string='Sale Order Type', default='cash_memo',
                                         selection=[('cash_memo', 'Cash Memo'), ('credit_sale', 'Credit Sale'),
                                                    ('paid_on_delivery', 'Paid on Delivery'),
                                                    ('advance_payment', 'Cash Invoice'), ('service', 'Service')])

    x_is_not_required = fields.Boolean(string='Invisible Invoice Address ',
                                       help='if The Field Been True Invoice Address will be invisible and required')
    x_product_ids = fields.Many2many('product.product', string='Product', relation='x_product_ids_project_rel')
    x_service_ids = fields.Many2many('product.product', string='Services', relation='x_service_ids_project_rel')
