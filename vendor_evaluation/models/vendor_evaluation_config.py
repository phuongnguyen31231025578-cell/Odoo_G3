# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class VendorEvaluationCriteria(models.Model):
    _name = 'vendor.evaluation.criteria'
    _description = 'Tiêu chí chấm điểm nhà cung cấp'

    name = fields.Char(string='Tên tiêu chí', required=True)
    code = fields.Selection([
        ('quality', 'Chất lượng hàng hóa'),
        ('price', 'Giá cả'),
        ('delivery', 'Giao hàng đúng hạn')
    ], string='Mã hệ thống', required=True)
    weight = fields.Float(string='Điểm tối đa', required=True, default=0.0)
    active = fields.Boolean(string='Kích hoạt', default=True)

    @api.constrains('weight', 'active')
    def _check_total_weight(self):
        """ Sơ đồ 1.4: Tổng điểm cấu hình bắt buộc phải bằng đúng 100 điểm """
        # Thêm điều kiện: Nếu hệ thống đang trong quá trình cài đặt/nạp file XML data đầu kỳ thì bỏ qua không chặn lỗi
        if self.env.context.get('install_mode') or self.env.context.get('module_update'):
            return True
            
        active_criteria = self.search([('active', '=', True)])
        total_weight = sum(criterion.weight for criterion in active_criteria)
        if total_weight != 100.0 and total_weight != 0.0:
            raise ValidationError(_("Quy tắc không hợp lệ! Tổng điểm tối đa phải bằng 100 điểm. Hiện tại là: %s điểm.") % total_weight)