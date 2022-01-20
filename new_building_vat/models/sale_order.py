# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
from datetime import datetime, timedelta


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_new_building = fields.Boolean(string="Is New Building", default=False, store=True, track_visibility='always')
    cpr_attachment = fields.Binary(string='CPR', track_visibility='always', attachment=True)
    zero_rated_attachment = fields.Binary(string='Zero Rated Certificate', track_visibility='always', attachment=True)
    building_permit_attachment = fields.Binary(string='Building Permit', track_visibility='always', attachment=True)
    deadtile_attachment = fields.Binary(string='Deadtile', track_visibility='always', attachment=True)
    mazaya_attachment = fields.Binary(string='Mazaya/Eskan Agreement', track_visibility='always', attachment=True)
    other_attachment = fields.Binary(string='Other Documents', track_visibility='always', attachment=True)
    old_fiscal_position_id = fields.Many2one('account.fiscal.position', store=True)  # The old fiscal position before the module is changing it.

    @api.model
    def create(self, vals):
        result = super(SaleOrder, self).create(vals)
        if result.is_new_building:
            group_enable_newbuilding = self.env.user.has_group('new_building_vat.group_enable_newbuilding')
            fasical_position_id = self.env['ir.config_parameter'].sudo().get_param('new_building_vat.newbuilding_fasical_position_id')
            if not group_enable_newbuilding or not fasical_position_id:
                raise UserError(_('The new building settings was not configured yet!'))
            # Make the 3 required attachment documents required!
            if not result.cpr_attachment or not result.zero_rated_attachment or not result.building_permit_attachment:
                raise UserError(
                    _('You must attach the required documents for the new building (Customer CPR, '
                      'Zero Rated Certificate, and Building Permit))'))
            # If all the documents were added, now we can continue with our process and apply the fiscal position
            fasical_position_id = self.env['account.fiscal.position'].search([('id', '=', fasical_position_id)])
            # Before replacing the fiscal position, we need to recalculate the unit price for the order lines that have the tax inside the fiscal position
            for tax_line_id in fasical_position_id.tax_ids:
                for order_line_id in result.order_line:
                    if tax_line_id.tax_src_id in order_line_id.tax_id:
                        if tax_line_id.tax_src_id.price_include:
                            if tax_line_id.tax_src_id.amount_type == 'percent':
                                order_line_id.nb_price_unit = order_line_id.price_unit
                                order_line_id.price_unit = order_line_id.price_unit / ((tax_line_id.tax_src_id.amount / 100) + 1.00)
                            elif tax_line_id.tax_src_id.amount_type == 'fixed':
                                order_line_id.nb_price_unit = order_line_id.price_unit
                                order_line_id.price_unit = order_line_id.price_unit - tax_line_id.tax_src_id.amount
            result.old_fiscal_position_id = result.fiscal_position_id
            result.fiscal_position_id = fasical_position_id
            result.order_line._compute_tax_id()  # Recompute the order lines taxes as the onchange will not be triggered
            # Send an activity to the users who are responsible for validation!
            responsible_user_id = self.env.ref('new_building_vat.new_building_activity_type').default_user_id
            if responsible_user_id:
                result.message_subscribe(partner_ids=responsible_user_id.ids)
                self.env['mail.activity'].create({
                    'res_id': result.id,
                    'res_model_id': self.env['ir.model'].search([('model', '=', 'sale.order')], limit=1).id,
                    'summary': "New Building Permit",
                    'note': "Please double check the documents for the new building permit!",
                    'activity_type_id': self.env.ref('new_building_vat.new_building_activity_type').id,
                    'user_id': responsible_user_id.id,
                    'date_deadline': datetime.now() + timedelta(weeks=1),
                })
        return result

    def write(self, vals):
        attachment_fields = ['cpr_attachment', 'zero_rated_attachment', 'building_permit_attachment', 'deadtile_attachment', 'mazaya_attachment', 'other_attachment']
        attachment_module_fields = {'cpr_attachment': self.cpr_attachment, 'zero_rated_attachment': self.zero_rated_attachment, 'building_permit_attachment': self.building_permit_attachment, 'deadtile_attachment': self.deadtile_attachment, 'mazaya_attachment': self.mazaya_attachment, 'other_attachment': self.other_attachment}
        for attachment_field in attachment_fields:
            if attachment_field in vals:
                if attachment_module_fields[attachment_field] != False:
                    attachment_id = self.env['ir.attachment'].sudo().search([
                        ('res_model', '=', self._name),
                        ('res_field', '=', attachment_field),
                        ('res_id', '=', self.id)
                    ])
                    self.message_post(attachment_ids=[attachment_id.id])
        res = super(SaleOrder, self).write(vals)

        if 'is_new_building' in vals:
            group_enable_newbuilding = self.env.user.has_group('new_building_vat.group_enable_newbuilding')
            fasical_position_id = self.env['ir.config_parameter'].sudo().get_param('new_building_vat.newbuilding_fasical_position_id')
            if self.is_new_building:
                if not group_enable_newbuilding or not fasical_position_id:
                    raise UserError(_('The new building settings was not configured yet!'))
                # Make the 3 required attachment documents required!
                if not self.cpr_attachment or not self.zero_rated_attachment or not self.building_permit_attachment:
                    raise UserError(
                        _('You must attach the required documents for the new building (Customer CPR, '
                          'Zero Rated Certificate, and Building Permit))'))
                # If all the documents were added, now we can continue with our process and apply the fiscal position
                fasical_position_id = self.env['account.fiscal.position'].search([('id', '=', fasical_position_id)])
                # Before replacing the fiscal position, we need to recalculate the unit price for the order lines that have the tax inside the fiscal position
                for tax_line_id in fasical_position_id.tax_ids:
                    for order_line_id in self.order_line:
                        if tax_line_id.tax_src_id in order_line_id.tax_id:
                            if tax_line_id.tax_src_id.price_include:
                                if tax_line_id.tax_src_id.amount_type == 'percent':
                                    order_line_id.nb_price_unit = order_line_id.price_unit
                                    order_line_id.price_unit = order_line_id.price_unit / ((tax_line_id.tax_src_id.amount / 100) + 1.00)
                                elif tax_line_id.tax_src_id.amount_type == 'fixed':
                                    order_line_id.nb_price_unit = order_line_id.price_unit
                                    order_line_id.price_unit = order_line_id.price_unit - tax_line_id.tax_src_id.amount
                self.old_fiscal_position_id = self.fiscal_position_id
                self.fiscal_position_id = fasical_position_id
                self.order_line._compute_tax_id()  # Recompute the order lines taxes as the onchange will not be triggered
                # Send an activity to the users who are responsible for validation!
                responsible_user_id = self.env.ref('new_building_vat.new_building_activity_type').default_user_id
                if responsible_user_id:
                    self.message_subscribe(partner_ids=responsible_user_id.ids)
                    self.env['mail.activity'].create({
                        'res_id': self.id,
                        'res_model_id': self.env['ir.model'].search([('model', '=', 'sale.order')], limit=1).id,
                        'summary': "New Building Permit",
                        'note': "Please double check the documents for the new building permit!",
                        'activity_type_id': self.env.ref('new_building_vat.new_building_activity_type').id,
                        'user_id': responsible_user_id.id,
                        'date_deadline': datetime.now() + timedelta(weeks=1),
                    })
            else:  # The user changed it back to False
                if not self.old_fiscal_position_id:
                    raise UserError(_('The system can not revert back to the stage before applying the new building rates!'))
                # Check if there are any pending activities and mark them as done
                activity_ids = self.env['mail.activity'].search([('activity_type_id', '=', self.env.ref('new_building_vat.new_building_activity_type').id), ('res_id', '=', self.id), ('res_model_id', '=', self.env['ir.model'].search([('model', '=', 'sale.order')], limit=1).id)])
                for activity_id in activity_ids:
                    activity_id.unlink()
                # Return the unit price to the old unit price by reverting the calculation formulas, then revert the fiscal position to its old id
                fasical_position_id = self.env['account.fiscal.position'].search([('id', '=', fasical_position_id)])
                for tax_line_id in fasical_position_id.tax_ids:
                    for order_line_id in self.order_line:
                        if tax_line_id.tax_dest_id in order_line_id.tax_id:
                            if tax_line_id.tax_src_id.price_include:
                                order_line_id.price_unit = order_line_id.nb_price_unit
                self.fiscal_position_id = self.old_fiscal_position_id
                self.order_line._compute_tax_id()  # Recompute the order lines taxes as the onchange will not be triggered
        return res

    @api.onchange('is_new_building')
    def _onchange_is_new_building(self):
        group_enable_newbuilding = self.env.user.has_group('new_building_vat.group_enable_newbuilding')
        if not group_enable_newbuilding and self.is_new_building:
            self.is_new_building = False
            raise UserError(_('The new building settings was not configured yet!'))
