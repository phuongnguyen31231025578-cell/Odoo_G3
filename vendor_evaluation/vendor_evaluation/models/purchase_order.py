from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Tạo trường lưu điểm trên Form đơn hàng
    x_vendor_rating_display = fields.Float(
        related='partner_id.x_vendor_rating', 
        string='Điểm uy tín nhà cung cấp', 
        readonly=True
    )

    def action_rfq_send(self):
        """ Kiểm tra dữ liệu hợp lệ trước khi gửi báo giá """
        for order in self:
            if not order.partner_id:
                raise ValidationError(_("Vui lòng chọn nhà cung cấp trước khi gửi báo giá!"))
            if not order.order_line:
                raise ValidationError(_("Phiếu RFQ phải có ít nhất một nguyên vật liệu!"))
        return super(PurchaseOrder, self).action_rfq_send()