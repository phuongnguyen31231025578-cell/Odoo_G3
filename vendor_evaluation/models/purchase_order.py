# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Sửa thuộc tính bắt buộc của Odoo gốc thành False lúc nháp để nhân viên thực hiện bước chọn sản phẩm trước
    partner_id = fields.Many2one('res.partner', string='Nhà cung cấp', required=False, domain=[('supplier_rank', '>', 0)])

    # Hiển thị điểm uy tín của NCC ngay trên header đơn hàng (related từ đối tác)
    x_vendor_rating = fields.Float(
        related='partner_id.x_vendor_rating',
        string='Điểm uy tín NCC (/100)',
        readonly=True,
    )

    def action_rfq_send(self):
        """ Luồng RFQ: Kiểm tra dữ liệu hợp lệ trước khi cho gửi mail """
        for order in self:
            if not order.partner_id:
                raise ValidationError(_("Dữ liệu không hợp lệ: Vui lòng chọn nhà cung cấp trước khi gửi báo giá!"))
            if not order.order_line:
                raise ValidationError(_("Dữ liệu không hợp lệ: Phiếu RFQ phải có ít nhất một nguyên vật liệu!"))
        return super(PurchaseOrder, self).action_rfq_send()

    def button_confirm(self):
        """ Luồng PO: Xác nhận PO -> Kiểm tra tính hợp lệ -> Tự động sinh phiếu kho ngầm """
        for order in self:
            if not order.partner_id:
                raise ValidationError(_("Dữ liệu không hợp lệ: Chưa chọn nhà cung cấp cho đơn hàng!"))
            if not order.order_line:
                raise ValidationError(_("Dữ liệu không hợp lệ: Đơn mua hàng phải có ít nhất một nguyên vật liệu!"))
            # Chặn nhà cung cấp dưới mức sàn uy tín 40 điểm
            if order.partner_id.x_vendor_rating < 40.0:
                raise ValidationError(_("Dữ liệu không hợp lệ: Nhà cung cấp %s có điểm uy tín quá thấp (%s/100).") % (order.partner_id.name, order.partner_id.x_vendor_rating))
        
        # Gọi hàm gốc super() để Odoo tự động chuyển trạng thái sang PO và TỰ ĐỘNG SINH INCOMING RECEIPT
        return super(PurchaseOrder, self).button_confirm()

    def button_cancel(self):
        """ Luồng Hủy đơn: Kiểm tra xem đã nhập kho chưa để rẽ nhánh xử lý """
        # B1: Kiểm tra toàn bộ đơn trước - nếu bất kỳ đơn nào đã nhập kho thì chặn
        for order in self:
            if any(p.state == 'done' for p in order.picking_ids):
                # [Đã nhập kho] -> Thông báo không hủy được
                raise UserError(_("Thông báo: Không thể hủy đơn hàng! Hệ thống kiểm tra thấy đơn hàng này đã có sản phẩm nhập kho thực tế."))

        # B2: [Chưa nhập kho] -> Gọi gốc super() một lần để chuyển trạng thái sang Cancelled
        res = super(PurchaseOrder, self).button_cancel()

        # B3: Tự động hủy luôn các phiếu nhập kho liên quan đang treo chưa hoàn thành
        for order in self:
            pickings_to_cancel = order.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
            if pickings_to_cancel:
                pickings_to_cancel.action_cancel()
                order.message_post(body=_("Hệ thống Odoo 19: Đã tự động hủy %s phiếu nhập kho liên quan đang treo.") % len(pickings_to_cancel))

        return res

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_suggested_vendor_id = fields.Many2one('res.partner', string='Nhà cung cấp đề xuất', domain=[('supplier_rank', '>', 0)])
    x_vendor_score_display = fields.Float(related='x_suggested_vendor_id.x_vendor_rating', string='Điểm số', readonly=True)

    @api.onchange('product_id')
    def _onchange_product_id_recommend_vendor(self):
        """ BƯỚC 1: Chọn sản phẩm trước -> BƯỚC 2: Gợi ý danh sách NCC xếp từ CAO xuống THẤP """
        if not self.product_id:
            return {}
        supplier_infos = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)])
        # Odoo 19: product.supplierinfo dùng field 'partner_id' (không còn field 'name')
        vendor_ids = supplier_infos.mapped('partner_id').ids
        # Sắp xếp giảm dần (desc) theo điểm số uy tín tổng kết của nhà cung cấp
        vendors = self.env['res.partner'].search([('id', 'in', vendor_ids)], order='x_vendor_rating desc')
        if vendors:
            best_vendor = vendors[0]  # NCC điểm cao nhất (tránh lỗi singleton khi có nhiều NCC)
            self.x_suggested_vendor_id = best_vendor
            self.order_id.partner_id = best_vendor  # BƯỚC 3: Đồng bộ NCC tốt nhất ra ô đối tác tổng
        return {'domain': {'x_suggested_vendor_id': [('id', 'in', vendors.ids)]}}

    @api.onchange('x_suggested_vendor_id')
    def _onchange_x_suggested_vendor_id(self):
        """ Cập nhật lại Nhà cung cấp tổng của đơn hàng khi nhân viên thay đổi lựa chọn trên dòng """
        if self.x_suggested_vendor_id:
            self.order_id.partner_id = self.x_suggested_vendor_id.id