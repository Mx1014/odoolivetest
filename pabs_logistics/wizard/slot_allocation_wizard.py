# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import fields, models


class SlotTimeWizard(models.TransientModel):
    _name = 'slot.time.wizard'
    _description = "slot Time Wizard"

    def _set_default_last_from_date(self):
        last = self.env['slot.allocation.time'].search([], limit=1, order="date desc")
        last_date = last and last.date + timedelta(1) or fields.Date.today()
        return last_date

    from_date = fields.Date(string="From Date", default=_set_default_last_from_date)
    to_date = fields.Date(string="To Date", default=_set_default_last_from_date)
    picking_type_ids = fields.Many2many('stock.picking.type')

    def action_create_slot_allocation_time(self):
        self.ensure_one()
        types = ['evening', 'morning']

        def daterange(date1, date2):
            for n in range(int((date2 - date1).days) + 1):
                yield date1 + timedelta(n)

        dates = []
        if self.picking_type_ids and self.from_date >= fields.Date.today() and self.to_date >= self.from_date:
            for dt in daterange(self.from_date, self.to_date):
                for i in self.picking_type_ids.ids:
                    dates.append({'date': dt.strftime("%Y-%m-%d"), 'id': i})
            records = []
            for dt in dates:
                record = {}
                record['date'] = dt['date']
                record['picking_type_id'] = dt['id']
                for t in types:
                    record1 = record.copy()
                    record1['name'] = "%s %s" % (dt['date'], t)
                    record1['time_zone'] = t
                    records.append(record1)
            if records:
                self.env['slot.allocation.time'].create(records)
        return True
