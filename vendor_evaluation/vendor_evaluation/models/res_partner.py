from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Trường lưu điểm tổng kết của nhà cung cấp
    x_vendor_rating = fields.Float(string='Điểm đánh giá NCC', default=0.0)