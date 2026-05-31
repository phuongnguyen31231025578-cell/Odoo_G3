# -*- coding: utf-8 -*-
from odoo import models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _load_pos_data_fields(self, config):
        result = super()._load_pos_data_fields(config)
        result += ['pos_loyalty_points', 'loyalty_rank', 'loyalty_rank_label']
        return result

    @api.model
    def _load_pos_data_search_read(self, data, config):
        result = super()._load_pos_data_search_read(data, config)
        domain = self._load_pos_data_domain(data, config)
        fields = self._load_pos_data_fields(config)
        partners = self.search_read(domain, fields, load=False)
        return partners


class LoyaltyCard(models.Model):
    _inherit = 'loyalty.card'

    def write(self, vals):
        result = super().write(vals)
        if 'points' in vals:
            partners = self.mapped('partner_id').filtered(lambda p: p.id)
            for partner in partners:
                pts = sum(partner.loyalty_card_ids.mapped('points'))
                rank = 'normal'
                if pts >= 255:
                    rank = 'diamond'
                elif pts >= 175:
                    rank = 'gold'
                elif pts >= 110:
                    rank = 'silver'
                elif pts >= 50:
                    rank = 'bronze'
                partner.sudo().write({
                    'pos_loyalty_points': pts,
                    'loyalty_rank': rank,
                    'loyalty_rank_label': dict([
                        ('normal', 'Thường'),
                        ('bronze', 'Đồng'),
                        ('silver', 'Bạc'),
                        ('gold', 'Vàng'),
                        ('diamond', 'Kim Cương'),
                    ]).get(rank, 'Thường'),
                })
        return result

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.partner_id:
            pts = sum(record.partner_id.loyalty_card_ids.mapped('points'))
            rank = 'normal'
            if pts >= 255:
                rank = 'diamond'
            elif pts >= 175:
                rank = 'gold'
            elif pts >= 110:
                rank = 'silver'
            elif pts >= 50:
                rank = 'bronze'
            record.partner_id.sudo().write({
                'pos_loyalty_points': pts,
                'loyalty_rank': rank,
                'loyalty_rank_label': dict([
                    ('normal', 'Thường'),
                    ('bronze', 'Đồng'),
                    ('silver', 'Bạc'),
                    ('gold', 'Vàng'),
                    ('diamond', 'Kim Cương'),
                ]).get(rank, 'Thường'),
            })
        return record

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def action_pos_order_paid(self):
        result = super().action_pos_order_paid()
        # Recompute loyalty rank cho partner sau khi thanh toán
        if self.partner_id:
            pts = sum(self.partner_id.loyalty_card_ids.mapped('points'))
            rank = 'normal'
            if pts >= 255: rank = 'diamond'
            elif pts >= 175: rank = 'gold'
            elif pts >= 110: rank = 'silver'
            elif pts >= 50: rank = 'bronze'
            self.partner_id.sudo().write({
                'pos_loyalty_points': pts,
                'loyalty_rank': rank,
            })
        return result