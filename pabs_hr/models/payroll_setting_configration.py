from odoo import fields, models, api, _


class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_annual_leave_provision_account = fields.Many2one('account.account', string="Annual Leave Provision",
                                                             default_model='provision.adjustment')
    default_annual_leave_expense_account = fields.Many2one('account.account', string="Annual Leave Expense",
                                                           default_model='provision.adjustment')
    default_indemnity_leave_provision_account = fields.Many2one('account.account',
                                                                string="Indemnity Provision Account",
                                                                default_model='provision.adjustment')
    default_indemnity_leave_expense_account = fields.Many2one('account.account', string="Indemnity Expense",
                                                              default_model='provision.adjustment')
    default_journal = fields.Many2one('account.journal', string="journal",
                                      default_model='provision.adjustment')
