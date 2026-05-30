# -*- coding: utf-8 -*-
from odoo import models, fields, api


RANK_THRESHOLDS = [
    (255, 'diamond'),
    (175, 'gold'),
    (110, 'silver'),
    (50,  'bronze'),
    (0,   'normal'),
]

RANK_SELECTION = [
    ('normal',  'Thường'),
    ('bronze',  'Đồng'),
    ('silver',  'Bạc'),
    ('gold',    'Vàng'),
    ('diamond', 'Kim Cương'),
]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    loyalty_card_ids = fields.One2many(
        'loyalty.card', 'partner_id',
        string='Loyalty Cards',
    )

    pos_loyalty_points = fields.Float(
        string='Tổng điểm Loyalty',
        compute='_compute_pos_loyalty_points',
        store=True,
        digits=(16, 2),
        help='Tổng điểm loyalty tích lũy từ tất cả chương trình POS.',
    )

    loyalty_rank = fields.Selection(
        selection=RANK_SELECTION,
        string='Hạng khách hàng',
        compute='_compute_loyalty_rank',
        store=True,
    )

    loyalty_rank_label = fields.Char(
        string='Hạng',
        compute='_compute_loyalty_rank',
        store=True,
    )

    @api.depends('loyalty_card_ids.points')
    def _compute_pos_loyalty_points(self):
        for partner in self:
            partner.pos_loyalty_points = sum(partner.loyalty_card_ids.mapped('points'))

    @api.depends('pos_loyalty_points')
    def _compute_loyalty_rank(self):
        rank_labels = dict(RANK_SELECTION)
        for partner in self:
            pts = partner.pos_loyalty_points or 0.0
            rank = 'normal'
            for threshold, rank_key in RANK_THRESHOLDS:
                if pts >= threshold:
                    rank = rank_key
                    break
            partner.loyalty_rank = rank
            partner.loyalty_rank_label = rank_labels.get(rank, 'Thường')