from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from lxml import etree
from lxml.builder import E


class DeliveryReminder(models.TransientModel):
    _name = 'delivery.reminder'
    _description = 'Delivery Reminder'

    def name_get(self):
        result = [(self.id, 'Reminder')]
        return result

    def _default_x_delivery(self):
        # delivery = self._context.get('delivery')
        # so_delivery_id = self.env['stock.picking'].search([('id', '=', delivery)]).sale_id.id
        sale_id = self._context.get('sale_id')
        print(sale_id, 'so_delivery_ids')
        all_booked = []
        for booked in self.env['stock.picking'].search([('sale_id.id', '=', sale_id), ('x_slot', '=', False),
                                                        ('picking_type_id.business_line', '!=', False),
                                                        ('state', '!=', 'done'), ('state', '!=', 'cancel')]):
            all_booked.append(booked.id)
        print(all_booked)
        print('booked')
        # print(delivery, 'delivery')

        return all_booked

    name = fields.Char('Name')
    x_delivery = fields.Many2many('stock.picking', string="Remaining Deliveries", default=_default_x_delivery,
                                  readonly=1)
    x_dn_status = fields.Selection([('reserved', 'Reserved'), ('normal', 'Normal')], string="Slot delivery Type")

    def action_view_logistic_gantt_from_reminder(self):
        self.ensure_one()
        # delivery = self._context.get('delivery')
        # sale_id = self.env['stock.picking'].search([('id', '=', delivery)]).sale_id.id
        sale_id = self._context.get('sale_id')
        delivery_ids = self.env['stock.picking'].search([('sale_id', '=', sale_id), ('x_slot', '=', False)])
        business = []
        print(delivery_ids, 'del')
        print(sale_id, 'sale')
        # print(delivery)
        for d in delivery_ids:
            if d.picking_type_id.business_line:
                business.append(d.picking_type_id.business_line.id)
        show = []
        for rec in self.env['plan.calendar'].search([]):
            # if rec.business_line.id in business:
            if rec.status == 'available' and rec.business_line.id in business:
                show.append(rec.id)
            elif rec.status == 'booked' and rec.delivery.sale_id.id == sale_id:
                show.append(rec.id)
        print(business)
        return {
            'name': _('Logistic'),
            'res_model': 'plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_logistics_extra.plan_calendar_view_gantt').id, 'gantt'),
            ],
            'context': {"active_model": 'sale.order', "active_id": sale_id, 'search_default_group_by_business_line': 1,
                        'search_default_group_by_status': 1},
            'domain': [('id', 'in', show)],
            'type': 'ir.actions.act_window',
        }

    def action_view_sale_order_from_reminder(self):
        self.ensure_one()
        return {
            'name': _('Sale Order'),
            'res_model': 'sale.order',
            'res_id': self._context.get('sale_id'),
            'view_mode': 'form',
            'target': 'main',
            'views': [
                (self.env.ref('sale.view_order_form').id, 'form'),
            ],
            # 'context': {'no_breadcrumbs': 1},
            # 'domain': [('id', 'in', show)],
            'type': 'ir.actions.act_window',
        }

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(DeliveryReminder, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                             submenu=submenu)
        if view_type == 'form' and view_id == self.env.ref('pabs_logistics_extra.delivery_reminder_form_view').id:
            sale_order = self.env['sale.order'].search([('id', '=', self._context.get('active_id'))])
            doc = etree.XML(res['arch'])
            for delivery in sale_order.picking_ids:
                if delivery.x_business_line.no_days and len(sale_order.picking_ids) == 1:
                    node = doc.xpath("//button[@name='reserve_slots']")[0]
                    node.set('string', "Reserve after %s Days" % (delivery.x_business_line.no_days))
                    node1 = doc.xpath("//button[@name='test']")[0]
                    node1.set('string', "Immediate within %s Days" % (delivery.x_business_line.no_days))
                    res['arch'] = etree.tostring(doc)
        return res
