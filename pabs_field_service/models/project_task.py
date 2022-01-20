import base64

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from odoo.tools import format_time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ProjectTask(models.Model):
    _inherit = 'project.task'

    x_scheduled_date = fields.Datetime("Scheduled Date")
    x_is_collect_ticket = fields.Boolean(string='No S.O.', related='helpdesk_ticket_id.is_collect')
    related_x_is_not_required = fields.Boolean(string='Related Invoice Not Required.', related='project_id.x_is_not_required')
    x_slot = fields.Many2one('field.plan.calendar', string="Calendar Slot", copy=False)
    x_business_line = fields.Many2one('business.line', string="Business Line", related='project_id.business_line', store=True)
    x_crm_id = fields.Many2one('crm.lead', string="Opportunity", copy=False)
    x_no_charge = fields.Boolean('Non Chargeable Visit', default=False)
    x_helpdesk_use_product_returns = fields.Boolean(string="Helpdesk Use Product Returns", related='helpdesk_ticket_id.use_product_returns')
    x_helpdesk_ticket_team_id = fields.Many2one('helpdesk.team', string="Helpdesk Team Id In Related Ticket", related='helpdesk_ticket_id.team_id')
    x_helpdesk_product_id = fields.Many2one('product.product', string="Helpdesk Product ID", related='helpdesk_ticket_id.product_id')
    x_helpdesk_lot_id = fields.Many2one('stock.production.lot', string="Helpdesk Lot ID", related='helpdesk_ticket_id.lot_id')
    x_helpdesk_use_product_repairs = fields.Boolean(string="Helpdesk Use Product Repairs", related='helpdesk_ticket_id.use_product_repairs')
    x_batch_id = fields.Many2one('project.task.batch', string='Batch ID', copy=False)
    x_team_id = fields.Many2one('logistics.team', string='Team', related='x_batch_id.x_team', copy=False, store=True)
    x_zone_id = fields.Many2one('res.zone', 'Zone', related='partner_id.x_zone_id', store=True, copy=False)
    x_block_id = fields.Many2one('city.block', 'Block', related='partner_id.x_address_block', store=True, copy=False)
    x_road_id = fields.Many2one('city.road', 'Road', related='partner_id.x_address_road', store=True, copy=False)
    x_city = fields.Char(string='City', related='partner_id.city', store=True, copy=False)
    x_house = fields.Char(string='House', related='partner_id.street_number', store=True, copy=False)
    x_route_id = fields.Many2one('stock.location.route', string='Spare Parts Route', related='x_team_id.x_route_id')
    x_mobile = fields.Char(string='Mobile', related='partner_id.mobile', store=True, copy=False)
    x_priority = fields.Selection(string='Priority', default='1',
                                  selection=[('0', 'Not urgent'), ('1', 'Normal'), ('2', 'Urgent'),
                                             ('3', 'Very urgent')], related='x_slot.x_priority', store=1, readonly=False, copy=False)
    x_product_id = fields.Many2one('product.product', string="Product", related='helpdesk_ticket_id.product_id')
    x_warranty_id = fields.Many2one('warranty.line', string="Warranty Reference",
                                    related='helpdesk_ticket_id.warranty_sequence')
    x_warranty_end_date = fields.Date(string='Warranty End Date', related='x_warranty_id.date_done', store=True)
    x_extended_end_date = fields.Date(string='Extended Warranty End Date', related='x_warranty_id.extended_end_date')
    x_warranty_state = fields.Selection([
        ('Running', 'Running'),
        ('Extended', 'Extended'),
        ('Expired', 'Expired'),
    ],
        string='Warranty State')
    x_show_inspection_print = fields.Boolean('is split inspection', compute='compute_x_show_inspection_print')
    x_service_type = fields.Char(string="Service Type", store=True, default="@ Field")
    x_invoices_id = fields.Many2one('account.move', string="Invoice", compute="_get_invoices")
    x_invoices = fields.Many2one('account.move', string="Invoices", store=True)
    x_issue_type = fields.Char(string="Issue Type", store=True, related='helpdesk_ticket_id.x_issue_type.name')

    x_invoice_method = fields.Selection([
        ("warranty", "Under Warranty"),
        ("after_sale", "After Sale")], string="Invoice Method",
        default='after_sale', index=True)
    x_invoice_partner_id = fields.Many2one('res.partner', 'Invoice Address')
    x_ticket_id = fields.Integer(string="ID", related="helpdesk_ticket_id.id")
    x_ticket_stage = fields.Many2one('helpdesk.stage', related="helpdesk_ticket_id.stage_id", string="Stage")
    x_ticket_type_id = fields.Many2one('helpdesk.ticket.type', related="helpdesk_ticket_id.ticket_type_id", string="Ticket Type")
    x_state = fields.Selection([
        ('new', 'New'),
        ('quote', 'Quotation'),
        ('invoice', 'Invoiced'),
        ('cancel', 'Cancelled')], default='new',
        copy=False, tracking=True, string="State", readonly=True, compute="compute_fsm_x_state")
    x_sale_state = fields.Selection(related="sale_order_id.state")
    x_cancelled = fields.Boolean(string="Cancelled", default=False, store=True)
    x_batch_date = fields.Date(related="x_batch_id.x_scheduled_date", store=True)

    def compute_fsm_x_state(self):
        for task in self:
            if task.sale_order_id:
                if task.sale_order_id.state in ['draft', 'sent']:
                    task.x_state = 'quote'
                elif task.sale_order_id.invoice_ids:
                    task.x_state = 'invoice'
                elif task.sale_order_id.state == 'cancel':
                    task.x_state = 'cancel'
                else:
                    task.x_state = 'quote'
            else:
                if task.x_cancelled:
                    task.x_state = 'cancel'
                else:
                   task.x_state = 'new'


    def compute_fsm_warranty_state_once(self):
        records = self.env['project.task'].search([('helpdesk_ticket_id', '!=', False), ('x_warranty_state', '=', False)])
        for rec in records:
            rec.warranty_state = rec.helpdesk_ticket_id.warranty_status

    @api.onchange('partner_id')
    def _onchange_partner_idd(self):
        super(ProjectTask, self)._onchange_partner_id()
        order = self.sale_order_id
        if self.x_invoice_method == 'after_sale':
            self.x_invoice_partner_id = self.partner_id
            if order and order.state == 'draft':
                order.partner_invoice_id = self.x_invoice_partner_id
                for line in order.order_line:
                    if order.partner_invoice_id.id == order.company_id.partner_id.id:
                        line['tax_id'] = [(6, 0, [19])]

    @api.onchange('x_invoice_method', 'x_warranty_state')
    def _onchange_partner_id(self):
        comeback = self.env.ref('pabs_repair.comeback').id
        if self.x_invoice_method == 'warranty':
            if self.helpdesk_ticket_id.ticket_type_id.id == comeback:
                self.x_invoice_partner_id = self.company_id.partner_id.id
            elif self.x_warranty_state == 'Running':
                self.x_invoice_partner_id = self.x_product_id.product_brand_id.partner_id.id
            elif self.x_warranty_state == 'Extended':
                self.x_invoice_partner_id = self.x_warranty_id.x_warranty_agent.id
        else:
            self.x_invoice_partner_id = self.partner_id.id

        if self.sale_order_id and self.sale_order_id.state == 'draft':
            self.sudo().sale_order_id.update({'partner_invoice_id': self.x_invoice_partner_id.id})
            self.sale_order_id.payment_term_id = self.x_invoice_partner_id.property_payment_term_id and self.x_invoice_partner_id.property_payment_term_id.id or False
            #self.sale_order_id.onchange_partner_id()
            for line in self.sale_order_id.order_line:
                if self.sale_order_id.partner_invoice_id.id == self.sale_order_id.company_id.partner_id.id:
                    line['tax_id'] = [(6, 0, [19])]
                else:
                    line.product_id_change()


    x_spare_parts = fields.Selection([('request', 'Requested'), ('arrange', 'Arranged')], string="Spare Parts")


    def _get_invoices(self):
        for task in self:
            if task.sale_order_id.invoice_ids:
                task.x_invoices = task.sale_order_id.invoice_ids[0].id
                task.x_invoices_id = task.sale_order_id.invoice_ids[0].id
            else:
                task.x_invoices = False
                task.x_invoices_id = False

    @api.depends('worksheet_template_id')
    def compute_x_show_inspection_print(self):
        if self.worksheet_template_id and self.worksheet_template_id.id == self.env.ref('pabs_field_service.fsm_worksheet_template_inspection_service_worksheet').id:
            worksheet = self.env['split.inspection.worksheet'].search([('x_task_id', '=', self.id)], limit=1)
            if worksheet:
                self.x_show_inspection_print = True
            else:
                self.x_show_inspection_print = False
        else:
            self.x_show_inspection_print = False

    @api.onchange('x_scheduled_date')
    def onchange_fleet_vehicle_id(self):
        for rec in self:
            rec.planned_date_begin = rec.x_scheduled_date
            rec.planned_date_end = rec.x_scheduled_date

    # def _fsm_create_sale_order(self):
    #     res = super(ProjectTask, self)._fsm_create_sale_order()
    #     self.sale_order_id.write({'x_no_charge': self.x_no_charge})
    #     self.sale_order_id.sale_order_type = self.project_id.x_sale_order_type
    #     self.sale_order_id.opportunity_id = self.x_crm_id
    #     return res

    def _fsm_create_sale_order_custom(self):
        """ Create the SO from the task, with the 'service product' sales line and link all timesheet to that line it """
        if not self.partner_id:
            raise UserError(_('The FSM task must have a customer set to be sold.'))

        SaleOrder = self.env['sale.order']
        if self.user_has_groups('project.group_project_user'):
            SaleOrder = SaleOrder.sudo()

        sale_order = SaleOrder.create({
            'partner_id': self.partner_id.id,
            'analytic_account_id': self.project_id.analytic_account_id.id,
            'x_no_charge': self.x_no_charge,
            'sale_order_type': self.project_id.x_sale_order_type,
            'opportunity_id': self.x_crm_id,
            'x_task_id': self.id,
        })
        sale_order.onchange_partner_id()
        sale_order.partner_invoice_id = self.x_invoice_partner_id.id

        # write after creation since onchange_partner_id sets the current user
        sale_order.write({'user_id': self.user_id.id})

        self.sale_order_id = sale_order

    def _fsm_create_sale_order(self):
        return


    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        context = dict(self.env.context)
        # for default stage
        if vals.get('project_id') and not context.get('default_project_id'):
            context['default_project_id'] = vals.get('project_id')
        # user_id change: update date_assign
        if vals.get('user_id'):
            vals['date_assign'] = fields.Datetime.now()
        # Stage change: Update date_end if folded stage and date_last_stage_update
        if vals.get('stage_id'):
            vals.update(self.update_date_end(vals['stage_id']))
            vals['date_last_stage_update'] = fields.Datetime.now()
        # substask default values
        if vals.get('parent_id'):
            for fname, value in self._subtask_values_from_parent(vals['parent_id']).items():
                if fname not in vals:
                    vals[fname] = value
        task = super(ProjectTask, self.with_context(context)).create(vals)
        if task.is_fsm:
            task._fsm_ensure_sale_order()
        return task

    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        for rec in self:
            if rec.is_fsm:
                rec.sale_order_id.write({'x_no_charge': rec.x_no_charge})
        print(res)
        return res

    def unlink(self):
        task = self
        # slot = self.env['field.plan.calendar'].search([('id', '=', self.x_slot.id)])
        if self.x_slot:
            self.x_slot.status = 'available'
            self.x_slot.note = ''
            self.x_slot.period = 0
            self.x_slot.x_priority = '1'
        return super(ProjectTask, task).unlink()

    def action_field_plan_calendar_from_reminder_item(self):
        task_id = self._context.get('task_id')
        business_line_id = self.env['project.task'].search([('id', '=', task_id)]).x_business_line.id
        return {
            'name': _('Field Service Calendar'),
            'res_model': 'field.plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_field_service.field_plan_calendar_gantt_view_sale').id, 'gantt'),
            ],
            # 'target': 'new',
            # 'context': {'business_line': business_line},
            'domain': [('status', '=', 'available'), ('business_line', '=', business_line_id), ('start_datetime', '>=', fields.Date.today())],
            'type': 'ir.actions.act_window',
        }

    def action_field_plan_calendar_task(self):
        task_id = self._context.get('task_id')
        business_line_id = self.env['project.task'].search([('id', '=', task_id)]).x_business_line.id
        return {
            'name': _('Field Service Calendar'),
            'res_model': 'field.plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_field_service.field_plan_calendar_gantt_view_task').id, 'gantt'),
            ],
            'target': 'new',
            # 'context': {'business_line': business_line},
            'domain': [('status', '=', 'available'), ('business_line', '=', business_line_id),
                       ('start_datetime', '>=', fields.Date.today())],
            'type': 'ir.actions.act_window',
        }

    def action_field_plan_calendar_shift_task(self):
        self.ensure_one()
        business_line = self._context.get('business_line')
        slot_id = self._context.get('slot')
        return {
            'name': _('Field Service Calendar'),
            'res_model': 'field.plan.calendar',
            'view_mode': 'gantt',
            'views': [
                (self.env.ref('pabs_field_service.shift_field_plan_calendar_gantt_view_task').id, 'gantt'),
            ],
            'target': 'new',
            'context': {'business_line': business_line, 'slot_id': slot_id},
            'domain': [('business_line', '=', business_line), ('status', '=', 'available')],
            'type': 'ir.actions.act_window',
        }

    def action_field_plan_calendar_sale_quotation(self):
        self.ensure_one()
        return {
            'name': _('Sale Order From Task'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'views': [
                (self.env.ref('sale.view_order_form').id, 'form'),
            ],
            'type': 'ir.actions.act_window',
        }

    service_line_service_count = fields.Integer(compute='_compute_service_line_totals')
    service_line_total_service_price = fields.Float(compute='_compute_service_line_totals')

    @api.depends('sale_order_id.order_line.product_uom_qty', 'sale_order_id.order_line.price_total')
    def _compute_service_line_totals(self):

        def if_fsm_service_line(sale_line_id, task):
            is_not_timesheet_line = sale_line_id.product_id != task.project_id.timesheet_product_id
            is_not_empty = sale_line_id.product_uom_qty != 0
            is_not_service_from_so = sale_line_id != task.sale_line_id
            is_not_consumable_product = sale_line_id.product_id.type != 'consu'
            is_not_storable_product = sale_line_id.product_id.type != 'product'
            return all([is_not_timesheet_line, is_not_empty, is_not_service_from_so, is_not_consumable_product, is_not_storable_product])

        for task in self:
            service_sale_lines = task.sudo().sale_order_id.order_line.filtered(
                lambda sol: if_fsm_service_line(sol, task))
            task.service_line_total_service_price = sum(service_sale_lines.mapped('price_total'))
            task.service_line_service_count = sum(service_sale_lines.mapped('product_uom_qty'))

    @api.depends('sale_order_id.order_line.product_uom_qty', 'sale_order_id.order_line.price_total')
    def _compute_material_line_totals(self):

        def if_fsm_material_line(sale_line_id, task):
            is_not_timesheet_line = sale_line_id.product_id != task.project_id.timesheet_product_id
            is_not_empty = sale_line_id.product_uom_qty != 0
            is_not_service_from_so = sale_line_id != task.sale_line_id
            is_not_service_from = sale_line_id.product_id.type != 'service'
            return all([is_not_timesheet_line, is_not_empty, is_not_service_from_so, is_not_service_from])

        for task in self:
            material_sale_lines = task.sudo().sale_order_id.order_line.filtered(
                lambda sol: if_fsm_material_line(sol, task))
            task.material_line_total_price = sum(material_sale_lines.mapped('price_total'))
            task.material_line_product_count = sum(material_sale_lines.mapped('product_uom_qty'))

    def action_fsm_view_services(self):
        self._fsm_ensure_sale_order()
        domain = [('sale_ok', '=', True), ('id', 'in', self.project_id.x_service_ids.ids)]
        if self.project_id and self.project_id.timesheet_product_id:
            domain = expression.AND([domain, [('id', '!=', self.project_id.timesheet_product_id.id)]])
        deposit_product = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
        if deposit_product:
            domain = expression.AND([domain, [('id', '!=', deposit_product)]])

        kanban_view = self.env.ref('industry_fsm.view_product_product_kanban_material')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Choose Products'),
            'res_model': 'product.product',
            'views': [(kanban_view.id, 'kanban'), (False, 'form')],
            'domain': domain,
            'context': {
                'fsm_mode': True,
                'create': self.env['product.template'].check_access_rights('create', raise_exception=False),
                'fsm_task_id': self.id,  # avoid 'default_' context key as we are going to create SOL with this context
                'pricelist': self.partner_id.property_product_pricelist.id if self.partner_id else False,
                'partner': self.partner_id.id if self.partner_id else False,
                'search_default_services': 1,
                'hide_qty_buttons': self.fsm_done
            },
            'help': _("""<p class="o_view_nocontent_smiling_face">
                            Create a new product
                        </p><p>
                            You must define a product for everything you sell or purchase,
                            whether it's a storable product, a consumable or a service.
                        </p>""")
        }

    def action_fsm_view_material(self):
        """Override to remove tracked products from the domain.
        """
        action = super(ProjectTask, self).action_fsm_view_material()
        action['domain'] = expression.AND([action.get('domain', []), [('id', 'in', self.project_id.x_product_ids.ids)]])
        return action

    def _fsm_create_sale_order_line(self):
       print('abc123')

    def action_print_custom_worksheet_report(self):
        if self.worksheet_template_id and self.worksheet_template_id.id == self.env.ref('pabs_field_service.fsm_worksheet_template_inspection_service_worksheet').id:
            worksheet = self.env['split.inspection.worksheet'].search([('x_task_id', '=', self.id)], limit=1)
            if not worksheet:
                raise UserError(_('Nothing to print.'))

            return self.env.ref('pabs_field_service.task_custom_report_split_inspection').report_action(worksheet)

    def attach_work_sheet(self):
        worksheet = self.env['split.inspection.worksheet'].search([('x_task_id', '=', self.id)], limit=1)
        pdf = self.env.ref('pabs_field_service.task_custom_report_split_inspection').render_qweb_pdf(worksheet.id)
        b64_pdf = base64.b64encode(pdf[0])
        return self.env['ir.attachment'].create({
            'name': self.name + '.pdf',
            'type': 'binary',
            'datas': b64_pdf,
            # 'datas_fname': self.sale_order_id.name + '.pdf',
            'store_fname': self.name,
            'res_model': 'project.task',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

    def action_email_custom_worksheet_report(self):
        self.ensure_one()
        worksheet = self.attach_work_sheet()
        print(worksheet, "dddddd")
        if not self.worksheet_template_id:
            raise UserError(_("To send the report, you need to select a worksheet template."))

        # Note: as we want to see all time and material on worksheet, ensure the SO is created (case: timesheet but no material, the
        # time should be sold on SO)
        if self.allow_billable:
            self._fsm_ensure_sale_order()

        template_id = self.env.ref('pabs_field_service.pabs_field_service_spilt_inspection_mail_template_data_send_report').id
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': {
                'default_model': 'project.task',
                'default_res_id': self.id,
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                # 'default_attachment_ids': [6, 0, worksheet.id],
                'default_attachment_ids': [(4, worksheet.id)],
                'force_email': True,
                'fsm_mark_as_sent': True,
            },
        }

    def action_send_report(self):
        ws = self.env['split.inspection.worksheet'].search([('x_task_id', '=', self.id)], limit=1)
        if ws:
            return self.action_email_custom_worksheet_report()
        else:
            return super(ProjectTask, self).action_send_report()

    def action_cancel(self):
        for task in self:
            task.fsm_done = True
            task.sale_order_id.action_cancel()
            task.x_cancelled = 'cancel'
