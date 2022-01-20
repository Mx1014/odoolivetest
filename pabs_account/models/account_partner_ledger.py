# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, _lt, fields
from odoo.tools.misc import format_date
from datetime import timedelta


class ReportPartnerLedger(models.AbstractModel):
    _inherit = "account.partner.ledger"

    print("aaa")

    @api.model
    def _get_options_due_amount(self, options):
        ''' Create options used to compute the initial balances for each partner.
        The resulting dates domain will be:
        [('date' <= options['date_from'] - 1)]
        :param options: The report options.
        :return:        A copy of the options.
        '''
        new_options = options.copy()
        new_options['date'] = new_options['date'].copy()
        new_date_to = fields.Date.from_string(new_options['date']['date_from']) - timedelta(days=1)
        new_options['date'].update({
            'date_from': False,
            'date_to': fields.Date.to_string(new_date_to),
        })
        return new_options

    @api.model
    def _get_query_sums(self, options, expanded_partner=None):
        ''' Construct a query retrieving all the aggregated sums to build the report. It includes:
        - sums for all accounts.
        - sums for the initial balances.
        - sums for the unaffected earnings.
        - sums for the tax declaration.
        :param options:             The report options.
        :param expanded_partner:    An optional account.account record that must be specified when expanding a line
                                    with of without the load more.
        :return:                    (query, params)
        '''
        params = []
        queries = []

        if expanded_partner:
            domain = [('partner_id', '=', expanded_partner.id)]
        else:
            domain = []

        # Create the currency table.
        ct_query = self._get_query_currency_table(options)

        # Get sums for all partners.
        # period: [('date' <= options['date_to']), ('date' >= options['date_from'])]
        new_options = self._get_options_sum_balance(options)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        params += where_params
        queries.append('''
                SELECT
                    account_move_line.partner_id        AS groupby,
                    'sum'                               AS key,
                    SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                    SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                    SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                    SUM(ROUND(account_move_line__move_id.amount_residual_signed * currency_table.rate, currency_table.precision)) AS x_due_am,
                    SUM(ROUND(payment.x_payment_due_amount * currency_table.rate, currency_table.precision)) AS due_payment
                FROM %s
                LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN account_payment payment           ON payment.id = account_move_line.payment_id
                WHERE %s
                GROUP BY account_move_line.partner_id
            ''' % (tables, ct_query, where_clause))

        # Get sums for the initial balance.
        # period: [('date' <= options['date_from'] - 1)]
        new_options = self._get_options_initial_balance(options)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        params += where_params
        queries.append('''
                SELECT
                    account_move_line.partner_id        AS groupby,
                    'initial_balance'                   AS key,
                    SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))   AS debit,
                    SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))  AS credit,
                    SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision)) AS balance,
                    SUM(ROUND(account_move_line__move_id.amount_residual_signed * currency_table.rate, currency_table.precision)) AS x_due_am,
                    SUM(ROUND(payment.x_payment_due_amount * currency_table.rate, currency_table.precision)) AS due_payment
                FROM %s
                LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN account_payment payment           ON payment.id = account_move_line.payment_id
                WHERE %s
                GROUP BY account_move_line.partner_id
            ''' % (tables, ct_query, where_clause))

        return ' UNION ALL '.join(queries), params

    @api.model
    def _do_query(self, options, expanded_partner=None):
        ''' Execute the queries, perform all the computation and return partners_results,
        a lists of tuple (partner, fetched_values) sorted by the table's model _order:
            - partner is a res.parter record.
            - fetched_values is a dictionary containing:
                - sum:                              {'debit': float, 'credit': float, 'balance': float}
                - (optional) initial_balance:       {'debit': float, 'credit': float, 'balance': float}
                - (optional) lines:                 [line_vals_1, line_vals_2, ...]
        :param options:             The report options.
        :param expanded_account:    An optional account.account record that must be specified when expanding a line
                                    with of without the load more.
        :param fetch_lines:         A flag to fetch the account.move.lines or not (the 'lines' key in accounts_values).
        :return:                    (accounts_values, taxes_results)
        '''
        company_currency = self.env.company.currency_id

        # Execute the queries and dispatch the results.
        query, params = self._get_query_sums(options, expanded_partner=expanded_partner)

        groupby_partners = {}

        self._cr.execute(query, params)
        for res in self._cr.dictfetchall():
            key = res['key']
            # unpaid = 0.0
            # value_p = self.env['account.payment'].search([('id', '=', pay['payment_id'])], limit=1)
            # for val in value_p:
            #     unpaid += val.compute_invoiceids()
            #
            # res['x_due_am'] = unpaid
            if key == 'sum':
                if not company_currency.is_zero(res['debit']) or not company_currency.is_zero(res['credit']):
                    groupby_partners.setdefault(res['groupby'], {})
                    groupby_partners[res['groupby']][key] = res
                    # groupby_partners[res['groupby']][x_due_am] = res
            elif key == 'initial_balance':
                if not company_currency.is_zero(res['balance']):
                    groupby_partners.setdefault(res['groupby'], {})
                    groupby_partners[res['groupby']][key] = res
                    # groupby_partners[res['groupby']][x_due_am] = res

        # Fetch the lines of unfolded accounts.
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])
        if expanded_partner or unfold_all or options['unfolded_lines']:
            query, params = self._get_query_amls(options, expanded_partner=expanded_partner)
            self._cr.execute(query, params)
            for res in self._cr.dictfetchall():
                if res['partner_id'] not in groupby_partners:
                    continue
                groupby_partners[res['partner_id']].setdefault('lines', [])
                groupby_partners[res['partner_id']]['lines'].append(res)

        # Retrieve the partners to browse.
        # groupby_partners.keys() contains all account ids affected by:
        # - the amls in the current period.
        # - the amls affecting the initial balance.
        # Note a search is done instead of a browse to preserve the table ordering.
        if expanded_partner:
            partners = expanded_partner
        elif groupby_partners:
            partners = self.env['res.partner'].with_context(active_test=False).search(
                [('id', 'in', list(groupby_partners.keys()))])
        else:
            partners = []
        return [(partner, groupby_partners[partner.id]) for partner in partners]

    @api.model
    def _get_partner_ledger_lines(self, options, line_id=None):
        ''' Get lines for the whole report or for a specific line.
        :param options: The report options.
        :return:        A list of lines, each one represented by a dictionary.
        '''
        lines = []
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        expanded_partner = line_id and self.env['res.partner'].browse(int(line_id[8:]))
        partners_results = self._do_query(options, expanded_partner=expanded_partner)

        total_initial_balance = total_debit = total_credit = total_x_due_am = total_due_payment = total_balance = 0.0
        for partner, results in partners_results:
            is_unfolded = 'partner_%s' % partner.id in options['unfolded_lines']

            # res.partner record line.
            partner_sum = results.get('sum', {})
            partner_init_bal = results.get('initial_balance', {})
            initial_balance = partner_init_bal.get('balance', 0.0)
            debit = partner_sum.get('debit', 0.0)
            credit = partner_sum.get('credit', 0.0)
            # due_payment = partner_sum.get('due_payment', 0.0)
            due_payment_x = partner_sum.get('due_payment', 0.0)
            due_amp = partner_sum.get('x_due_am', 0.0)
            if due_amp and due_payment_x:
                x_due_am = due_amp + due_payment_x
            elif not due_amp and due_payment_x:
                x_due_am = due_payment_x
            else:
                x_due_am = partner_sum.get('x_due_am', 0.0)

            # if due_amp and due_payment_x:
            #     x_due_am = due_amp + due_payment_x
            # elif not due_amp and due_payment_x:
            #     x_due_am = due_payment_x
            # else:
            #     x_due_am = partner_sum.get('x_due_am', 0.0)
            balance = initial_balance + partner_sum.get('balance', 0.0)

            lines.append(self._get_report_line_partner(options, partner, x_due_am, debit, credit, balance))

            # total_initial_balance += initial_balance
            total_debit += debit
            total_credit += credit
            total_x_due_am += x_due_am
            # total_due_payment += due_payment
            total_balance += balance

            if unfold_all or is_unfolded:
                cumulated_balance = initial_balance

                # account.move.line record lines.
                amls = results.get('lines', [])

                load_more_remaining = len(amls)
                load_more_counter = self._context.get('print_mode') and load_more_remaining or self.MAX_LINES

                for aml in amls:
                    # Don't show more line than load_more_counter.
                    if load_more_counter == 0:
                        break

                    cumulated_init_balance = cumulated_balance
                    cumulated_balance += aml['balance']

                    lines.append(self._get_report_line_move_line(options, partner, aml, cumulated_init_balance,
                                                                 cumulated_balance))

                    load_more_remaining -= 1
                    load_more_counter -= 1

                if load_more_remaining > 0:
                    # Load more line.
                    lines.append(self._get_report_line_load_more(
                        options,
                        partner,
                        self.MAX_LINES,
                        load_more_remaining,
                        cumulated_balance,
                    ))

        if not line_id:
            # Report total line.
            lines.append(self._get_report_line_total(
                options,
                total_x_due_am,
                # total_x_due_am + total_due_payment,
                total_debit,
                total_credit,
                total_balance
            ))
        return lines

    @api.model
    def _get_query_amls(self, options, expanded_partner=None, offset=None, limit=None):
        ''' Construct a query retrieving the account.move.lines when expanding a report line with or without the load
        more.
        :param options:             The report options.
        :param expanded_partner:    The res.partner record corresponding to the expanded line.
        :param offset:              The offset of the query (used by the load more).
        :param limit:               The limit of the query (used by the load more).
        :return:                    (query, params)
        '''
        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        # Get sums for the account move lines.
        # period: [('date' <= options['date_to']), ('date', '>=', options['date_from'])]
        if expanded_partner:
            domain = [('partner_id', '=', expanded_partner.id)]
        elif unfold_all:
            domain = []
        elif options['unfolded_lines']:
            domain = [('partner_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]

        new_options = self._get_options_sum_balance(options)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        ct_query = self._get_query_currency_table(options)

        query = '''
            SELECT
                account_move_line.id,
                account_move_line.date,
                account_move_line.date_maturity,
                account_move_line.name,
                account_move_line.ref,
                account_move_line.company_id,
                account_move_line.account_id,
                account_move_line.payment_id,
                account_move_line.partner_id,
                account_move_line.currency_id,
                account_move_line.amount_currency,
                ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)   AS debit,
                ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
                ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
                account_move_line__move_id.name         AS move_name,
                company.currency_id                     AS company_currency_id,
                partner.name                            AS partner_name,
                account_move_line__move_id.type         AS move_type,
                account_move_line__move_id.x_shipping_address         AS delivery_address,
                account.code                            AS account_code,
                account.name                            AS account_name,
                journal.code                            AS journal_code,
                journal.name                            AS journal_name,
                full_rec.name                           AS full_rec_name,
                account_move_line__move_id.invoice_origin   AS invoice_origin,
                account_move_line__move_id.x_brand      AS x_brand,
                account_move_line__move_id.amount_residual_signed     AS x_due_am,
                delivery.name                           AS partner_shipping_id,
                payment.x_payment_due_amount            AS due_payment
            FROM account_move_line
            LEFT JOIN account_move account_move_line__move_id ON account_move_line__move_id.id = account_move_line.move_id
            LEFT JOIN %s ON currency_table.company_id = account_move_line.company_id
            LEFT JOIN res_company company               ON company.id = account_move_line.company_id
            LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
            LEFT JOIN res_partner delivery              ON delivery.id = account_move_line__move_id.partner_shipping_id
            LEFT JOIN account_account account           ON account.id = account_move_line.account_id
            LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
            LEFT JOIN account_full_reconcile full_rec   ON full_rec.id = account_move_line.full_reconcile_id
            LEFT JOIN account_payment payment           ON payment.id = account_move_line.payment_id
            WHERE %s
            ORDER BY account_move_line.id
        ''' % (ct_query, where_clause)

        if offset:
            query += ' OFFSET %s '
            where_params.append(offset)
        if limit:
            query += ' LIMIT %s '
            where_params.append(limit)

        return query, where_params

    @api.model
    def _get_report_line_move_line(self, options, partner, aml, cumulated_init_balance, cumulated_balance):
        if aml['payment_id']:
            caret_type = 'account.payment'
        elif aml['move_type'] in ('in_refund', 'in_invoice', 'in_receipt'):
            caret_type = 'account.invoice.in'
        elif aml['move_type'] in ('out_refund', 'out_invoice', 'out_receipt'):
            caret_type = 'account.invoice.out'
        else:
            caret_type = 'account.move'

        type = ''
        if aml['move_type'] == 'in_refund':
            type = 'Vendor Credit'
        elif aml['move_type'] == 'in_invoice':
            type = 'Vendor Bill'
        elif aml['move_type'] == 'out_refund':
            type = 'Credit Note'
        elif aml['move_type'] == 'out_invoice':
            type = 'Customer Invoice'
        elif aml['move_type'] == 'out_receipt':
            type = 'Sales Receipt'
        elif aml['move_type'] == 'in_receipt':
            type = 'Purchase Receipt'
        elif aml['move_type'] == 'entry':
            type = 'Payment'
        elif aml['move_type'] == 'adjustment':
            type = 'Adjustment'
        elif aml['move_type'] == 'apportionment':
            type = 'Apportionment'

        date_maturity = aml['date_maturity'] and format_date(self.env, fields.Date.from_string(aml['date_maturity']))
        columns = [
            {'name': aml['journal_code']},
            {'name': aml['account_code']},
            {'name': type},
            {'name': aml['move_name']},
            {'name': aml['ref']},
            {'name': aml['invoice_origin']},
            {'name': aml['x_brand']},
            {'name': aml['delivery_address']},
            # {'name': aml['partner_shipping_id']},
            {'name': date_maturity or '', 'class': 'date'},
            {'name': aml['full_rec_name'] or ''},
            # {'name': self.format_value(cumulated_init_balance), 'class': 'number'},
            {'name': aml['x_due_am'] or aml['due_payment'], 'class': 'number'},
            {'name': self.format_value(aml['debit'], blank_if_zero=True), 'class': 'number'},
            {'name': self.format_value(aml['credit'], blank_if_zero=True), 'class': 'number'},
        ]
        if self.user_has_groups('base.group_multi_currency'):
            if aml['currency_id']:
                currency = self.env['res.currency'].browse(aml['currency_id'])
                formatted_amount = self.format_value(aml['amount_currency'], currency=currency, blank_if_zero=True)
                columns.append({'name': formatted_amount, 'class': 'number'})
            else:
                columns.append({'name': ''})
        columns.append({'name': self.format_value(cumulated_balance), 'class': 'number'})
        return {
            'id': aml['id'],
            'parent_id': 'partner_%s' % partner.id,
            'name': format_date(self.env, aml['date']),
            'class': 'date',
            'columns': columns,
            'caret_options': caret_type,
            'level': 4,
        }

    # issue of line here

    # @api.model
    # def _get_report_line_move_line(self, options, partner, aml, cumulated_balance, x_due_am):
    # if aml['payment_id']:
    #     caret_type = 'account.payment'
    # elif aml['move_type'] in ('in_refund', 'in_invoice', 'in_receipt'):
    #     caret_type = 'account.invoice.in'
    # elif aml['move_type'] in ('out_refund', 'out_invoice', 'out_receipt'):
    #     caret_type = 'account.invoice.out'
    # else:
    #     caret_type = 'account.move'
    #
    # # amount_payment = self.env['account.payment'].search([('id', '=', aml['payment_id'])], limit=1)
    # # unpaid = amount_payment.compute_amount()
    # type = ''
    # if aml['move_type'] == 'in_refund':
    #     type = 'Vendor Credit'
    # elif aml['move_type'] == 'in_invoice':
    #     type = 'Vendor Bill'
    # elif aml['move_type'] == 'out_refund':
    #     type = 'Credit Note'
    # elif aml['move_type'] == 'out_invoice':
    #     type = 'Customer Invoice'
    # elif aml['move_type'] == 'out_receipt':
    #     type = 'Sales Receipt'
    # elif aml['move_type'] == 'in_receipt':
    #     type = 'Purchase Receipt'
    # elif aml['move_type'] == 'entry':
    #     type = 'Payment'
    # elif aml['move_type'] == 'adjustment':
    #     type = 'Adjustment'
    # elif aml['move_type'] == 'apportionment':
    #     type = 'Apportionment'
    #
    # date_maturity = aml['date_maturity'] and format_date(self.env, fields.Date.from_string(aml['date_maturity']))
    # columns = [
    #     {'name': aml['journal_code']},
    #     {'name': aml['account_code']},
    #     {'name': type},
    #     {'name': aml['move_name']},
    #     {'name': aml['ref']},
    #     {'name': aml['invoice_origin']},
    #     {'name': aml['x_brand']},
    #     {'name': aml['delivery_address']},
    #     # {'name': aml['partner_shipping_id']},
    #     {'name': date_maturity or '', 'class': 'date'},
    #     {'name': aml['full_rec_name'] or ''},
    #     # {'name': self.format_value(cumulated_init_balance), 'class': 'number'},
    #     {'name': aml['x_due_am'] or aml['due_payment'], 'class': 'number'},
    #     {'name': self.format_value(aml['debit'], blank_if_zero=True), 'class': 'number'},
    #     {'name': self.format_value(aml['credit'], blank_if_zero=True), 'class': 'number'},
    # ]
    # if self.user_has_groups('base.group_multi_currency'):
    #     if aml['currency_id']:
    #         currency = self.env['res.currency'].browse(aml['currency_id'])
    #         formatted_amount = self.format_value(aml['amount_currency'], currency=currency, blank_if_zero=True)
    #         columns.append({'name': formatted_amount, 'class': 'number'})
    #     else:
    #         columns.append({'name': ''})
    # columns.append({'name': self.format_value(cumulated_balance), 'class': 'number'})
    # return {
    #     'id': aml['id'],
    #     'parent_id': 'partner_%s' % partner.id,
    #     'name': format_date(self.env, aml['date']),
    #     'class': 'date',
    #     'columns': columns,
    #     'caret_options': caret_type,
    #     'level': 4,
    # }

    def _get_columns_name(self, options):
        columns = [
            {},
            {'name': _('JRNL')},
            {'name': _('Account')},
            {'name': _('Transaction Type')},
            {'name': _('Bill No')},
            {'name': _('Ref')},
            {'name': _('PO')},
            {'name': _('Brand')},
            {'name': _('Delivery Address')},
            {'name': _('Due Date'), 'class': 'date'},
            {'name': _('Matching Number')},
            {'name': _('Amount Due'), 'class': 'number'},
            # {'name': _('Initial Balance'), 'class': 'number'},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'},
        ]

        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': _('Amount Currency'), 'class': 'number'})

        columns.append({'name': _('Balance'), 'class': 'number'})

        return columns

    @api.model
    def _get_report_line_total(self, options, x_due_am, debit, credit, balance):
        columns = [
            {'name': self.format_value(x_due_am), 'class': 'number'},
            # {'name': self.format_value(initial_balance), 'class': 'number'},
            {'name': self.format_value(debit), 'class': 'number'},
            {'name': self.format_value(credit), 'class': 'number'},
        ]

        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': ''})
        columns.append({'name': self.format_value(balance), 'class': 'number'})
        return {
            'id': 'partner_ledger_total_%s' % self.env.company.id,
            'name': _('Total'),
            'class': 'total',
            'level': 1,
            'columns': columns,
            'colspan': 11,
        }

    @api.model
    def _get_report_line_partner(self, options, partner, x_due_am, debit, credit, balance):
        company_currency = self.env.company.currency_id
        unfold_all = self._context.get('print_mode') and not options.get('unfolded_lines')

        columns = [
            {'name': self.format_value(x_due_am), 'class': 'number'},
            # {'name': self.format_value(initial_balance), 'class': 'number'},
            {'name': self.format_value(debit), 'class': 'number'},
            {'name': self.format_value(credit), 'class': 'number'},
        ]
        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': ''})
        columns.append({'name': self.format_value(balance), 'class': 'number'})

        return {
            'id': 'partner_%s' % partner.id,
            'name': partner.name[:128],
            'columns': columns,
            'level': 2,
            'trust': partner.trust,
            'unfoldable': not company_currency.is_zero(debit) or not company_currency.is_zero(credit),
            'unfolded': 'partner_%s' % partner.id in options['unfolded_lines'] or unfold_all,
            'colspan': 11,
        }
