from odoo import fields, models


class CustomerTierHistory(models.Model):
    _name = 'customer.tier.history'
    _description = 'Customer Tier History'
    _order = 'change_date desc, id desc'

    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade', index=True)
    old_tier_id = fields.Many2one('customer.tier')
    new_tier_id = fields.Many2one('customer.tier', required=True)
    change_date = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    reason = fields.Char()
    triggered_by_user_id = fields.Many2one('res.users')
