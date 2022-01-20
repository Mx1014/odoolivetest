from datetime import datetime
from dateutil import relativedelta
from odoo.exceptions import UserError

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_x_repair_project = fields.Many2one('project.project', string="Repair Project", default_model='repair.order')

    # def set_values(self):
    #     res = super(ResConfigSettings, self).set_values()
    #     self.env['ir.config_parameter'].set_param('repair.x_repair_project', self.x_repair_project)
    #     return res
    #
    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     IPCSudo = self.env['ir.config_parameter'].sudo()
    #     project = IPCSudo.get_param('repair.x_repair_project')
    #     res.update(x_repair_project=project)
    #     return res
