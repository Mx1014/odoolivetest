# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from collections import defaultdict, namedtuple

from dateutil.relativedelta import relativedelta

from odoo import SUPERUSER_ID, _, api, fields, models, registry
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero, html_escape
from odoo.tools.misc import split_every

_logger = logging.getLogger(__name__)

class ProcurementException(Exception):
    """An exception raised by ProcurementGroup `run` containing all the faulty
    procurements.
    """
    def __init__(self, procurement_exceptions):
        """:param procurement_exceptions: a list of tuples containing the faulty
        procurement and their error messages
        :type procurement_exceptions: list
        """
        self.procurement_exceptions = procurement_exceptions


class StockRule(models.Model):
    """ A rule describe what a procurement should do; produce, buy, move, ... """
    _inherit = 'stock.rule'


    def _get_lead_days(self, product):
        """Returns the cumulative delay and its description encountered by a
        procurement going through the rules in `self`.

        :param product: the product of the procurement
        :type product: :class:`~odoo.addons.product.models.product.ProductProduct`
        :return: the cumulative delay and cumulative delay's description
        :rtype: tuple
        """
        delay = sum(self.filtered(lambda r: r.action in ['pull', 'pull_push']).mapped('delay'))
        if self.env.context.get('bypass_delay_description'):
            delay_description = ""
        else:
            delay_description = ''.join(['<tr><td>%s %s</td><td class="text-right">+ %d %s</td></tr>' % (_('Delay on'), html_escape(rule.name), rule.delay, _('day(s)')) for rule in self if rule.action in ['pull', 'pull_push'] and rule.delay])
        return delay, delay_description


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    # @api.model
    # def run(self, procurements):
    #     """ Method used in a procurement case. The purpose is to supply the
    #     product passed as argument in the location also given as an argument.
    #     In order to be able to find a suitable location that provide the product
    #     it will search among stock.rule.
    #     """
    #     actions_to_run = defaultdict(list)
    #     errors = []
    #     for procurement in procurements:
    #         procurement.values.setdefault('company_id', self.env.company)
    #         procurement.values.setdefault('priority', '1')
    #         procurement.values.setdefault('date_planned', fields.Datetime.now())
    #         rule = self._get_rule(procurement.product_id, procurement.location_id, procurement.values)
    #         if not rule:
    #             errors.append(_(
    #                 'No rule has been found to replenish "%s" in "%s".\nVerify the routes configuration on the product.') %
    #                           (procurement.product_id.display_name, procurement.location_id.display_name))
    #         else:
    #             action = 'pull' if rule.action == 'pull_push' else rule.action
    #             actions_to_run[action].append((procurement, rule))
    #
    #     if errors:
    #         raise UserError('\n'.join(errors))
    #
    #     for action, procurements in actions_to_run.items():
    #         if hasattr(self.env['stock.rule'], '_run_%s' % action):
    #             try:
    #                 getattr(self.env['stock.rule'], '_run_%s' % action)(procurements)
    #             except UserError as e:
    #                 errors.append(e.name)
    #         else:
    #             _logger.error("The method _run_%s doesn't exist on the procurement rules" % action)
    #
    #     if errors:
    #         raise UserError('\n'.join(errors))
    #     return True

    @api.model
    def run(self, procurements, raise_user_error=True):
        """Fulfil `procurements` with the help of stock rules.
        Procurements are needs of products at a certain location. To fulfil
        these needs, we need to create some sort of documents (`stock.move`
        by default, but extensions of `_run_` methods allow to create every
        type of documents).
        :param procurements: the description of the procurement
        :type list: list of `~odoo.addons.stock.models.stock_rule.ProcurementGroup.Procurement`
        :param raise_user_error: will raise either an UserError or a ProcurementException
        :type raise_user_error: boolan, optional
        :raises UserError: if `raise_user_error` is True and a procurement isn't fulfillable
        :raises ProcurementException: if `raise_user_error` is False and a procurement isn't fulfillable
        """

        def raise_exception(procurement_errors):
            if raise_user_error:
                dummy, errors = zip(*procurement_errors)
                raise UserError('\n'.join(errors))
            else:
                raise ProcurementException(procurement_errors)

        actions_to_run = defaultdict(list)
        procurement_errors = []
        for procurement in procurements:
            procurement.values.setdefault('company_id', procurement.location_id.company_id)
            procurement.values.setdefault('priority', '0')
            procurement.values.setdefault('date_planned', fields.Datetime.now())
            if (
                    procurement.product_id.type not in ('consu', 'product') or
                    float_is_zero(procurement.product_qty, precision_rounding=procurement.product_uom.rounding)
            ):
                continue
            rule = self._get_rule(procurement.product_id, procurement.location_id, procurement.values)
            if not rule:
                error = _(
                    'No rule has been found to replenish "%s" in "%s".\nVerify the routes configuration on the product.') % \
                        (procurement.product_id.display_name, procurement.location_id.display_name)
                procurement_errors.append((procurement, error))
            else:
                action = 'pull' if rule.action == 'pull_push' else rule.action
                actions_to_run[action].append((procurement, rule))

        if procurement_errors:
            raise_exception(procurement_errors)

        for action, procurements in actions_to_run.items():
            if hasattr(self.env['stock.rule'], '_run_%s' % action):
                try:
                    getattr(self.env['stock.rule'], '_run_%s' % action)(procurements)
                except ProcurementException as e:
                    procurement_errors += e.procurement_exceptions
            else:
                _logger.error("The method _run_%s doesn't exist on the procurement rules" % action)

        if procurement_errors:
            raise_exception(procurement_errors)
        return True


