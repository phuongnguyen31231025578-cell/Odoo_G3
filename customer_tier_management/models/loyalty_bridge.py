from odoo import api, models


class LoyaltyCard(models.Model):
    _inherit = 'loyalty.card'

    @api.model_create_multi
    def create(self, vals_list):
        cards = super().create(vals_list)
        partners = cards.mapped('partner_id')
        if partners:
            partners._compute_total_loyalty_points()
            partners._update_customer_tier(reason='Purchase')
        return cards

    def write(self, vals):
        old_points = None
        if 'points' in vals:
            old_points = {c.id: (c.points or 0.0) for c in self}

        res = super().write(vals)

        if 'points' in vals:
            reasons_by_partner = {}
            for card in self:
                before = (old_points or {}).get(card.id, 0.0)
                after = card.points or 0.0

                if after > before:
                    reason = 'Purchase'
                elif after < before:
                    reason = 'Redemption'
                else:
                    reason = 'Points adjusted'

                if card.partner_id:
                    reasons_by_partner[card.partner_id.id] = reason

            partners = self.mapped('partner_id')
            if partners:
                partners._compute_total_loyalty_points()
                for partner in partners:
                    partner._update_customer_tier(reason=reasons_by_partner.get(partner.id) or 'Points adjusted')

        return res
