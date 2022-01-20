# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    payment_term_type = fields.Selection([
        ('so', 'Sale Order'),
        ('po', 'Purchase Order'),
        ('both', 'Both'),
    ], string='Type', default='both', required=True)
