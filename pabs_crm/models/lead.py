from odoo import models, fields, api, _


class Lead(models.Model):
    _inherit = "crm.lead"

    x_opportunity_type_id = fields.Many2one('crm.lead.type', string="Opportunity Type")
    x_quotation_amount_total = fields.Monetary(compute='_compute_quote', string="Sum of Quote", currency_field='company_currency')
    x_sequence_name = fields.Char(string='Sequence')
    planned_revenue = fields.Monetary('Expected Revenue', currency_field='company_currency', tracking=False)

    @api.depends('order_ids.state', 'order_ids.currency_id', 'order_ids.amount_untaxed', 'order_ids.date_order',
                 'order_ids.company_id')
    def _compute_quote(self):
        for lead in self:
            lead.x_quotation_amount_total = sum(lead.order_ids.filtered(lambda x: x.state != 'cancel').mapped('amount_total'))
            lead.planned_revenue = lead.x_quotation_amount_total


    @api.onchange('x_opportunity_type_id')
    def onchange_opportunity_type(self):
        for lead in self:
            lead.name = lead.x_opportunity_type_id.name

    @api.model
    def create(self, vals):
        res = super(Lead, self).create(vals)
        res.x_sequence_name = res.x_opportunity_type_id.sequence_id.next_by_id()
        return res
    
    def name_get(self):
        res = []
        for lead in self:
            res.append((lead.id, "%s (%s)" % (lead.x_sequence_name, lead.name)))
        return res

