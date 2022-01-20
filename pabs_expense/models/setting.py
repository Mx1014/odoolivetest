from odoo import fields, models, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    default_x_ownwer_journal = fields.Many2one('account.journal', string="Owner Journal", default_model='hr.expense.sheet')