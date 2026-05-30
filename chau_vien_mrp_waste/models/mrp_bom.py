# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    expected_waste_rate = fields.Float(
        string='Tỷ lệ hao hụt dự kiến (%)',
        default=0.0,
        digits=(5, 2),
        help=(
            'Tỷ lệ hao hụt dự kiến trong quá trình sản xuất (%).\n'
            'Chỉ áp dụng cho BoM loại "Manufacture this product".\n'
            'Dùng để so sánh với hao hụt thực tế khi hoàn tất lệnh sản xuất.'
        ),
    )

    @api.constrains('expected_waste_rate')
    def _check_expected_waste_rate(self):
        for rec in self:
            if rec.expected_waste_rate < 0:
                raise ValidationError(
                    'Tỷ lệ hao hụt dự kiến không được âm.'
                )
            if rec.expected_waste_rate > 100:
                raise ValidationError(
                    'Tỷ lệ hao hụt dự kiến không được vượt quá 100%.'
                )