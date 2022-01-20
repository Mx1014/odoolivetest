import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class IncrementWages(models.TransientModel):
    _name = 'increment.wages'

    def do_increments(self):
        contracts = self.env['hr.contract'].search([('increments', '>', 0)])
        for contract in contracts:
            if contract.increments > 0:
                contract.wage = contract.increments + contract.wage
                contract.gosi_salary = contract.increments + contract.gosi_salary
                contract.increments = 0
        return {
            'name': _('Increments'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hr.contract',
            'views': [
                (self.env.ref('pabs_hr.hr_contract_view_new_tree').id, 'tree'),
                (self.env.ref('hr_contract.hr_contract_view_form').id, 'form'),
            ],  # 'res_id': planning_slot.id,
            # 'context': context,
        }