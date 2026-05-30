# -*- coding: utf-8 -*-
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_vendor_rating = fields.Float(string='Điểm đánh giá NCC tổng kết', default=100.0)
    x_quality_score = fields.Float(string='Điểm chất lượng (Max 45)', default=45.0)
    x_price_score = fields.Float(string='Điểm giá cả (Max 30)', default=30.0)
    x_delivery_score = fields.Float(string='Điểm giao hàng (Max 25)', default=25.0)