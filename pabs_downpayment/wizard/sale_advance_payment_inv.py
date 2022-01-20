from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"


    def _default_order_lines(self):
        lines = self.env['sale.order.line']
        payment_line = lines.search([('order_id', '=', self._context.get('active_id')), ('x_lineid', '!=', 0)])
        sale_order_line = lines.search([('order_id', '=', self._context.get('active_id')), ('is_downpayment', '=', False), ('id', 'not in', payment_line.mapped('x_lineid')), ('display_type', 'not in', ['line_section', 'line_note'])])
        return sale_order_line

    @api.onchange('advance_payment_method')
    def _onchange_get_order_line(self):
        sale_order_line = self.env['sale.order.line'].search(
            [('order_id', '=', self._context.get('active_id')), ('is_downpayment', '=', True), ('x_lineid', '!=', 0)])
        index = []
        res = {}
        # test = sale_order_line.ids
        if self.advance_payment_method == 'specific':
            for ids in sale_order_line:
                index.append(ids.x_lineid)
            self.x_os_line = [(6, 0, self.env['sale.order.line'].search([('id', 'not in', index), ('order_id', '=', self._context.get('active_id')), ('is_downpayment', '=', False), ('qty_invoiced', '=', 0), ('display_type', 'not in', ['line_section', 'line_note'])]).ids)]
            res['domain'] = {'x_os_line': [('id', 'not in', index), ('order_id', '=', self._context.get('active_id')), ('is_downpayment', '=', False), ('qty_invoiced', '=', 0), ('display_type', 'not in', ['line_section', 'line_note'])]}
            return res

    def _default_date(self):
        return fields.Date.today()

    def _default_so_type(self):
        sale_order = self.env['sale.order'].search([('id', '=', self._context.get('active_id'))])
        return sale_order.sale_order_type

    advance_payment_method = fields.Selection(selection_add=[('specific', 'Specific Product')])
    x_os_line = fields.Many2many('sale.order.line', string='Order Line', default=_default_order_lines)
    x_sale_order_type = fields.Selection(string='Sale Order Type', readonly=True,
                                       selection=[('cash_memo', 'Cash Memo'), ('credit_sale', 'Credit Sale'),
                                                  ('paid_on_delivery', 'Paid on Delivery'),
                                                  ('advance_payment', 'Cash Invoice'), ('service', 'Service')], default=_default_so_type)

    x_invoice_date = fields.Date(string="Date", default=_default_date)


    @api.onchange('advance_payment_method')
    def default_delivery_date(self):
        if self.advance_payment_method == 'delivered':
            picking = self.env['stock.picking'].search([('sale_id', '=', self._context.get('active_id')), ('state', '=', 'done')], order="date_done asc")
            for picking in picking:
                #if picking.sale_id.sale_order_type != 'cash_memo':
                self.x_invoice_date = picking.date_done.date()

    def default_delivery_date_return(self):
        if self.advance_payment_method == 'delivered':
            picking = self.env['stock.picking'].search([('sale_id', '=', self._context.get('active_id')), ('state', '=', 'done')], order="date_done asc")
            for picking in picking:
                #if picking.sale_id.sale_order_type != 'cash_memo':
                return picking.date_done.date()

    @api.onchange('x_os_line')
    def line_amount_get(self):
        for advance in self:
            total = 0
            amount_residual = 0.0
            #advance_total = 0
            for line in advance.x_os_line:
                total = total + line.price_total
                amount_residual = line.order_id.x_downpayment_amount #x_amount_residual
                # if line.price_subtotal != self.env['sale.order.line'].search([('x_lineid', '=', line.id)]).price_unit:
                #     advance_total = self.env['sale.order.line'].search([('x_lineid', '=', line.id)]).price_unit
            advance.fixed_amount = amount_residual
            advance.amount = amount_residual

    # def downpayment_line_get(self, order_id, amount):
    #     lines = self.env['sale.order.line'].search([('id','=', order_id.id)])
    #     for line in lines:
    #         line.x_down_payment_amount = amount


    # def _prepare_so_line(self, order, analytic_tag_ids, tax_ids, amount):
    #     res = super(SaleAdvancePaymentInv, self)._prepare_so_line(order, analytic_tag_ids, tax_ids, amount)
    #     res['name'] = 'Down Payment: %s' % order.name
    #     res['order_id'] = order.order_id.id
    #     res['x_lineid'] = order.id
    #     #res['x_down_payment_amount'] = order.price_subtotal
    #     res['sequence'] = order.sequence + 1
    #     res['tax_id'] = [(6, 0, order.tax_id.ids)]
    #     print(amount)
    #     return res

    def _prepare_so_line(self, order, analytic_tag_ids, tax_ids, amount):
        context = {'lang': order.order_id.partner_id.lang}
        so_values = {
            'name': '%s' % order.name,
            'price_unit': amount,
            'product_uom_qty': 0.0,
            'order_id': order.order_id.id,
            'discount': 0.0,
            'x_lineid': order.id,
            'product_uom': self.product_id.uom_id.id,
            'product_id': self.product_id.id,
            'analytic_tag_ids': analytic_tag_ids,
            'tax_id': [(6, 0, order.tax_id.ids)],
            'sequence': order.sequence + 1,
            'is_downpayment': True,
        }
        del context
        return so_values

    def _prepare_so_pod_line(self, order, analytic_tag_ids, tax_ids, amount, qty, discount_amount, disc):
        context = {'lang': order.order_id.partner_id.lang}
        so_values = {
            'name': '%s' % order.name,
            'price_unit': amount,
            'product_uom_qty': 0.0,
            'x_qty': qty,
            'order_id': order.order_id.id,
            'x_discount_amount': discount_amount,
            'discount': disc,
            'x_lineid': order.id,
            'product_uom': self.product_id.uom_id.id,
            'product_id': self.product_id.id,
            'analytic_tag_ids': analytic_tag_ids,
            'tax_id': [(6, 0, order.tax_id.ids)],
            'sequence': order.sequence + 1,
            'is_downpayment': True,
        }
        del context
        return so_values

    def _prepare_so_line_fixed(self, order, analytic_tag_ids, tax_ids, amount):
        context = {'lang': order.partner_id.lang}
        so_values = {
            'name': 'Down Payment',
            'price_unit': amount,
            'product_uom_qty': 0.0,
            'order_id': order.id,
            'discount': 0.0,
            'x_lineid': order.id,
            'product_uom': self.product_id.uom_id.id,
            'product_id': self.product_id.id,
            'analytic_tag_ids': analytic_tag_ids,
            'tax_id': [(6, 0, tax_ids)],
            #'sequence': order.sequence + 1,
            'is_downpayment': True,
        }
        del context
        return so_values

    def _prepare_so_line_percentage(self, order, analytic_tag_ids, tax_ids, amount):
        context = {'lang': order.partner_id.lang}
        so_values = {
            'name':  _("Down payment of %s%%") % (self.amount),
            'price_unit': amount,
            'product_uom_qty': 0.0,
            'order_id': order.id,
            'discount': 0.0,
            'x_lineid': order.id,
            'product_uom': self.product_id.uom_id.id,
            'product_id': self.product_id.id,
            'analytic_tag_ids': analytic_tag_ids,
            'tax_id': [(6, 0, tax_ids)],
            #'sequence': order.sequence + 1,
            'is_downpayment': True,
        }
        del context
        return so_values

    # def _prepare_invoice_values(self, order, name, amount, so_line):
    #     res = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, name, amount, so_line)
    #     so_line_value = []
    #     for line in so_line:
    #         so_line_value.append((0, 0, {
    #             'name': name,
    #             'price_unit': amount,
    #             'quantity': 1.0,
    #             'product_id': self.product_id.id,
    #             'product_uom_id': line.product_uom.id,
    #             'tax_ids': [(6, 0, line.tax_id.ids)],
    #             'sale_line_ids': [(6, 0, [line.id])],
    #             'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
    #             'analytic_account_id': order.analytic_account_id.id or False,
    #         }))
    #
    #     res['invoice_line_ids'] = so_line_value
    #     print(res['invoice_line_ids'])
    #     return res

    def _prepare_invoice_values(self, order, name, amount, so_line):
        print(self.x_invoice_date, 'self.x_invoice_date')
        invoice_vals = {
            'ref': order.client_order_ref,
            'type': 'out_invoice',
            'invoice_origin': order.name,
            'x_sale_id': order.id,
            'invoice_user_id': order.user_id.id,
            'narration': order.note,
            'invoice_date': self.x_invoice_date or fields.Date.today(),
            'partner_id': order.partner_invoice_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'partner_shipping_id': order.partner_shipping_id.id,
            'currency_id': order.pricelist_id.currency_id.id,
            'invoice_payment_ref': order.reference,
            'invoice_payment_term_id': order.payment_term_id.id,
            'invoice_partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
            'team_id': order.team_id.id,
            'campaign_id': order.campaign_id.id,
            'medium_id': order.medium_id.id,
            'source_id': order.source_id.id,
            'sale_order_type': order.sale_order_type,
        }
        so_line_value = []
        if order.sale_order_type not in ['paid_on_delivery', 'credit_sale', 'advance_payment'] and (self.advance_payment_method != 'fixed' or self.advance_payment_method != 'percentage'):
            for line in so_line:
                #print(line.price_unit)
                so_line_value.append((0, 0, {
                    'name': line.name,
                    'price_unit': line.price_unit,
                    'quantity': 1.0,
                    'product_id': self.product_id.id,
                    'product_uom_id': line.product_uom.id,
                    'tax_ids': [(6, 0, line.tax_id.ids)],
                    'sale_line_ids': [(6, 0, [line.id])],
                    'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                    'analytic_account_id': order.analytic_account_id.id or False,
                }))
        elif order.sale_order_type == 'service' and self.advance_payment_method == 'fixed':
            print(so_line)
            so_line_value.append((0, 0, {
                'name': 'Down Payment',
                'price_unit': self.fixed_amount,
                'quantity': 1.0,
                'product_id': self.product_id.id,
                'product_uom_id': so_line.product_uom.id,
                'tax_ids': [(6, 0, so_line.tax_id.ids)],
                'sale_line_ids': [(6, 0, [so_line.id])],
                'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'analytic_account_id': order.analytic_account_id.id or False,
            }))
        elif order.sale_order_type in ['paid_on_delivery', 'credit_sale', 'advance_payment'] and self.advance_payment_method == 'fixed':
            for line in so_line:
                so_line_value.append((0, 0, {
                    'name': line.name,
                    'price_unit': line.price_unit,
                    'quantity': line.x_qty,
                    'discount': line.discount,
                    'product_id': self.product_id.id,
                    'product_uom_id': line.product_uom.id,
                    'tax_ids': [(6, 0, line.tax_id.ids)],
                    'sale_line_ids': [(6, 0, [line.id])],
                    'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                    'analytic_account_id': order.analytic_account_id.id or False,
                }))
        elif order.sale_order_type == 'service' and self.advance_payment_method == 'percentage':
            print(so_line)
            so_line_value.append((0, 0, {
                'name':  _("Down payment of %s%%") % (self.amount),
                'price_unit': order.x_amount_residual * self.amount / 100,
                'quantity': 1.0,
                'product_id': self.product_id.id,
                'product_uom_id': so_line.product_uom.id,
                'tax_ids': [(6, 0, so_line.tax_id.ids)],
                'sale_line_ids': [(6, 0, [so_line.id])],
                'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'analytic_account_id': order.analytic_account_id.id or False,
            }))

        invoice_vals['invoice_line_ids'] = so_line_value
        return invoice_vals

    def reverse_moves(self, move_id):
        moves = move_id

        # Create default values.
        default_values_list = []
        for move in moves:
            default_values_list.append({
                'ref': _('Reversal of: %s') % (move.name),
                'date': move.date,
                'invoice_date': move.is_invoice(include_receipts=True) and (move.date) or False,
                'journal_id': move.journal_id.id,
                'invoice_payment_term_id': None,
                'auto_post': True if move.date > fields.Date.context_today(self) else False,
            })

        if any([vals.get('auto_post', False) for vals in default_values_list]):
            moves._reverse_moves(default_values_list)
        else:
            moves._reverse_moves(default_values_list, cancel=True)


    def _create_invoice(self, order, so_line, amount):
        if (self.advance_payment_method == 'percentage' and self.amount <= 0.00) or (self.advance_payment_method == 'fixed' and self.fixed_amount <= 0.00):
            raise UserError(_('The value of the down payment amount must be positive.'))

        # amount, name = self._get_advance_details(order)
        name = _('Down Payment')
        # lines = []
        # for line in so_line:
        #     lines.append(line)
        # print(lines)
        # print(so_line)

        invoice_vals = self._prepare_invoice_values(order, name, amount, so_line)
        if self.advance_payment_method == 'fixed':
            invoice_vals['journal_id'] = self.env['ir.default'].sudo().get('account.move', 'x_down_payment_journal'),



        if order.fiscal_position_id:
            invoice_vals['fiscal_position_id'] = order.fiscal_position_id.id
        invoice = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)
        invoice.action_post()
        #invoice.action_register_payment_custom()
        invoice.message_post_with_view('mail.message_origin_link',
                    values={'self': invoice, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return invoice

    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        down_payment = []
        invoice_to_pay = 0
        if self.advance_payment_method == 'delivered':
            sale_orders.x_so_line = self.x_os_line.ids
            sale_orders.x_invoice_date = self.default_delivery_date_return() or fields.Date.today()
            move = sale_orders._create_invoices(final=self.deduct_down_payments)
            for order in sale_orders:
                if order.sale_order_type == 'cash_memo':
                    move.action_post()
                    return move.action_register_payment_custom()
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id', self.product_id.id)

            sale_line_obj = self.env['sale.order.line']

            # for order in sale_orders:
            #     amount, name = self._get_advance_details(order)
            order_id = 0
            amount = 0
            # if (sale_orders.sale_order_type == 'advance_payment' and self.advance_payment_method == 'fixed') or (sale_orders.sale_order_type == 'service' and self.advance_payment_method == 'specific'):
            #     for order in self.x_os_line:
            #         amount = order.price_total
            #         # if len(self.x_os_line) == 1:
            #         #    if amount != self.env['sale.order.line'].search([('x_lineid', '=', order.id)]).price_unit:
            #         #        amount = order.price_subtotal - self.env['sale.order.line'].search([('x_lineid', '=', order.id)]).price_unit
            #         name = _('Down Payment')
            #         if amount > sale_orders.x_downpayment_amount:
            #             raise UserError(_('The value of the down payment amount must be less than or equal Total.'))
            #         if self.product_id.invoice_policy != 'order':
            #             raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
            #         if self.product_id.type != 'service':
            #             raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
            #         taxes = self.product_id.taxes_id.filtered(lambda r: not order.order_id.company_id or r.company_id == order.order_id.company_id)
            #         if order.order_id.fiscal_position_id and taxes:
            #             tax_ids = order.order_id.fiscal_position_id.map_tax(taxes, self.product_id, order.order_id.partner_shipping_id).ids
            #         else:
            #             tax_ids = taxes.ids
            #         context = {'lang': order.order_id.partner_id.lang}
            #         analytic_tag_ids = []
            #         #for line in order.order_line:
            #         analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in order.analytic_tag_ids]
            #
            #         so_line_values = self._prepare_so_line(order, analytic_tag_ids, tax_ids, amount)
            #         down_payment.append(so_line_values)
            #         order_id = order.order_id
            #         #so_line = sale_line_obj.create(so_line_values)
            #         #self.downpayment_line_get(order, amount)
            #     so_line = sale_line_obj.create(down_payment)
            #     del context
            #     invoice_to_pay = self._create_invoice(order_id, so_line, amount)
            if sale_orders.sale_order_type in ['paid_on_delivery', 'credit_sale', 'advance_payment'] and self.advance_payment_method == 'fixed':
                if not self.x_os_line:
                    raise UserError(_('No need create down-payment.'))
                for order in self.x_os_line:
                    amount = order.price_unit
                    qty = order.product_uom_qty
                    discount_amount = order.x_discount_amount
                    disc = order.discount
                    # if len(self.x_os_line) == 1:
                    #    if amount != self.env['sale.order.line'].search([('x_lineid', '=', order.id)]).price_unit:
                    #        amount = order.price_subtotal - self.env['sale.order.line'].search([('x_lineid', '=', order.id)]).price_unit
                    name = _('Down Payment')
                    # if amount > sale_orders.x_downpayment_amount:
                    #     raise UserError(_('The value of the down payment amount must be less than or equal Total.'))
                    if self.product_id.invoice_policy != 'order':
                        raise UserError(_(
                            'The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                    if self.product_id.type != 'service':
                        raise UserError(_(
                            "The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                    taxes = self.product_id.taxes_id.filtered(
                        lambda r: not order.order_id.company_id or r.company_id == order.order_id.company_id)
                    if order.order_id.fiscal_position_id and taxes:
                        tax_ids = order.order_id.fiscal_position_id.map_tax(taxes, self.product_id,
                                                                            order.order_id.partner_shipping_id).ids
                    else:
                        tax_ids = taxes.ids
                    context = {'lang': order.order_id.partner_id.lang}
                    analytic_tag_ids = []
                    # for line in order.order_line:
                    analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in order.analytic_tag_ids]

                    so_line_values = self._prepare_so_pod_line(order, analytic_tag_ids, tax_ids, amount, qty, discount_amount, disc)
                    down_payment.append(so_line_values)
                    order_id = order.order_id
                    # so_line = sale_line_obj.create(so_line_values)
                    # self.downpayment_line_get(order, amount)
                order_line = sale_orders.order_line.filtered(lambda x: x.is_downpayment and x.qty_to_invoice != 0)
                if order_line and len(sale_orders.order_line.filtered(lambda x: x.x_lineid).ids) != len(sale_orders.order_line.filtered(lambda x: not x.is_downpayment).ids):
                    for order in order_line:
                        if order.name == 'Down Payment':
                            invoice_line = order.invoice_lines.filtered(lambda x: x.move_id.state != 'cancel')
                            # credit = []
                            # if len(invoice_line) > 1:
                            #     credit = invoice_line.filtered(lambda x: x.move_id.type == 'out_refund').mapped('move_id.reversed_entry_id').ids
                            #for line in invoice_line.filtered(lambda x: x.move_id.id not in credit):
                            for line in invoice_line:
                                self.reverse_moves(line.move_id)
                so_line = sale_line_obj.create(down_payment)
                #so_line.qty_invoiced = qty
                del context
                invoice_to_pay = self._create_invoice(order_id, so_line, amount)
            elif sale_orders.sale_order_type == 'service' and self.advance_payment_method == 'fixed':
                    amount = self.fixed_amount
                    # if len(self.x_os_line) == 1:
                    #    if amount != self.env['sale.order.line'].search([('x_lineid', '=', order.id)]).price_unit:
                    #        amount = order.price_subtotal - self.env['sale.order.line'].search([('x_lineid', '=', order.id)]).price_unit
                    name = _('Down Payment')
                    if amount > sale_orders.x_downpayment_amount:
                        raise UserError(_('The value of the down payment amount must be less than or equal Total.'))
                    if self.product_id.invoice_policy != 'order':
                        raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                    if self.product_id.type != 'service':
                        raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                    taxes = self.product_id.taxes_id.filtered(lambda r: not sale_orders.company_id or r.company_id == sale_orders.company_id)
                    print(taxes)
                    if sale_orders.fiscal_position_id and taxes:
                        tax_ids = sale_orders.fiscal_position_id.map_tax(taxes, self.product_id, sale_orders.partner_shipping_id).ids
                    else:
                        tax_ids = taxes.ids
                    context = {'lang': sale_orders.partner_id.lang}
                    analytic_tag_ids = []
                    #for line in order.order_line:
                    #analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in sale_orders.analytic_tag_ids]

                    so_line_values = self._prepare_so_line_fixed(sale_orders, analytic_tag_ids, tax_ids, amount)
                    down_payment.append(so_line_values)
                    order_id = sale_orders
                    #so_line = sale_line_obj.create(so_line_values)
                    #self.downpayment_line_get(order, amount)
                    so_line = sale_line_obj.create(down_payment)
                    del context
                    invoice_to_pay = self._create_invoice(order_id, so_line, amount)
            elif sale_orders.sale_order_type == 'service' and self.advance_payment_method == 'percentage':
                   amount = sale_orders.amount_total * self.amount / 100
                   if amount > sale_orders.x_downpayment_amount:
                       raise UserError(_('The value of the down payment amount must be less than or equal Total.'))
                   if self.product_id.invoice_policy != 'order':
                       raise UserError(_(
                           'The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                   if self.product_id.type != 'service':
                       raise UserError(_(
                           "The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                   taxes = self.product_id.taxes_id.filtered(
                       lambda r: not sale_orders.company_id or r.company_id == sale_orders.company_id)
                   if sale_orders.fiscal_position_id and taxes:
                       tax_ids = sale_orders.fiscal_position_id.map_tax(taxes, self.product_id,
                                                                        sale_orders.partner_shipping_id).ids
                   else:
                       tax_ids = taxes.ids
                   context = {'lang': sale_orders.partner_id.lang}
                   analytic_tag_ids = []
                   # for line in order.order_line:
                   # analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in sale_orders.analytic_tag_ids]

                   so_line_values = self._prepare_so_line_percentage(sale_orders, analytic_tag_ids, tax_ids, amount)
                   down_payment.append(so_line_values)
                   order_id = sale_orders
                   # so_line = sale_line_obj.create(so_line_values)
                   # self.downpayment_line_get(order, amount)
                   so_line = sale_line_obj.create(down_payment)
                   del context
                   invoice_to_pay = self._create_invoice(order_id, so_line, amount)
        if self._context.get('open_invoices', False):
            if not invoice_to_pay:
                return sale_orders.action_view_invoice()
            else:
                return invoice_to_pay.action_register_payment_custom()
        return {'type': 'ir.actions.act_window_close'}
