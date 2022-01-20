from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError, Warning


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_view_closing = fields.Many2one('account.move')

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.type == 'entry':
            print('')
        return res

    def action_vat_closing(self):
        self.ensure_one()
        tax_group = self.env['account.tax'].search([])

        account_payable = tax_group.tax_group_id[0].property_tax_payable_account_id
        account_receivable = tax_group.tax_group_id[0].property_tax_receivable_account_id

        print(self.mapped('line_ids')[len(self.mapped('line_ids')) - 1].account_id.id)
        if self.mapped('line_ids')[len(self.mapped('line_ids')) - 1].account_id.id == account_payable.id:
            id = self.env['account.move'].create({
                # 'ref': self.ref,
                'type': 'in_invoice',
                'partner_id': 6,
                'line_ids': [(0, 0, {'name': account_payable.name,
                                     'price_unit': self.mapped('line_ids')[len(self.mapped('line_ids')) - 1].credit,
                                     'account_id': account_payable.id,
                                     })]
            })
            self.x_view_closing = id
            id.action_post()
        elif self.mapped('line_ids')[len(self.mapped('line_ids')) - 1].account_id.id == account_receivable.id:
            id = self.env['account.move'].create({
                'ref': self.ref,
                'type': 'out_invoice',
                'partner_id': 6,
                'line_ids': [(0, 0, {'name': account_receivable.name,
                                     'price_unit': self.mapped('line_ids')[len(self.mapped('line_ids')) - 1].debit,
                                     'account_id': account_receivable.id,
                                     })]
            })
            self.x_view_closing = id
            id.action_post()

    def action_view_vat_closing(self):
        self.ensure_one()
        if self.x_view_closing.type == 'out_invoice':
            return {
                'name': _('Invoices'),
                'res_model': 'account.move',
                'view_mode': 'form',
                'views': [

                    (self.env.ref('account.view_move_form').id, 'form'),
                ],
                'type': 'ir.actions.act_window',
                'domain': [('type', '=', 'out_invoice')],
                'res_id': self.x_view_closing.id,
            }
        elif self.x_view_closing.type == 'in_invoice':
            return {
                'name': _('Bill'),
                'res_model': 'account.move',
                'view_mode': 'form',
                'views': [
                    (self.env.ref('account.view_move_form').id, 'form'),
                ],
                'type': 'ir.actions.act_window',
                'domain': [('type', '=', 'in_invoice')],
                'res_id': self.x_view_closing.id,
            }


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    x_treatment_type = fields.Selection(
        [('out_of_scope', 'Out of Scope'), ('registered', 'VAT Registered'), ('non_registered', 'Non VAT Registered'),
         ('i_e', 'Import/Export')], string="Treatment Type")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_treatment_type = fields.Selection(related='property_account_position_id.x_treatment_type')
    # x_is_vendor = fields.Boolean(string="Vendor", compute="is_vendor", force_save=True, readonly=False, tracking="1")
    # x_is_customer = fields.Boolean(string="Customer", compute="is_customer", force_save=True, readonly=False,
    #                                tracking="1")

    def get_fiscal_default(self):
            non_register = self.env['account.fiscal.position'].search([('x_treatment_type','=','non_registered')], limit=1)
            return non_register

    property_account_position_id = fields.Many2one('account.fiscal.position', company_dependent=True,
                                                   string="Fiscal Position",
                                                   help="The fiscal position determines the taxes/accounts used for this contact.", default=get_fiscal_default)

    @api.onchange('x_treatment_type', 'property_account_position_id')
    def _onchange_country_id(self):
        res = {}
        if self.x_treatment_type in ['non_registered', 'registered']:
            country = self.env['res.country'].search([('name', '=', 'Bahrain')], limit=1)
            self.country_id = country.id
            res['domain'] = {'country_id': [('id', '=', country.id)]}
        else:
            res['domain'] = {'country_id': []}
        return res


    @api.constrains('vat')
    def _check_vat(self):
        for partner in self:
            if partner.vat:
                if not partner.vat.isdigit():
                    raise ValidationError(_("VAT No. must contains only digits"))
                if len(partner.vat) > 15 or len(partner.vat) < 15:
                    raise ValidationError(_("Invalid VAT No., must contains only 15 digits only"))


    @api.depends('supplier_rank', 'x_is_vendor')
    def is_vendor(self):
        for all in self:
            if all.supplier_rank != 0:
                all.x_is_vendor = True
            else:
                all.x_is_vendor = False

    @api.depends('customer_rank', 'x_is_customer')
    def is_customer(self):
        for all in self:
            if all.customer_rank != 0:
                all.x_is_customer = True
            else:
                all.x_is_customer = False

    @api.onchange('x_is_customer', 'x_is_vendor', )
    def onchange_rank(self):
        for test in self:
            if test.x_is_customer == False and test.customer_rank == 1:
                test.customer_rank = 0
            elif test.x_is_customer == True and test.customer_rank == 0:
                test.customer_rank = 1
            if test.x_is_vendor == False and test.supplier_rank == 1:
                test.supplier_rank = 0
            elif test.x_is_vendor == True and test.supplier_rank == 0:
                test.supplier_rank = 1
