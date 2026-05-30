# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from odoo import fields
from datetime import timedelta

class TestVendorEvaluationFullWorkflow(TransactionCase):

    @classmethod
    def setUpClass(cls):
        """ THIẾT LẬP TRẠNG THÁI (ARRANGE): Chuẩn bị dữ liệu mồi trong môi trường cô lập """
        super(TestVendorEvaluationFullWorkflow, cls).setUpClass()
        
        # 1. Tạo Nhà cung cấp A (Điểm cao: 90.0)
        cls.vendor_A = cls.env['res.partner'].create({
            'name': 'Nhà Cung Cấp Uy Tín A',
            'supplier_rank': 1,
            'x_vendor_rating': 90.0,
        })
        
        # 2. Tạo Nhà cung cấp B (Điểm thấp: 50.0)
        cls.vendor_B = cls.env['res.partner'].create({
            'name': 'Nhà Cung Cấp Thường B',
            'supplier_rank': 1,
            'x_vendor_rating': 50.0,
        })

        # 3. Tạo nguyên vật liệu thô mẫu dùng để test
        cls.product = cls.env['product.product'].create({
            'name': 'Nguyên Vật Liệu Thô Của Châu Viên',
            'type': 'consu',
        })

        # 4. Cấu hình bảng giá (Pricelist) báo cho Odoo biết cả 2 ông cùng bán mặt hàng này
        cls.env['product.supplierinfo'].create({
            'partner_id': cls.vendor_A.id,
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'price': 100.0,
        })
        cls.env['product.supplierinfo'].create({
            'partner_id': cls.vendor_B.id,
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'price': 120.0,
        })

    def test_full_purchase_and_scoring_workflow(self):
        """ HÀNH ĐỘNG TÁC ĐỘNG & KẾT QUẢ KỲ VỌNG (ACT & ASSERT) """

        # =====================================================================
        # TRẠM 1: KIỂM TRA WORKFLOW ĐẢO NGƯỢC (Chọn sản phẩm trước -> Gợi ý NCC)
        # =====================================================================
        # Nhân viên mở form tạo mới 1 dòng sản phẩm mua hàng
        po_line = self.env['purchase.order.line'].new({
            'product_id': self.product.id,
            'product_qty': 10,
            'price_unit': 100.0,
        })
        
        # Kích hoạt hàm onchange xử lý gợi ý nhà cung cấp ngầm
        po_line._onchange_product_id_recommend_vendor()
        
        # KIỂM TRA (Assert): Vì ông A (90đ) cao điểm hơn ông B (50đ), hệ thống phải tự động đề xuất ông A
        self.assertEqual(po_line.x_suggested_vendor_id.id, self.vendor_A.id, 
                         "Lỗi Workflow: Hệ thống không đề xuất nhà cung cấp có điểm số cao nhất!")

        # =====================================================================
        # TRẠM 2: KIỂM TRA CHẶN LỖI ĐƠN HÀNG TRỐNG (Bảo vệ dữ liệu RFQ/PO)
        # =====================================================================
        # Tình huống: Nhân viên cố tình tạo 1 đơn RFQ trống không có vật liệu và bấm gửi
        po_empty = self.env['purchase.order'].create({
            'partner_id': self.vendor_A.id,
        })
        # Hệ thống bắt buộc phải quăng lỗi ValidationError chặn đứng lại
        with self.assertRaises(ValidationError):
            po_empty.action_rfq_send()

        # =====================================================================
        # TRẠM 3: XÁC NHẬN PO VÀ TỰ ĐỘNG SINH PHIẾU NHẬP KHO (INCOMING RECEIPT)
        # =====================================================================
        # Tạo một đơn hàng chuẩn khớp luồng gợi ý ở Trạm 1
        po_valid = self.env['purchase.order'].create({
            'partner_id': self.vendor_A.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 10,
                'price_unit': 100.0,
                'name': self.product.name,
                'date_planned': fields.Datetime.now() + timedelta(days=2), # Hẹn giao sau 2 ngày
            })]
        })
        
        # Nhân viên bấm Xác nhận đơn hàng (Confirm Order)
        po_valid.button_confirm()
        
        # KIỂM TRA (Assert): Mã đơn phải đổi sang dạng PO và phải có phiếu nhập kho nháp tự động sinh ra
        self.assertEqual(po_valid.state, 'purchase')
        self.assertTrue(po_valid.picking_ids, "Lỗi Workflow: Hệ thống không tự động tạo Incoming Receipt phiếu kho!")

        # =====================================================================
        # TRẠM 4: KIỂM TRA CHẶN HỦY ĐƠN HÀNG KHI HÀNG ĐÃ VÀO KHO
        # =====================================================================
        # Lấy phiếu nhập kho vừa sinh ra ở trên
        picking = po_valid.picking_ids[0]
        # Giả lập Thủ kho kiểm đếm và bấm nút Validate xác nhận hoàn thành nhập kho (Done)
        picking.button_validate()
        
        # Tình huống: Nhân viên mua hàng bấm Cancel hủy đơn PO khi hàng đã nằm trong kho
        # Hệ thống bắt buộc phải quăng lỗi UserError chặn đứng hành vi gian lận này lại
        with self.assertRaises(UserError):
            po_valid.button_cancel()

        # =====================================================================
        # TRẠM 5: ĐỐI CHIẾU SỐ LƯỢNG 3-WAY MATCHING TRÊN HÓA ĐƠN KẾ TOÁN
        # =====================================================================
        # Nhân viên kế toán bấm Create Bill để tạo hóa đơn nhà cung cấp (Vendor Bill)
        # Nhưng kế toán cố tình khai gian/nhập sai số lượng từ 10 cái lên thành 15 cái
        invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.vendor_A.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 15, # Sai lệch với PO gốc (15 != 10)
                'price_unit': 100.0,
                'name': self.product.name,
                'purchase_line_id': po_valid.order_line[0].id, # Móc nối chéo về PO gốc
            })]
        })
        
        # Kế toán bấm nút Post để xác nhận vào sổ kế toán
        # Hệ thống phát hiện đối chiếu sai lệch, bắt buộc phải văng lỗi UserError chặn dòng tiền lại
        with self.assertRaises(UserError):
            invoice.action_post()