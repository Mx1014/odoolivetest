from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import date
from datetime import timedelta
from datetime import datetime
import dateutil


class PaymentType(models.Model):
    _name = 'settlement.type'

    name = fields.Char(string='Description')
    x_payable_account = fields.Many2one('account.account', string='Payable Account')
    x_air_ticket_account = fields.Many2one('account.account', string='Air Ticket Account')
    x_annual_leave_account = fields.Many2one('account.account', string='Annual Leave Account')
    x_indemnity_account = fields.Many2one('account.account', string='Indemnity Account')
    x_overtime_account = fields.Many2one('account.account', string='Overtime Account')
    is_settlement = fields.Boolean(string='is Settlement')
    is_encashment = fields.Boolean(string='is Encashment')
    is_vacation_payment = fields.Boolean(string='is Vacation Payment')
    journal_id = fields.Many2one('account.journal', 'Journal', required=True,
                                 default=lambda self: self.env['account.journal'].search([('type', '=', 'general')],
                                                                                         limit=1))
    x_sequence_id = fields.Many2one('ir.sequence', string='Reference Sequence')
