import base64
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class Repair(models.Model):
    _inherit = 'repair.order'

    @api.model
    def _default_stock_location(self):
        default_ticket_id = self._context.get('default_ticket_id')
        default_warranty_end = self._context.get('default_guarantee_limit')
        ticket_id = self.env['helpdesk.ticket'].browse(default_ticket_id)
        print(default_warranty_end, 'default_WAR')
        if ticket_id and ticket_id.team_id.x_location_id:
            return ticket_id.team_id.x_location_id.id

        else:
            warehouse = self.env['stock.warehouse'].search([], limit=1)
            if warehouse:
                return warehouse.lot_stock_id.id
        return False

    location_id = fields.Many2one(
        'stock.location', 'Location',
        default=_default_stock_location,
        index=True, readonly=True, required=True,
        help="This is the location where the product to repair is located.",
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', True)]})

    # def _compute_x_task_id(self):
    #     for rec in self:
    #         task_id = self.env['project.task'].search([('x_repair_id', '=', rec.id)], limit=1)
    #         rec.x_task_id = task_id
    # , compute = _compute_x_task_id
    invoice_method = fields.Selection([
        ("none", "No Invoice"),
        ("warranty", "Under Warranty"),
        ("b4repair", "Before Repair"),
        ("after_repair", "After Repair")], string="Invoice Method",
        default='after_repair', index=True, readonly=True, required=True,
        states={'draft': [('readonly', False)]},
        help='Selecting \'Before Repair\' or \'After Repair\' will allow you to generate invoice before or after the repair is done respectively. \'No invoice\' means you don\'t want to generate invoice for this repair order.')

    x_task_id = fields.Many2one('project.task', string="Task", copy=False)
    project_id = fields.Many2one('project.project', string='Project', related='x_task_id.project_id', store=True)
    #x_business_line = fields.Many2one('business.line', string='Business Line', related="x_task_id.project_id.business_line", store=True)
    analytic_account_active = fields.Boolean("Analytic Account", related='x_task_id.analytic_account_active',
                                             readonly=True)
    allow_timesheets = fields.Boolean("Allow timesheets", related='x_task_id.allow_timesheets',
                                      help="Timesheets can be logged on this task.", readonly=True)
    remaining_hours = fields.Float("Remaining Hours", related='x_task_id.remaining_hours', store=True, readonly=True,
                                   help="Total remaining time, can be re-estimated periodically by the assignee of the task.")
    effective_hours = fields.Float("Hours Spent", related='x_task_id.effective_hours', store=True,
                                   help="Computed using the sum of the task work done.")
    total_hours_spent = fields.Float("Total Hours", related='x_task_id.total_hours_spent', store=True,
                                     help="Computed as: Time Spent + Sub-tasks Hours.")
    progress = fields.Float("Progress", related='x_task_id.progress', store=True, group_operator="avg",
                            help="Display progress of current task.")
    subtask_effective_hours = fields.Float("Sub-tasks Hours Spent", related='x_task_id.subtask_effective_hours',
                                           store=True, help="Sum of actually spent hours on the subtask(s)")
    # timesheet_ids = fields.Many2many('account.analytic.line', string='Timesheets', compute='compute_timesheet_ids')
    timesheet_ids = fields.One2many('account.analytic.line', 'repair_id', 'Timesheets')
    planned_hours = fields.Float("Planned Hours",
                                 help='It is the time planned to achieve the task. If this document has sub-tasks, it means the time needed to achieve this tasks and its childs.',
                                 tracking=True, related='x_task_id.planned_hours')
    subtask_planned_hours = fields.Float("Subtasks", related='x_task_id.subtask_planned_hours',
                                         help="Computed using sum of hours planned of all subtasks created from main task. Usually these hours are less or equal to the Planned Hours (of main task).")
    subtask_count = fields.Integer("Sub-task count", related='x_task_id.subtask_count')
    product_brand = fields.Many2one('product.brand', string='Brand', related='product_id.product_brand_id')
    repair_date = fields.Datetime(string='Repair Start Date', copy=False, readonly=True)
    x_repair_end_date = fields.Datetime(string='Repair End Date', copy=False, readonly=True)
    technician = fields.Many2one('hr.employee', string="Technician")
    diagnosis = fields.Char(string="Diagnosis")
    product_model = fields.Char(string="Product Model")
    receive_condition = fields.Char(string="Receive Condition")
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', related='ticket_id.sale_order_id')
    warranty_state = fields.Selection([
        ('Running', 'Running'),
        ('Extended', 'Extended'),
        ('Expired', 'Expired')],
        string=' Warranty Status')
    warranty = fields.Char(string='Warranty')
    x_product_serial_no = fields.Char('Product Serial No')
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id')
    x_repair_project = fields.Many2one('project.project', string="Repair Project")
    x_not_covered = fields.Boolean(string="Not Covered By Warranty", compute='compute_x_not_covered')
    operations = fields.One2many(
        'repair.line', 'repair_id', 'Parts',
        copy=True, readonly=False)

    @api.depends('invoice_method')
    def compute_x_not_covered(self):
        for rec in self:
            if rec.invoice_method == 'warranty':
                rec.x_not_covered = False
            else:
                rec.x_not_covered = True

    def set_to_quotation(self):
        for rec in self:
            rec.write({'state': 'draft'})

    @api.model
    def onchange_operations_custom(self):
        for repair in self:
            if repair.state == 'under_repair':
                message = '%s made changes in spare part lines' %(self.env.user.name)
                return repair.message_post(body=message, message_type="comment")


    def compute_warranty_state_once(self):
        records = self.env['repair.order'].search([('ticket_id', '!=', False), ('warranty_state', '=', False)])
        for rec in records:
            rec.warranty_state = rec.ticket_id.warranty_status

    x_service_type = fields.Char(string="Service Type", store=True, default="@ Center")
    x_spare_parts = fields.Selection([('request', 'Requested'), ('arrange', 'Arranged')], string="Spare Parts")
    x_pickings_count = fields.Integer('Return Orders Count', compute="_compute_pickings_count")
    x_picking_ids = fields.Many2many('stock.picking', related="ticket_id.picking_ids", string="Return Orders")

    @api.depends('x_picking_ids')
    def _compute_pickings_count(self):
        for ticket in self:
            ticket.x_pickings_count = len(ticket.x_picking_ids)

    def action_view_pickings(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Return Orders'),
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.x_picking_ids.ids)],
            'context': dict(self._context, create=False, default_company_id=self.company_id.id)
        }

    def _amount_tax(self):
        for order in self:
            val = 0.0
            for operation in order.operations:
                if operation.tax_id:
                    if operation.tax_id.price_include:
                        total = operation.price_unit * operation.product_uom_qty - operation.x_discount_amount
                        tax_calculate = total - (total / (1 + ((operation.tax_id.amount if operation.tax_id else 0) / 100)))
                        val += tax_calculate
                    # else:
                    #     total = operation.price_unit * operation.product_uom_qty - operation.x_discount_amount
                    #     tax_calculate = total * ((operation.tax_id.amount if operation.tax_id else 0) / 100)
                    #     val += tax_calculate
            for fee in order.fees_lines:
                if fee.tax_id:
                    total = fee.price_unit * fee.product_uom_qty - fee.x_discount_amount
                    tax_calculate = total - (total / (1 + ((fee.tax_id.amount if fee.tax_id else 0) / 100)))
                    val += tax_calculate
            order.amount_tax = val

    def attach_repair(self):
        pdf = self.env.ref('pabs_service.service_report_by_email').render_qweb_pdf(self.id)
        b64_pdf = base64.b64encode(pdf[0])
        return self.env['ir.attachment'].create({
            'name': self.name + '.pdf',
            'type': 'binary',
            'datas': b64_pdf,
            # 'datas_fname': self.sale_order_id.name + '.pdf',
            'store_fname': self.name,
            'res_model': 'repair.order',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

    def action_send_mail(self):
        self.ensure_one()
        repair = self.attach_repair()
        template_id = self.env.ref('pabs_repair.pabs_repair_mail_template_repair_quotation').id
        ctx = {
            'default_model': 'repair.order',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            # 'default_composition_mode': 'comment',
            # 'custom_layout': 'mail.mail_notification_light',
            'default_attachment_ids': [(4, repair.id)]

        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            # 'views': [(repair.id, 'form')],
            # 'view_id': repair.id,
            'target': 'new',
            'context': ctx,
        }

    def action_repair_start(self):
        res = super(Repair, self).action_repair_start()
        self.repair_date = fields.Datetime.now()
        if self.x_task_id:
            self.x_task_id.planned_date_begin = self.repair_date
        return res

    @api.depends('invoice_id')
    def onchange_product_id(self):
        if not self.invoice_id:
            self.invoiced = False

    @api.onchange('product_id')
    def onchange_product_id(self):
        if (self.product_id and self.lot_id and self.lot_id.product_id != self.product_id) or not self.product_id:
            self.lot_id = False
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id

    def compute_timesheet_ids(self):
        for rec in self:
            rec.timesheet_ids = rec.x_task_id.timesheet_ids

    # @api.onchange('product_id')
    # def onchange_product_brand(self):
    #     # if self.product_id.product_brand_id:
    #     self.product_brand = self.product_id.product_brand_id

    def action_repair_end(self):
        res = super(Repair, self).action_repair_end()
        self.x_repair_end_date = fields.Datetime.now()
        if self.x_task_id:
            print(fields.Datetime.now(), 'datetime')
            self.x_task_id.planned_date_end = self.x_repair_end_date
        return res

    def action_repair_invoice_create_for_company(self, group=False):
        grouped_invoices_vals = {}
        repairs = self.filtered(lambda repair: repair.state not in ('draft', 'cancel')
                                               and not repair.invoice_id
                                               and repair.invoice_method == 'warranty')
        for repair in repairs:
            partner_invoice = repair.partner_invoice_id or repair.partner_id
            if not partner_invoice:
                raise UserError(_('You have to select an invoice address in the repair form.'))

            narration = repair.quotation_notes
            currency = repair.pricelist_id.currency_id
            # Fallback on the user company as the 'company_id' is not required.
            company = repair.company_id or self.env.user.company_id

            journal = self.env['account.move'].with_context(force_company=company.id,
                                                            type='out_invoice')._get_default_journal()
            if not journal:
                raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
                    self.company_id.name, self.company_id.id))

            if (partner_invoice.id, currency.id) not in grouped_invoices_vals:
                grouped_invoices_vals[(partner_invoice.id, currency.id)] = []
            current_invoices_list = grouped_invoices_vals[(partner_invoice.id, currency.id)]

            if not group or len(current_invoices_list) == 0:
                fp_id = repair.partner_id.property_account_position_id.id or self.env[
                    'account.fiscal.position'].get_fiscal_position(repair.partner_id.id,
                                                                   delivery_id=repair.address_id.id)
                invoice_vals = {
                    'type': 'out_invoice',
                    'partner_id': partner_invoice.id,
                    'currency_id': currency.id,
                    'narration': narration,
                    'line_ids': [],
                    'invoice_origin': repair.name,
                    'repair_ids': [(4, repair.id)],
                    'invoice_line_ids': [],
                    'fiscal_position_id': fp_id,
                    'x_ticket_id': repair.ticket_id.id,
                }
                current_invoices_list.append(invoice_vals)
            else:
                # if group == True: concatenate invoices by partner and currency
                invoice_vals = current_invoices_list[0]
                invoice_vals['invoice_origin'] += ', ' + repair.name
                invoice_vals['repair_ids'].append((4, repair.id))
                if not invoice_vals['narration']:
                    invoice_vals['narration'] = narration
                else:
                    invoice_vals['narration'] += '\n' + narration

            # Create invoice lines from operations.
            for operation in repair.operations.filtered(lambda op: op.type == 'add'):
                if group:
                    name = repair.name + '-' + operation.name
                else:
                    name = operation.name

                account = operation.product_id.product_tmpl_id._get_product_accounts()['income']
                if not account:
                    raise UserError(_('No account defined for product "%s".') % operation.product_id.name)

                invoice_line_vals = {
                    'name': name,
                    'account_id': account.id,
                    'quantity': operation.product_uom_qty,
                    'tax_ids': [(6, 0, operation.tax_id.ids)],
                    'product_uom_id': operation.product_uom.id,
                    'price_unit': operation.price_unit,
                    'product_id': operation.product_id.id,
                    'repair_line_ids': [(4, operation.id)],
                    'analytic_account_id': repair.project_id.analytic_account_id.id or False,
                }

                if currency == company.currency_id:
                    balance = -(operation.product_uom_qty * operation.price_unit)
                    invoice_line_vals.update({
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                    })
                else:
                    amount_currency = -(operation.product_uom_qty * operation.price_unit)
                    balance = currency._convert(amount_currency, self.company_id.currency_id, self.company_id,
                                                fields.Date.today())
                    invoice_line_vals.update({
                        'amount_currency': amount_currency,
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                        'currency_id': currency.id,
                    })
                invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

            # Create invoice lines from fees.
            for fee in repair.fees_lines:
                if group:
                    name = repair.name + '-' + fee.name
                else:
                    name = fee.name

                if not fee.product_id:
                    raise UserError(_('No product defined on fees.'))

                account = fee.product_id.product_tmpl_id._get_product_accounts()['income']
                if not account:
                    raise UserError(_('No account defined for product "%s".') % fee.product_id.name)

                invoice_line_vals = {
                    'name': name,
                    'account_id': account.id,
                    'quantity': fee.product_uom_qty,
                    'tax_ids': [(6, 0, fee.tax_id.ids)],
                    'product_uom_id': fee.product_uom.id,
                    'price_unit': fee.price_unit,
                    'product_id': fee.product_id.id,
                    'repair_fee_ids': [(4, fee.id)],
                    'analytic_account_id': repair.project_id.analytic_account_id.id or False,
                }

                if currency == company.currency_id:
                    balance = -(fee.product_uom_qty * fee.price_unit)
                    invoice_line_vals.update({
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                    })
                else:
                    amount_currency = -(fee.product_uom_qty * fee.price_unit)
                    balance = currency._convert(amount_currency, self.company_id.currency_id, self.company_id,
                                                fields.Date.today())
                    invoice_line_vals.update({
                        'amount_currency': amount_currency,
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                        'currency_id': currency.id,
                    })
                invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

        # Create invoices.
        invoices_vals_list = []
        for invoices in grouped_invoices_vals.values():
            for invoice in invoices:
                invoices_vals_list.append(invoice)
        self.env['account.move'].with_context(default_type='out_invoice', default_sale_order_type='service').create(
            invoices_vals_list)

        repairs.write({'invoiced': True})
        repairs.mapped('operations').filtered(lambda op: op.type == 'add').write({'invoiced': True})
        repairs.mapped('fees_lines').write({'invoiced': True})

        return dict((repair.id, repair.invoice_id.id) for repair in repairs)

    def action_repair_invoice_create_for_none(self, group=False):
        SALE_ORDER_TYPE = {
            'cash_memo': self.env.ref('pabs_account.type_cashmemo').ids,
            'credit_sale': self.env.ref('pabs_account.type_credit').ids,
            'paid_on_delivery': self.env.ref('pabs_account.type_pod').ids,
            'advance_payment': self.env.ref('pabs_account.type_cashinvoice').ids,
            'service': self.env.ref('pabs_account.type_service').ids,

        }
        grouped_invoices_vals = {}
        repairs = self.filtered(lambda repair: repair.state not in ('draft', 'cancel')
                                               and not repair.invoice_id
                                               and repair.invoice_method == 'none')
        for repair in repairs:
            partner_invoice = repair.partner_invoice_id or repair.partner_id
            if not partner_invoice:
                raise UserError(_('You have to select an invoice address in the repair form.'))

            narration = repair.quotation_notes
            currency = repair.pricelist_id.currency_id
            # Fallback on the user company as the 'company_id' is not required.
            company = repair.company_id or self.env.user.company_id

            journal = self.env['account.move'].with_context(force_company=company.id,
                                                            type='out_invoice')._get_default_journal()
            if not journal:
                raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
                    self.company_id.name, self.company_id.id))

            if (partner_invoice.id, currency.id) not in grouped_invoices_vals:
                grouped_invoices_vals[(partner_invoice.id, currency.id)] = []
            current_invoices_list = grouped_invoices_vals[(partner_invoice.id, currency.id)]

            if not group or len(current_invoices_list) == 0:
                fp_id = repair.partner_id.property_account_position_id.id or self.env[
                    'account.fiscal.position'].get_fiscal_position(repair.partner_id.id,
                                                                   delivery_id=repair.address_id.id)
                invoice_vals = {
                    'type': 'out_invoice',
                    'partner_id': partner_invoice.id,
                    'currency_id': currency.id,
                    'narration': narration,
                    'line_ids': [],
                    'invoice_origin': repair.name,
                    'repair_ids': [(4, repair.id)],
                    'invoice_line_ids': [],
                    'fiscal_position_id': fp_id,
                    'sale_order_type': 'service',
                    'x_ticket_id': repair.ticket_id.id,
                }
                journals = self.env['account.journal']
                journal = journals.search([('x_sale_order_type_ids', 'in', SALE_ORDER_TYPE['service'])], limit=1).id
                if journal:
                    invoice_vals['journal_id'] = journal
                current_invoices_list.append(invoice_vals)
            else:
                # if group == True: concatenate invoices by partner and currency
                invoice_vals = current_invoices_list[0]
                invoice_vals['invoice_origin'] += ', ' + repair.name
                invoice_vals['repair_ids'].append((4, repair.id))
                if not invoice_vals['narration']:
                    invoice_vals['narration'] = narration
                else:
                    invoice_vals['narration'] += '\n' + narration

            # Create invoice lines from operations.
            for operation in repair.operations.filtered(lambda op: op.type == 'add'):
                if group:
                    name = repair.name + '-' + operation.name
                else:
                    name = operation.name

                account = operation.product_id.product_tmpl_id._get_product_accounts()['income']
                if not account:
                    raise UserError(_('No account defined for product "%s".') % operation.product_id.name)

                invoice_line_vals = {
                    'name': name,
                    'account_id': account.id,
                    'quantity': operation.product_uom_qty,
                    'tax_ids': [(6, 0, operation.tax_id.ids)],
                    'product_uom_id': operation.product_uom.id,
                    'price_unit': 0,
                    'product_id': operation.product_id.id,
                    'repair_line_ids': [(4, operation.id)],
                    'analytic_account_id': repair.project_id.analytic_account_id.id or False,
                }

                if currency == company.currency_id:
                    balance = -(operation.product_uom_qty * operation.price_unit)
                    invoice_line_vals.update({
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                    })
                else:
                    amount_currency = -(operation.product_uom_qty * operation.price_unit)
                    balance = currency._convert(amount_currency, self.company_id.currency_id, self.company_id,
                                                fields.Date.today())
                    invoice_line_vals.update({
                        'amount_currency': amount_currency,
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                        'currency_id': currency.id,
                    })
                invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

            # Create invoice lines from fees.
            for fee in repair.fees_lines:
                if group:
                    name = repair.name + '-' + fee.name
                else:
                    name = fee.name

                if not fee.product_id:
                    raise UserError(_('No product defined on fees.'))

                account = fee.product_id.product_tmpl_id._get_product_accounts()['income']
                if not account:
                    raise UserError(_('No account defined for product "%s".') % fee.product_id.name)

                invoice_line_vals = {
                    'name': name,
                    'account_id': account.id,
                    'quantity': fee.product_uom_qty,
                    'tax_ids': [(6, 0, fee.tax_id.ids)],
                    'product_uom_id': fee.product_uom.id,
                    'price_unit': 0,
                    'product_id': fee.product_id.id,
                    'repair_fee_ids': [(4, fee.id)],
                    'analytic_account_id': repair.project_id.analytic_account_id.id or False,
                }

                if currency == company.currency_id:
                    balance = -(fee.product_uom_qty * fee.price_unit)
                    invoice_line_vals.update({
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                    })
                else:
                    amount_currency = -(fee.product_uom_qty * fee.price_unit)
                    balance = currency._convert(amount_currency, self.company_id.currency_id, self.company_id,
                                                fields.Date.today())
                    invoice_line_vals.update({
                        'amount_currency': amount_currency,
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                        'currency_id': currency.id,
                    })
                invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

        # Create invoices.
        invoices_vals_list = []
        for invoices in grouped_invoices_vals.values():
            for invoice in invoices:
                invoices_vals_list.append(invoice)
        self.env['account.move'].with_context(default_type='out_invoice', default_sale_order_type='service').create(
            invoices_vals_list)

        repairs.write({'invoiced': True})
        repairs.mapped('operations').filtered(lambda op: op.type == 'add').write({'invoiced': True})
        repairs.mapped('fees_lines').write({'invoiced': True})

        return dict((repair.id, repair.invoice_id.id) for repair in repairs)

    def action_repair_confirm(self):
        """ Repair order state is set to 'To be invoiced' when invoice method
        is 'Before repair' else state becomes 'Confirmed'.
        @param *arg: Arguments
        @return: True
        """
        if self.filtered(lambda repair: repair.state != 'draft'):
            raise UserError(_("Only draft repairs can be confirmed."))
        before_repair = self.filtered(lambda repair: repair.invoice_method == 'b4repair')
        before_repair.write({'state': '2binvoiced'})
        to_confirm = self - before_repair
        to_confirm_operations = to_confirm.mapped('operations')
        to_confirm_operations.write({'state': 'confirmed'})
        to_confirm.write({'state': 'confirmed'})
        self.create_repair_task()
        return True

    def create_repair_task(self):
        project = self.x_repair_project.id
        created_task = self.env['project.task'].create({'name': self.name,
                                                        'project_id': project,
                                                        'partner_id': self.partner_id.id,
                                                        'x_repair_id': self.id})
        self.x_task_id = created_task

    def action_task_form_view(self):
        self.ensure_one()
        return {
            'name': _('Task From Repair'),
            'res_model': 'project.task',
            'res_id': self.x_task_id.id,
            'view_mode': 'form',
            'views': [
                (self.env.ref('project.view_task_form2').id, 'form'),
            ],
            'type': 'ir.actions.act_window'}

    # def _create_invoices(self):
    #     res = super(Repair, self)._create_invoices()
    #     invoice = self.env['account.move'].search([('id', '=', res[self.id])])
    #     if invoice and not invoice.sale_order_type:
    #         invoice.write({'sale_order_type': 'service', 'invoice_date': self.x_repair_end_date, 'x_sale_service_type': self.x_sale_service_type})
    #     return res


    def _create_invoices(self, group=False):
        """ Creates invoice(s) for repair order.
        @param group: It is set to true when group invoice is to be generated.
        @return: Invoice Ids.
        """
        grouped_invoices_vals = {}
        repairs = self.filtered(lambda repair: repair.state not in ('draft', 'cancel')
                                               and not repair.invoice_id
                                               and repair.invoice_method != 'none')
        for repair in repairs:
            partner_invoice = repair.partner_invoice_id or repair.partner_id
            if not partner_invoice:
                raise UserError(_('You have to select an invoice address in the repair form.'))

            narration = repair.quotation_notes
            currency = repair.pricelist_id.currency_id
            # Fallback on the user company as the 'company_id' is not required.
            company = repair.company_id or self.env.user.company_id

            journal = self.env['account.move'].with_context(force_company=company.id, type='out_invoice')._get_default_journal()
            if not journal:
                raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

            if (partner_invoice.id, currency.id) not in grouped_invoices_vals:
                grouped_invoices_vals[(partner_invoice.id, currency.id)] = []
            current_invoices_list = grouped_invoices_vals[(partner_invoice.id, currency.id)]

            if not group or len(current_invoices_list) == 0:
                fp_id = repair.partner_id.property_account_position_id.id or self.env['account.fiscal.position'].get_fiscal_position(repair.partner_id.id, delivery_id=repair.address_id.id)
                invoice_vals = {
                    'type': 'out_invoice',
                    'partner_id': partner_invoice.id,
                    'currency_id': currency.id,
                    'narration': narration,
                    'line_ids': [],
                    'invoice_origin': repair.name,
                    'repair_ids': [(4, repair.id)],
                    'invoice_line_ids': [],
                    'fiscal_position_id': fp_id,
                    'sale_order_type': 'service',
                    'invoice_date': self.x_repair_end_date,
                    'x_sale_service_type': self.x_sale_service_type

                }
                current_invoices_list.append(invoice_vals)
            else:
                # if group == True: concatenate invoices by partner and currency
                invoice_vals = current_invoices_list[0]
                invoice_vals['invoice_origin'] += ', ' + repair.name
                invoice_vals['repair_ids'].append((4, repair.id))
                if not invoice_vals['narration']:
                    invoice_vals['narration'] = narration
                else:
                    invoice_vals['narration'] += '\n' + narration

            # Create invoice lines from operations.
            for operation in repair.operations.filtered(lambda op: op.type == 'add'):
                if group:
                    name = repair.name + '-' + operation.name
                else:
                    name = operation.name

                account = operation.product_id.product_tmpl_id._get_product_accounts()['income']
                if not account:
                    raise UserError(_('No account defined for product "%s".') % operation.product_id.name)

                invoice_line_vals = {
                    'name': name,
                    'account_id': account.id,
                    'quantity': operation.product_uom_qty,
                    'tax_ids': [(6, 0, operation.tax_id.ids)],
                    'product_uom_id': operation.product_uom.id,
                    'price_unit': operation.price_unit,
                    'product_id': operation.product_id.id,
                    'repair_line_ids': [(4, operation.id)],
                    'analytic_account_id': repair.project_id.analytic_account_id.id or False,
                }

                if currency == company.currency_id:
                    balance = -(operation.product_uom_qty * operation.price_unit)
                    invoice_line_vals.update({
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                    })
                else:
                    amount_currency = -(operation.product_uom_qty * operation.price_unit)
                    balance = currency._convert(amount_currency, self.company_id.currency_id, self.company_id, fields.Date.today())
                    invoice_line_vals.update({
                        'amount_currency': amount_currency,
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                        'currency_id': currency.id,
                    })
                invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

            # Create invoice lines from fees.
            for fee in repair.fees_lines:
                if group:
                    name = repair.name + '-' + fee.name
                else:
                    name = fee.name

                if not fee.product_id:
                    raise UserError(_('No product defined on fees.'))

                account = fee.product_id.product_tmpl_id._get_product_accounts()['income']
                if not account:
                    raise UserError(_('No account defined for product "%s".') % fee.product_id.name)

                invoice_line_vals = {
                    'name': name,
                    'account_id': account.id,
                    'quantity': fee.product_uom_qty,
                    'tax_ids': [(6, 0, fee.tax_id.ids)],
                    'product_uom_id': fee.product_uom.id,
                    'price_unit': fee.price_unit,
                    'product_id': fee.product_id.id,
                    'repair_fee_ids': [(4, fee.id)],
                    'analytic_account_id': repair.project_id.analytic_account_id.id or False,
                }

                if currency == company.currency_id:
                    balance = -(fee.product_uom_qty * fee.price_unit)
                    invoice_line_vals.update({
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                    })
                else:
                    amount_currency = -(fee.product_uom_qty * fee.price_unit)
                    balance = currency._convert(amount_currency, self.company_id.currency_id, self.company_id,
                                                fields.Date.today())
                    invoice_line_vals.update({
                        'amount_currency': amount_currency,
                        'debit': balance > 0.0 and balance or 0.0,
                        'credit': balance < 0.0 and -balance or 0.0,
                        'currency_id': currency.id,
                    })
                invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

        # Create invoices.
        invoices_vals_list = []
        for invoices in grouped_invoices_vals.values():
            for invoice in invoices:
                invoices_vals_list.append(invoice)
        self.env['account.move'].with_context(default_type='out_invoice').create(invoices_vals_list)

        repairs.write({'invoiced': True})
        repairs.mapped('operations').filtered(lambda op: op.type == 'add').write({'invoiced': True})
        repairs.mapped('fees_lines').write({'invoiced': True})

        return dict((repair.id, repair.invoice_id.id) for repair in repairs)

    @api.onchange('partner_id', 'invoice_method', 'warranty_state')
    def onchange_partner_id(self):
        ticket_type = self.ticket_id.ticket_type_id.id
        comeback = self.env.ref('pabs_repair.comeback').id
        if not self.partner_id:
            self.address_id = False
            self.partner_invoice_id = False
            if self.warranty_state == 'Running' and self.invoice_method == 'warranty':
                self.partner_invoice_id = self.product_brand.partner_id
            elif self.warranty_state == 'Extended' and self.invoice_method == 'warranty':
                self.partner_invoice_id = self.ticket_id.warranty_sequence.x_warranty_agent
        else:
            addresses = self.partner_id.address_get(['delivery', 'invoice', 'contact'])
            self.address_id = addresses['delivery'] or addresses['contact']
            self.partner_invoice_id = addresses['invoice']
            if self.warranty_state == 'Running' and self.invoice_method == 'warranty':
                self.partner_invoice_id = self.product_brand.partner_id
            elif self.warranty_state == 'Extended' and self.invoice_method == 'warranty':
                self.partner_invoice_id = self.ticket_id.warranty_sequence.x_warranty_agent
        if ticket_type and ticket_type == comeback and self.warranty_state in ['Extended', 'Expired', False]:
            self.partner_invoice_id = self.company_id.partner_id

    @api.onchange('partner_invoice_id')
    def x_onchange_partner_invoice_id(self):
        if not self.partner_invoice_id:
            self.pricelist_id = self.env['product.pricelist'].search([], limit=1).id
        else:
            self.pricelist_id = self.partner_invoice_id.property_product_pricelist


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    repair_id = fields.Many2one('repair.order', string="Repair Order", copy=False)


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'
    x_ticket_id = fields.Many2one('helpdesk.ticket', string='Related Helpdesk Ticket')
