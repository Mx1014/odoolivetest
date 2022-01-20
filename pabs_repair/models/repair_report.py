import base64
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from odoo import tools


class Repair(models.Model):
    _name = 'repair.fsm.report'
    _description = "Repair FSM Report"
    _auto = False


    name = fields.Char('Reference', readonly=True)
    ticket_name = fields.Many2one('helpdesk.ticket', 'Ticket', readonly=True)
    task_name = fields.Char('Task', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True)
    # product_tmp_id = fields.Many2one('product.template', string="Product Template", readonly=True)
    product_id = fields.Many2one('product.product', string="Product", readonly=True)
    category = fields.Many2one('service.category', string="Category", readonly=True)
    date = fields.Date(string="Date", readonly=True)
    product_brand = fields.Many2one('product.brand', string="Brand", readonly=True)
    # repair_id = fields.Many2one('repair.order', string="Repair Order", readonly=True)
    delivery_address_id = fields.Many2one('res.partner', string="Delivery Address", readonly=True)
    warranty_expiration_date = fields.Date(string="Warranty Expiration", readonly=True)
    state = fields.Many2one('helpdesk.stage', string="Status", readonly=True)
    total_amount = fields.Monetary(string="Service Amount", readonly=True)
    invoiced_amount = fields.Monetary(string="Total Invoiced", readonly=True)
    due_amount = fields.Monetary(string="Due Amount", readonly=True)
    invoice_address = fields.Many2one('res.partner', string="Invoicing Address", readonly=True)
    warranty_state = fields.Selection([
        ('Running', 'Running'),
        ('Extended', 'Extended'),
        ('Expired', 'Expired'),
    ],
        string='Warranty State', readonly=True)
    invoice_number = fields.Many2one('account.move', string="Invoice Number", readonly=True)
    invoice_date = fields.Date(string="Invoice Date", readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.company_id.currency_id, string="Currency")
    team = fields.Char(string="Technician/Team", readonly=True)
    service_type = fields.Char(string="Service Type", readonly=True)
    ticket_type = fields.Many2one('helpdesk.ticket.type', string="Ticket Type", readonly=True)
    invoice_payment_state = fields.Selection(selection=[
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'paid')
    ], string='Payment Status', readonly=True)
    phone = fields.Char(string="Phone", readonly=True)

    def init(self):
        # self._table = ''
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            r.id as id,
            r.name as name,
            t.id as ticket_name,
            p.id as product_id,
            partner.id as partner_id,
            partner.phone as phone,
            r.address_id as delivery_address_id,
            r.guarantee_limit as warranty_expiration_date,
            t.stage_id as state,
            r.partner_invoice_id as invoice_address,
            e.name as team,
            t.ticket_type_id as ticket_type,
            r.amount_total as total_amount,
            r.warranty_state as warranty_state,
            move.id as invoice_number,
            move.invoice_date as invoice_date,
            move.amount_total as invoiced_amount,
            move.amount_residual as due_amount,
            move.invoice_payment_state as invoice_payment_state,
            r.x_service_type as service_type,
            t.create_date as date,
            p.x_service_category as category,
            p.product_brand_id as product_brand
        """

        from_ = """
                        repair_order r
                           left join helpdesk_ticket t on (r.ticket_id=t.id)
                           left join product_product p on (r.product_id=p.id)
                           left join res_partner partner on (r.partner_id=partner.id)
                           left join account_move move on (r.invoice_id=move.id)
                           left join hr_employee e on (r.technician=e.id)
                           UNION ALL
                           SELECT
                                task.id as id,
                                sale.name as name,
                                tic.id as ticket_name,
                                tic.product_id as product_id,
                                task.partner_id as partner_id,
                                partner.phone as phone,
                                task.partner_id as delivery_address_id,
                                task.x_warranty_end_date as warranty_expiration_date,
                                tic.stage_id as state,
                                task.partner_id as invoice_address,
                                log.name as team, 
                                tic.ticket_type_id as ticket_type,
                                sale.amount_total as total_amount,
                                task.x_warranty_state as warranty_state,
                                move.id as invoice_number,
                                move.invoice_date as invoice_date,
                                move.amount_total as invoiced_amount,
                                move.amount_residual as due_amount,
                                move.invoice_payment_state as invoice_payment_state,
                                task.x_service_type as service_type,
                                tic.create_date as date,
                                pro.x_service_category as category,
                                pro.product_brand_id as product_brand
                            FROM project_task task left 
                            join helpdesk_ticket tic on (task.helpdesk_ticket_id=tic.id)
                            join project_task_batch batch on (task.x_batch_id=batch.id)
                            join logistics_team log on (task.x_team_id=log.id)
                            join sale_order sale on (task.sale_order_id=sale.id)
                            join res_partner partner on (task.partner_id=partner.id)
                            join product_product pro on (task.x_product_id=pro.id)
                            left join account_move move on (task.x_invoices=move.id)
                            

                        %s
                """ % from_clause

        groupby_ = """%s""" % (groupby)

        return '%s (SELECT %s FROM %s)' % (with_, select_, from_)
