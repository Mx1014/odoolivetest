from odoo import fields, models, api, _
from odoo.exceptions import Warning, UserError, AccessError
from datetime import datetime, timedelta


class CreateSlotsWizard(models.TransientModel):
    _name = 'create.slots.wizard'
    _description = "Slot Creation Wizard"

    x_slot_type = fields.Selection([('logistic', 'Logistics'), ('service', 'Field Service')], string='Slots Type', default='logistic')
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

    def create_logistics_slots(self):
        first_date = self.x_from_date + timedelta(hours=3)
        last_date = self.x_to_date + timedelta(hours=3)
        days_to_skip = self.check_days()
        delta = (last_date - first_date).days
        if delta < 0:
            raise UserError(_('The end date cannot be before the start date'))
        if self.x_slot_type == 'logistic':
            for x in range(delta + 1):
                date_to_add = first_date + timedelta(days=x)
                if not days_to_skip or date_to_add.strftime("%A").lower() not in days_to_skip:
                    for i in range(self.x_slot_number):
                        print(date_to_add.strftime("%A").lower(), 'ADDED')
                        self.env['plan.calendar'].create({
                            'start_datetime': date_to_add,
                            'end_datetime': date_to_add,
                            'status': 'available',
                            'business_line': self.x_business_line.id,
                            'auto_create': True,
                        })
        else:
            for x in range(delta + 1):
                date_to_add = first_date + timedelta(days=x)
                if not days_to_skip or date_to_add.strftime("%A").lower() not in days_to_skip:
                    for i in range(self.x_slot_number):
                        print(date_to_add.strftime("%A").lower(), 'ADDED')
                        self.env['field.plan.calendar'].create({
                            'start_datetime': date_to_add,
                            'end_datetime': date_to_add,
                            'status': 'available',
                            'business_line': self.x_business_line.id,
                            'auto_create': True,
                        })
