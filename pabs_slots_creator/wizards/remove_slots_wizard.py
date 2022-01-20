from odoo import fields, models, api, _
from odoo.exceptions import Warning, UserError, AccessError
from datetime import datetime, timedelta


class CreateSlotsWizard(models.TransientModel):
    _name = 'remove.slots.wizard'
    _description = "Slot Removal Wizard"

    x_slot_type = fields.Selection([('logistic', 'Logistics'), ('service', 'Field Service')], string='Slots Type',
                                   default='logistic')
    x_business_line = fields.Many2one('business.line', string='Business Line')
    x_from_date = fields.Datetime(string='From')
    x_to_date = fields.Datetime(string='To')
    x_slot_number = fields.Integer(string='Number Of Slots')
    x_sun = fields.Boolean('Sundays', default=False)
    x_mon = fields.Boolean('Mondays', default=False)
    x_tue = fields.Boolean('tuesdays', default=False)
    x_wed = fields.Boolean('wednesdays', default=False)
    x_thu = fields.Boolean('thursdays', default=False)
    x_fri = fields.Boolean('Fridays', default=True)
    x_sat = fields.Boolean('Saturdays', default=False)

    @api.onchange('x_slot_type')
    def onchange_x_slot_type(self):
        res = {}
        if self.x_slot_type == 'logistic':
            res['domain'] = {'x_business_line': [('business_line_type', '=', 'delivery')]}
        elif self.x_slot_type == 'service':
            res['domain'] = {'x_business_line': [('business_line_type', '=', 'service')]}
        self.x_business_line = None
        return res

    def check_days(self):
        days = []
        if self.x_sun:
            days.append('sunday')
        if self.x_mon:
            days.append('monday')
        if self.x_tue:
            days.append('tuesday')
        if self.x_wed:
            days.append('wednesday')
        if self.x_thu:
            days.append('thursday')
        if self.x_fri:
            days.append('friday')
        if self.x_sat:
            days.append('saturday')
        return days

    def remove_logistics_slots(self):
        first_date = self.x_from_date
        last_date = self.x_to_date
        days_to_skip = self.check_days()
        delta = (last_date - first_date).days
        if delta < 0:
            raise UserError(_('The end date cannot be before the start date'))
        if self.x_slot_type == 'logistic':
            for x in range(delta + 1):
                date_to_remove = first_date + timedelta(days=x)
                slots_to_remove = False
                if not days_to_skip or date_to_remove.strftime("%A").lower() not in days_to_skip:
                    slots_to_remove = self.env['plan.calendar'].search([('business_line', '=', self.x_business_line.id),
                                                                        ('start_datetime', '>=', date_to_remove),
                                                                        ('start_datetime', '<=', date_to_remove + timedelta(days=1)),
                                                                        ('status', '=', 'available')], limit=self.x_slot_number)
                    if slots_to_remove:
                        print(date_to_remove.strftime("%A").lower(), 'removed')
                        slots_to_remove.unlink()
                        # for slot in slots_to_remove:
                        #     # self.env['plan.calendar'].browse(slot).unlink()
                        #     print(date_to_remove.strftime("%A").lower(), 'removed')
                        #     slot.unlink()
        else:
            for x in range(delta + 1):
                date_to_remove = first_date + timedelta(days=x)
                slots_to_remove = False
                if not days_to_skip or date_to_remove.strftime("%A").lower() not in days_to_skip:
                    slots_to_remove = self.env['field.plan.calendar'].search([('business_line', '=', self.x_business_line.id),
                                                                              ('start_datetime', '>=', date_to_remove),
                                                                              ('start_datetime', '<=', date_to_remove + timedelta(days=1)),
                                                                              ('status', '=', 'available')], limit=self.x_slot_number)
                    if slots_to_remove:
                        # for slot in slots_to_remove:
                            # self.env['plan.calendar'].browse(slot).unlink()
                        print(date_to_remove.strftime("%A").lower(), 'removed')
                        slots_to_remove.unlink()
