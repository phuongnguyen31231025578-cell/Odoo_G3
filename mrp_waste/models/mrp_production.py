# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    actual_qty = fields.Float(
        string='Sản lượng thực tế',
        digits=(10, 2),
        default=0.0,
        help='Sản lượng thực tế thu được sau khi hoàn tất sản xuất.',
    )

    actual_waste_rate = fields.Float(
        string='Tỷ lệ hao hụt thực tế (%)',
        digits=(5, 2),
        compute='_compute_waste_rates',
        store=True,
    )

    waste_rate_deviation = fields.Float(
        string='Chênh lệch hao hụt (%)',
        digits=(5, 2),
        compute='_compute_waste_rates',
        store=True,
    )

    is_waste_exceeded = fields.Boolean(
        string='Hao hụt vượt mức',
        compute='_compute_waste_rates',
        store=True,
        help='True nếu chênh lệch hao hụt thực tế so với dự kiến vượt quá 3%.',
    )

    expected_waste_rate = fields.Float(
        string='Tỷ lệ hao hụt dự kiến (%)',
        digits=(5, 2),
        compute='_compute_expected_waste_rate',
        store=True,
    )

    @api.depends('bom_id', 'bom_id.expected_waste_rate')
    def _compute_expected_waste_rate(self):
        for rec in self:
            rec.expected_waste_rate = rec.bom_id.expected_waste_rate if rec.bom_id else 0.0

    @api.depends('product_qty', 'actual_qty', 'expected_waste_rate')
    def _compute_waste_rates(self):
        for rec in self:
            qty = rec.product_qty or 0.0
            actual = rec.actual_qty or 0.0

            if qty > 0 and actual > 0:
                actual_waste = (qty - actual) / qty * 100.0
                deviation = actual_waste - rec.expected_waste_rate
            else:
                actual_waste = 0.0
                deviation = 0.0

            rec.actual_waste_rate = actual_waste
            rec.waste_rate_deviation = deviation
            rec.is_waste_exceeded = deviation > 3.0