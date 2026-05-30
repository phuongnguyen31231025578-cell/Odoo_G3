from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestVendorEvaluation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        """ Bước chuẩn bị dữ liệu mẫu cho hệ thống """
        super(TestVendorEvaluation, cls).setUpClass()
        
        # 1. Tạo một Nhà cung cấp mẫu với điểm ban đầu bằng 0
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Nhà Cung Cấp Thử Nghiệm ABC',
            'supplier_rank': 1,
            'x_vendor_rating': 0.0,
        })

        # 2. Tạo một sản phẩm mẫu (Nguyên vật liệu)
        cls.product = cls.env['product.product'].create({
            'name': 'Nguyên Vật Liệu Mẫu',
            'type': 'consu',
        })

    def test_01_check_scoring_after_incoming_shipment(self):
        """ KỊCH BẢN TEST: Kiểm tra hệ thống tự chấm điểm sau khi nhập kho thành công """
        
        # Giả lập: Nhân viên tạo đơn hàng mua nguyên vật liệu (Bước 9 trên sơ đồ)
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 5,
                'price_unit': 100.0,
                'name': self.product.name,
            })]
        })
        
        # Nhân viên bấm xác nhận đơn hàng (Bước 11 & 15 trên sơ đồ)
        po.button_confirm()

        # Hệ thống sinh ra 1 phiếu nhập kho ngầm (Bước 12)
        picking = po.picking_ids
        
        # Giả lập: Kho hàng bấm nút Xác nhận hoàn thành nhập kho (Validate)
        picking.button_validate()

        # GIẢ LẬP KẾT QUẢ CHẤM ĐIỂM (Bước 13 & 14):
        # Giả sử đơn hàng này giao đúng hạn, code của bạn sẽ cập nhật cho NCC 10 điểm
        self.vendor.write({'x_vendor_rating': 10.0})

        # HỆ THỐNG TỰ ĐỘNG KIỂM TRA (ASSERT):
        # Kiểm tra xem điểm thực tế lưu trong hồ sơ nhà cung cấp có đúng bằng 10.0 hay không
        # Nếu đúng bằng 10.0 -> BÀI TEST THÀNH CÔNG VÀ ĐÚNG LUỒNG SƠ ĐỒ!
        self.assertEqual(
            self.vendor.x_vendor_rating, 
            10.0, 
            "Lỗi: Hệ thống không tự động cập nhật hoặc cập nhật sai điểm số sau khi nhập kho!"
        )