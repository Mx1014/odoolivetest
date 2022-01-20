import dateutil
from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import date
from odoo.exceptions import UserError


class Warranty(models.Model):
    _name = 'warranty.line'
    _rec_name = 'warranty_sequence'
    delivery_note = fields.Many2one('stock.picking', string='Delivery Note')
    warranty_sequence = fields.Char(string='Warranty Reference', required=True, copy=False, readonly=True, index=True,
                                    default=lambda self: _('New'))
    order_id = fields.Many2one('sale.order', string='Order Reference')
    customer_name = fields.Many2one('res.partner', track_visibility="always")
    scheduled_date = fields.Date(string='Warranty Start Date')
    extended_end_date = fields.Date(string='Extended Warranty End Date')
    date_done = fields.Date(string='Warranty End Date')
    brand_agent = fields.Many2one('res.partner', string='Brand Agent', related='product_id.product_brand_id.partner_id')
    agents_product = fields.Many2one('product.brand', related='product_id.product_brand_id')
    x_order_line = fields.Many2one('sale.order.line', string='Order line')
    x_product_id_domain = fields.Many2many('product.product', compute='compute_x_product_id_domain')
    other_info = fields.Char(string='Other Info')
    serial_no = fields.Char(string='Serial No')
    # x_team = fields.Many2one('logistics.team', string='Transfer Team', related='delivery_note.x_logistics_team')
    x_transfer_team = fields.Many2one('logistics.team', string='Installed by', related='delivery_note.x_logistics_team')
    x_warranty_agent = fields.Many2one('res.partner', string="Warranty Agent", compute='compute_extended_warranty_agent')

    def compute_extended_warranty_agent(self):
        self.x_warranty_agent = False
        for rec in self.order_id.order_line:
            if self.x_order_line == rec.related_order_line_id:
                self.x_warranty_agent = rec.product_id.extended_warranty_agent
                break
            else:
                self.x_warranty_agent = False

    @api.depends('order_id')
    def compute_x_product_id_domain(self):
        ids = []
        if self.order_id:
            for rec in self.order_id.order_line:
                ids.append(rec.product_id.id)
            self.x_product_id_domain = [(6, 0, ids)]
        else:
            self.x_product_id_domain = [(5, 0, 0)]

    @api.onchange('x_product_id_domain')
    def onchange_x_product_id_domain(self):
        if not self.order_id:
            res = {'domain': {'product_id': []}}

        else:
            res = {'domain': {'product_id': [('id', 'in', self.x_product_id_domain.ids)]}}
        return res

    @api.onchange('order_id')
    def onchange_order_id(self):
        self.x_order_line = False
        #self.product_id = False
        self.delivery_note = False

    @api.model
    def create(self, vals):
        if vals.get('warranty_sequence', _('New')) == _('New'):
            vals['warranty_sequence'] = self.env['ir.sequence'].next_by_code('warranty.sequence') or _('New')
        result = super(Warranty, self).create(vals)
        return result

    # @api.depends('scheduled_date', 'date_done')
    def warranty_status(self):
        for rec in self:
            if rec.date_done:
                if fields.Date.today():
                    if fields.Date.today() > rec.date_done:
                        if rec.extended_end_date and rec.extended_end_date >= fields.Date.today():
                            rec.state = 'Extended'
                        else:
                            rec.state = 'Expired'
                    else:
                        rec.state = 'Running'

    state = fields.Selection([
        ('Running', 'Running'),
        ('Extended', 'Extended'),
        ('Expired', 'Expired'),
    ],
        string='Status', compute=warranty_status)
    product_id = fields.Many2one('product.product')


class WarrantyLines(models.Model):
    _inherit = 'sale.order'

    warranty_line = fields.One2many('warranty.line', 'order_id', string='Warranty Lines', copy=False)

    def copy(self, default=None):
        res = super(WarrantyLines, self).copy(default)
        for rec in res.order_line:
            if rec.product_id.is_extended:
                rec.unlink()
        return res


class RelationalProduct(models.Model):
    _inherit = 'sale.order.line'

    related_order_line_id = fields.Many2one('sale.order.line', string='Related Order Line', copy=False)
    related_partner_id = fields.Many2one('res.partner', string='Customer', related='order_id.partner_id')
    related_order_date = fields.Datetime(string='Order Date', related='order_id.date_order')
    related_allow_extended = fields.Boolean(related='product_id.allow_extended_warranty',
                                            string='Related Extended Warranty')

    def add_extended(self):
        self.ensure_one()
        has_extended = False
        for rec in self.order_id.order_line:
            if rec.related_order_line_id == self and rec.product_id.is_extended:
                has_extended = True
        if has_extended:
            raise UserError(_("This order line already has an extended warranty attached to it."))
        else:
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'get.extended.warranty',
                # 'res_id': self.id,
                'views': [
                    (self.env.ref('pabs_warranty.extended_warranty_form').id, 'form'),
                ],
                'target': 'new',
            }

    # def action_view_extended_warranty(self):
    #     return [('product_id', '=', self.env.ref('pabs_warranty.extended_warranty_product'))
    # ]
    def action_view_extended_warranty(self):
        extended_warranty_ids = self.env['product.product'].search([('is_extended', '=', True)])
        show = self.env['sale.order.line'].search(
            [('product_id.id', 'in', extended_warranty_ids.ids)]).ids
        return {
            'name': _('Extended  Warranty'),
            'res_model': 'sale.order.line',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', show)],
        }
