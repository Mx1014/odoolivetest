from odoo import _, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def contacts_whatsapp(self):
        return {'type': 'ir.actions.act_window',
                'name': _('Send Whatsapp Message'),
                'res_model': 'whatsapp.message.wizard',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_user_id': self.id, 'source_model': 'res.partner'},
                }

class WhatsappCrm(models.Model):
    _inherit = 'crm.lead'

    def crm_whatsapp(self):
        return {'type': 'ir.actions.act_window',
                'name': _('Send Whatsapp Message'),
                'res_model': 'whatsapp.message.wizard',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_user_id': self.partner_id.id, 'source_model': 'crm.lead'},
                }

class WhatsappInvoice(models.Model):
    _inherit = 'account.move'

    def invoice_whatsapp(self):
        return {'type': 'ir.actions.act_window',
                'name': _('Send Whatsapp Message'),
                'res_model': 'whatsapp.message.wizard',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_template_id': self.env.ref('ss_whatsapp_connector.whatsapp_invoice_template').id, 'source_model': 'account.move'},
                }

class WhatsappPurchase(models.Model):
    _inherit = 'purchase.order'

    def purchase_whatsapp(self):
        return {'type': 'ir.actions.act_window',
                'name': _('Send Whatsapp Message'),
                'res_model': 'whatsapp.message.wizard',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_template_id': self.env.ref('ss_whatsapp_connector.whatsapp_purchase_template').id, 'source_model': 'purchase.order'},
                }

class WhatsappSale(models.Model):
    _inherit = 'sale.order'

    def sale_whatsapp(self):
        return {'type': 'ir.actions.act_window',
                'name': _('Send Whatsapp Message'),
                'res_model': 'whatsapp.message.wizard',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_template_id': self.env.ref('ss_whatsapp_connector.whatsapp_sales_template').id, 'source_model': 'sale.order'},
                }




class WhatsappPurchase(models.Model):
    _inherit = 'stock.picking'

    def stock_whatsapp(self):
        return {'type': 'ir.actions.act_window',
                'name': _('Send Whatsapp Message'),
                'res_model': 'whatsapp.message.wizard',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_user_id': self.partner_id.id, 'source_model': 'stock.picking'},
                }


class WhatsappCoupon(models.Model):
    _inherit = 'sale.coupon'

    def coupon_whatsapp(self):
        cops = []
        coupons = self.search([('id', 'in', self._context.get('active_ids'))])
        for pdf in self.search([('id', 'in', coupons.ids)]):
            val = self.attach_coupons(pdf)
            cops.append(val.id)
        return {'type': 'ir.actions.act_window',
                'name': _('Send Whatsapp Message'),
                'res_model': 'whatsapp.message.wizard',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_user_id': coupons[0].partner_id.id,
                            'default_attachment_ids': [(6, 0, cops)],
                            'active_ids': self._context.get('active_ids'), 'active_model': self._context.get('active_model'),
                            'default_template_id': coupons.program_id.x_template_id.id, 'source_model': 'sale.coupon'},
                }
