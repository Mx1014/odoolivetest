from ast import literal_eval
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
import json
import logging
import pytz
import uuid
from lxml import etree
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ProjectTaskBatch(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = "project.task.batch"
    _description = 'Batch Tasks'
    _order = "id desc"

    # _order = 'start_datetime,id desc'
    # _rec_name = 'status'
    # _check_company_auto = True
    x_print_count = fields.Integer(string='Counting Print', tracking=True)
    x_current_time = fields.Datetime(string='Printing Datetime', tracking=True)

    def count_print_no(self):
        for rec in self:
            rec.x_print_count += 1

    def current_print_datetime(self):
        for rec in self:
            rec.x_current_time = datetime.now()

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('batch.name.sequence') or _('New')
        result = super(ProjectTaskBatch, self).create(vals)
        return result

    def unlink(self):
        for rec in self:
            if rec.state != 'cancel':
                raise UserError(_("To delete this visit sheet you have to cancel it first."))
        res = super(ProjectTaskBatch, self).unlink()
        return res

    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(ProjectTaskBatch, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                                         submenu=submenu)
    #     doc = etree.XML(res['arch'])
    #     nodes = doc.xpath("//field[@name='x_task_line']")
    #     print(self, 'ZOOOOOOOOOOOOONE')
    #     if self.x_zone:
    #         for node in nodes:
    #             node.set('domain', "[('is_fsm', '=', True), ('x_business_line', '=', x_business_line), ('partner_id.x_zone_id', '=', x_zone)]")
    #     else:
    #         for node in nodes:
    #             node.set('domain', "[('is_fsm', '=', True), ('x_business_line', '=', x_business_line)]")
    #     res['arch'] = etree.tostring(doc)
    #     print(res)
    #     return res

    # def _domain_x_task_line(self):
    #     res = "('is_fsm', '=', True), ('x_business_line', '=', x_business_line)"
    #     print(self.x_zone)
    #     if self.x_zone:
    #         res = "('is_fsm', '=', True), ('x_business_line', '=', x_business_line), ('partner_id.x_zone_id', '=', x_zone)"
    #         print(res)
    #     res = "[" + res + "]"
    #     print(res)
    #     return res
    @api.depends('x_zone', 'x_business_line')
    def _compute_x_task_line_domain(self):
        project_task = self.env['project.task']
        task_domain = project_task.search(
            [('is_fsm', '=', True), ('x_batch_id', '=', False), ('x_business_line.id', '=', self.x_business_line.id)])

        not_done = project_task.search(
            [('is_fsm', '=', True), ('fsm_done', '=', False), ('x_batch_id', '!=', False),
             ('x_business_line.id', '=', self.x_business_line.id), ('id', 'not in', task_domain.ids)])

        # task_domain = task_domain + not_done
        if self.x_zone:
            task_domain = project_task.search(
                [('is_fsm', '=', True), ('x_batch_id', '=', False),
                 ('x_business_line.id', '=', self.x_business_line.id),
                 ('partner_id.x_zone_id.id', '=', self.x_zone.id)])

            not_done = project_task.search(
                [('is_fsm', '=', True), ('fsm_done', '=', False), ('x_batch_id', '!=', False),
                 ('x_business_line.id', '=', self.x_business_line.id), ('partner_id.x_zone_id.id', '=', self.x_zone.id),
                 ('id', 'not in', task_domain.ids)])

        self.x_task_line_domain = task_domain + not_done

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], default='draft',
        copy=False, tracking=True, required=True, readonly=True)
    x_scheduled_date = fields.Date(string='Scheduled Date', default=fields.Date.today(), tracking=True)
    x_business_line = fields.Many2one('business.line', 'Business Line', tracking=True)
    x_team = fields.Many2one('logistics.team', 'Team', tracking=True)
    x_team_type = fields.Selection([('salamgas', 'Al-Salam Gas'), ('subcontractor', 'Subcontractor')],
                                   string='Team Type', related='x_team.team_type')
    x_vendor = fields.Many2one('res.partner', 'Team Vendor', related='x_team.team_owner')
    x_internal_team_supervisor = fields.Many2one('hr.employee', 'Team Supervisor', related='x_team.internal_team_owner')
    x_zone = fields.Many2one('res.zone', 'Zone', tracking=True)
    x_team_capacity = fields.Integer('Team Capacity', compute='compute_x_team_capacity')
    x_service_qty = fields.Integer('Scheduled Visits #', store=True, compute='compute_x_service_qty_x_remaining_qty')
    # x_service_qty_display = fields.Integer('Scheduled Visits #', store=True, )
    x_remaining_qty = fields.Integer('Remaining Capacity', store=True, compute='compute_x_service_qty_x_remaining_qty')
    x_task_line = fields.One2many('project.task', 'x_batch_id', string='Tasks', tracking=True)
    x_task_line_domain = fields.Many2many('project.task', string='Tasks', compute=_compute_x_task_line_domain)
    x_total_done = fields.Float(string="Done", store=True, compute="get_done_and_pending")
    x_total_pending = fields.Float(string="Pending", store=True, compute="get_done_and_pending")
    x_total_cancel = fields.Float(string="Cancelled", store=True, compute="get_done_and_pending")
    x_invoice_count = fields.Integer(string="Invoices", compute='_compute_invoice_count')
    x_invoice_qty = fields.Float(string="Invoiced", compute="_get_invoiced_and_not_invoiced")
    x_invoice_qty_show = fields.Float(string="Invoiced")
    x_not_invoice_qty = fields.Float(string="Not Invoiced", compute="_get_invoiced_and_not_invoiced")
    x_not_invoice_qty_show = fields.Float(string="Not Invoiced")

    def action_view_invoices(self):
        self.ensure_one()
        sales = self.env['sale.order'].search([('id', 'in', self.mapped('x_task_line.sale_order_id.id'))])
        return {
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_invoice_tree').id, 'tree'),
                (self.env.ref('account.view_move_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', sales.mapped('invoice_ids.id'))],
        }

    def _compute_invoice_count(self):
        for sheet in self:
            sales = self.env['sale.order'].search([('id', 'in', self.mapped('x_task_line.sale_order_id.id'))])
            sheet.x_invoice_count = len(sales.mapped('invoice_ids.id'))

    # @api.depends('x_task_line', 'state', 'x_team', 'x_scheduled_date', x_invoice_count)
    def _get_invoiced_and_not_invoiced(self):
        for task in self:
            sales = task.env['sale.order'].search([('id', 'in', task.mapped('x_task_line.sale_order_id.id'))])
            task.x_invoice_qty = len(sales.mapped('invoice_ids.id'))
            task.x_invoice_qty_show = len(sales.mapped('invoice_ids.id'))
            task.x_not_invoice_qty = task.x_total_done - len(sales.mapped('invoice_ids.id'))
            task.x_not_invoice_qty_show = task.x_total_done - len(sales.mapped('invoice_ids.id'))

    @api.onchange('x_team')
    def compute_x_team_capacity(self):
        for rec in self:
            if rec.x_team and rec.x_scheduled_date:
                delivery_day = rec.x_scheduled_date.strftime("%A").lower()
                for day in rec.x_team.attendance_ids:
                    if day.dayofweek == delivery_day:
                        rec.x_team_capacity = day.capacity_per_day
            else:
                rec.x_team_capacity = 0

    @api.onchange('x_task_line', 'x_team')
    @api.depends('x_task_line', 'state', 'x_team', 'x_scheduled_date')
    def compute_x_service_qty_x_remaining_qty(self):
        for rec in self:
            rec.x_service_qty = len(rec.x_task_line)
            rec.x_remaining_qty = rec.x_team_capacity - rec.x_service_qty

    @api.depends('x_task_line', 'state', 'x_team', 'x_scheduled_date')
    def get_done_and_pending(self):
        for task in self:
            task_line = task.x_task_line
            task.x_total_done = len(task_line.filtered(lambda x: x.fsm_done and not x.x_cancelled))
            task.x_total_pending = len(task_line.filtered(lambda x: not x.fsm_done))
            task.x_total_cancel = len(task_line.filtered(lambda x: x.fsm_done and x.x_cancelled))

    @api.onchange('x_business_line')
    def onchange_x_business_line(self):
        self.x_team = None
        self.x_task_line = [(5, 0, 0)]

    def action_confirm_batch(self):
        self.state = 'in_progress'

    def action_done_batch(self):
        for task in self.x_task_line:
            if not task.fsm_done:
                raise UserError(_("Some tasks are not done. Please mark all tasks as done then try again."))
        self.state = 'done'

    def action_cancel_project_task_batch(self):
        self.ensure_one()
        return {
            'name': _('Confirm Cancellation'),
            'res_model': 'cancel.task.batch',
            'view_mode': 'form',
            'views': [
                (self.env.ref('pabs_field_service.cancel_task_batch_view_form').id, 'form'),
            ],
            'target': 'new',
            'context': {'batch_id': self.id},
            'type': 'ir.actions.act_window',
        }

    def action_view_business_line_project_task_batch(self):
        # self.ensure_one()
        my_user = self.env.user
        business_line_ids = my_user.x_business_line_ids.ids
        show = []
        for rec in self.env['project.task.batch'].search([]):
            if rec.x_business_line.id in business_line_ids or not rec.x_business_line:
                show.append(rec.id)
        return {
            'name': _('Visits Sheets'),
            'res_model': 'project.task.batch',
            # 'res_id': self.x_batch_po.id,
            'view_type': 'form',
            'view_mode': 'tree,form,pivot,graph',
            # 'target': 'main',
            # 'views': [
            #     (self.env.ref('stock_picking_batch.stock_picking_batch_tree').id, 'tree'),
            # ],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', show)],
        }

    def action_set_to_draft_project_task_batch(self):
        self.state = 'draft'

    def print_all_visit_sheets(self):
        tasks = self.mapped('x_task_line')
        if not tasks:
            raise UserError(_('Nothing to print.'))
        return self.env.ref(
            'pabs_field_service.field_service_detailed_tripsheet_button').report_action(self)

    def print_all_helpdesk_tickets(self):
        helpdesk_ids = self.x_task_line.mapped('helpdesk_ticket_id')
        if not helpdesk_ids:
            raise UserError(_('Nothing to print.'))
        return self.env.ref(
            'pabs_repair.complaint_form').report_action(helpdesk_ids)

    def print_all_sales(self):
        task = self.mapped('x_task_line')
        order = task.mapped('sale_order_id')
        if order:
            return self.env.ref('pabs_sale_quotation.sale_quotation').report_action(order)
        else:
            raise UserError(_('Nothing to print.'))
