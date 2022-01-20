from odoo import fields, models, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    default_x_purchase_journal = fields.Many2one('account.journal', string="Purchase Journal", default_model='account.move', domain=[('type','=','purchase')])
    default_x_payroll_account = fields.Many2one('account.account', string="Payroll Payable Account",
                                                 default_model='account.move.line', domain=[('user_type_id.type', '=', 'payable')])