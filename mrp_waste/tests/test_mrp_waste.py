# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestMrpWasteTracking(TransactionCase):
    """
    Test suite cho module chau_vien_mrp_waste.
    Kiểm tra toàn bộ logic tính toán hao hụt trên BoM và MO.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Tạo sản phẩm bán thành phẩm (BoM type = normal)
        cls.product_tra_sua = cls.env['product.product'].create({
            'name': 'Trà Sữa',
            'type': 'consu',
        })

        # Tạo nguyên vật liệu
        cls.product_sua = cls.env['product.product'].create({
            'name': 'Sữa Bột',
            'type': 'consu',
        })
        cls.product_tra = cls.env['product.product'].create({
            'name': 'Cốt Trà',
            'type': 'consu',
        })

        # Tạo sản phẩm Kit (BoM type = phantom)
        cls.product_hong_tra_sua = cls.env['product.product'].create({
            'name': 'Hồng Trà Sữa',
            'type': 'consu',
        })

        # Lấy UoM mặc định
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

        # Tạo BoM normal với expected_waste_rate = 10%
        cls.bom_tra_sua = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_tra_sua.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'expected_waste_rate': 10.0,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': cls.product_sua.id,
                    'product_qty': 100.0,
                }),
                (0, 0, {
                    'product_id': cls.product_tra.id,
                    'product_qty': 50.0,
                }),
            ],
        })

        # Tạo BoM Kit (phantom) - không cần expected_waste_rate
        cls.bom_kit = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_hong_tra_sua.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'phantom',
            'expected_waste_rate': 0.0,
        })

        # Tạo MO mẫu
        cls.mo = cls.env['mrp.production'].create({
            'product_id': cls.product_tra_sua.id,
            'product_qty': 10.0,
            'bom_id': cls.bom_tra_sua.id,
            'product_uom_id': cls.uom_unit.id,
        })

    # =========================================================
    # NHÓM 1: Kiểm tra BoM
    # =========================================================

    def test_01_bom_expected_waste_rate_default(self):
        """BoM mới tạo phải có expected_waste_rate = 0.0 mặc định."""
        bom_new = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tra_sua.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
        })
        self.assertEqual(
            bom_new.expected_waste_rate, 0.0,
            "expected_waste_rate mặc định phải là 0.0"
        )

    def test_02_bom_expected_waste_rate_set(self):
        """Kiểm tra set expected_waste_rate = 10% thành công."""
        self.assertEqual(
            self.bom_tra_sua.expected_waste_rate, 10.0,
            "expected_waste_rate phải là 10.0"
        )

    def test_03_bom_expected_waste_rate_negative_raises(self):
        """expected_waste_rate âm phải raise ValidationError."""
        with self.assertRaises(ValidationError):
            self.env['mrp.bom'].create({
                'product_tmpl_id': self.product_tra_sua.product_tmpl_id.id,
                'product_qty': 1.0,
                'type': 'normal',
                'expected_waste_rate': -5.0,
            })

    def test_04_bom_expected_waste_rate_over_100_raises(self):
        """expected_waste_rate > 100 phải raise ValidationError."""
        with self.assertRaises(ValidationError):
            self.env['mrp.bom'].create({
                'product_tmpl_id': self.product_tra_sua.product_tmpl_id.id,
                'product_qty': 1.0,
                'type': 'normal',
                'expected_waste_rate': 101.0,
            })

    def test_05_bom_expected_waste_rate_boundary_zero(self):
        """expected_waste_rate = 0 phải hợp lệ."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tra_sua.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'expected_waste_rate': 0.0,
        })
        self.assertEqual(bom.expected_waste_rate, 0.0)

    def test_06_bom_expected_waste_rate_boundary_100(self):
        """expected_waste_rate = 100 phải hợp lệ (boundary)."""
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tra_sua.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'expected_waste_rate': 100.0,
        })
        self.assertEqual(bom.expected_waste_rate, 100.0)

    # =========================================================
    # NHÓM 2: Kiểm tra MO lấy expected_waste_rate từ BoM
    # =========================================================

    def test_07_mo_inherits_expected_waste_rate_from_bom(self):
        """MO phải tự lấy expected_waste_rate từ BoM."""
        self.assertEqual(
            self.mo.expected_waste_rate, 10.0,
            "MO phải kế thừa expected_waste_rate = 10.0 từ BoM"
        )

    def test_08_mo_no_bom_expected_waste_rate_zero(self):
        """MO không có BoM thì expected_waste_rate = 0."""
        product_no_bom = self.env['product.product'].create({
            'name': 'San Pham Khong Co BOM Test 08',
            'type': 'consu',
        })
        mo_no_bom = self.env['mrp.production'].create({
            'product_id': product_no_bom.id,
            'product_qty': 5.0,
            'product_uom_id': self.uom_unit.id,
        })
        self.assertEqual(mo_no_bom.expected_waste_rate, 0.0)

    # =========================================================
    # NHÓM 3: Kiểm tra tính toán actual_waste_rate
    # =========================================================

    def test_09_actual_waste_rate_normal(self):
        """
        MO: qty=10, actual_qty=9
        actual_waste_rate = (10-9)/10 * 100 = 10%
        """
        self.mo.actual_qty = 9.0
        self.assertAlmostEqual(
            self.mo.actual_waste_rate, 10.0, places=2,
            msg="actual_waste_rate phải là 10.0%"
        )

    def test_10_actual_waste_rate_no_loss(self):
        """
        MO: qty=10, actual_qty=10
        actual_waste_rate = 0%
        """
        self.mo.actual_qty = 10.0
        self.assertAlmostEqual(
            self.mo.actual_waste_rate, 0.0, places=2,
            msg="actual_waste_rate phải là 0.0% khi không có hao hụt"
        )

    def test_11_actual_waste_rate_total_loss(self):
        """
        MO: qty=10, actual_qty=0 (chưa nhập)
        actual_waste_rate = 0 (không tính khi actual_qty = 0)
        """
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 10.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        mo.actual_qty = 0.0
        self.assertAlmostEqual(
            mo.actual_waste_rate, 0.0, places=2,
            msg="actual_waste_rate phải là 0 khi actual_qty chưa nhập"
        )

    def test_12_actual_waste_rate_high_loss(self):
        """
        MO: qty=10, actual_qty=5
        actual_waste_rate = (10-5)/10 * 100 = 50%
        """
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 10.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        mo.actual_qty = 5.0
        self.assertAlmostEqual(
            mo.actual_waste_rate, 50.0, places=2,
            msg="actual_waste_rate phải là 50.0%"
        )

    # =========================================================
    # NHÓM 4: Kiểm tra waste_rate_deviation
    # =========================================================

    def test_13_deviation_zero_when_actual_equals_expected(self):
        """
        expected=10%, actual=10% → deviation=0%
        """
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 10.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        mo.actual_qty = 9.0  # (10-9)/10 = 10% = expected
        self.assertAlmostEqual(
            mo.waste_rate_deviation, 0.0, places=2,
            msg="deviation phải là 0 khi actual = expected"
        )

    def test_14_deviation_positive_when_actual_exceeds_expected(self):
        """
        expected=10%, actual=20% → deviation=+10%
        qty=10, actual_qty=8 → actual_waste=(10-8)/10*100=20%
        """
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 10.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        mo.actual_qty = 8.0
        self.assertAlmostEqual(
            mo.waste_rate_deviation, 10.0, places=2,
            msg="deviation phải là +10% khi actual vượt expected"
        )

    def test_15_deviation_negative_when_actual_below_expected(self):
        """
        expected=10%, actual=5% → deviation=-5%
        qty=10, actual_qty=9.5 → actual_waste=(10-9.5)/10*100=5%
        """
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 10.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        mo.actual_qty = 9.5
        self.assertAlmostEqual(
            mo.waste_rate_deviation, -5.0, places=2,
            msg="deviation phải là -5% khi actual thấp hơn expected"
        )

    # =========================================================
    # NHÓM 5: Kiểm tra is_waste_exceeded (tô đỏ)
    # =========================================================

    def test_16_is_waste_exceeded_false_when_deviation_below_3(self):
        """deviation = 2% → is_waste_exceeded = False"""
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 100.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        # actual_waste = 12%, expected = 10%, deviation = 2%
        mo.actual_qty = 88.0
        self.assertFalse(
            mo.is_waste_exceeded,
            "is_waste_exceeded phải False khi deviation = 2% < 3%"
        )

    def test_17_is_waste_exceeded_false_when_deviation_equals_3(self):
        """deviation = 3% → is_waste_exceeded = False (ngưỡng là >3%, không phải >=3%)"""
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 100.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        # actual_waste = 13%, expected = 10%, deviation = 3%
        mo.actual_qty = 87.0
        self.assertFalse(
            mo.is_waste_exceeded,
            "is_waste_exceeded phải False khi deviation = 3% (không vượt)"
        )

    def test_18_is_waste_exceeded_true_when_deviation_above_3(self):
        """deviation > 3% → is_waste_exceeded = True → tô đỏ"""
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 100.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        # actual_waste = 14%, expected = 10%, deviation = 4%
        mo.actual_qty = 86.0
        self.assertTrue(
            mo.is_waste_exceeded,
            "is_waste_exceeded phải True khi deviation = 4% > 3%"
        )

    def test_19_is_waste_exceeded_false_when_no_actual_qty(self):
        """Chưa nhập actual_qty → is_waste_exceeded = False"""
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 10.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        self.assertFalse(
            mo.is_waste_exceeded,
            "is_waste_exceeded phải False khi chưa nhập actual_qty"
        )

    def test_20_is_waste_exceeded_false_when_negative_deviation(self):
        """deviation âm (hao hụt thực tế thấp hơn dự kiến) → is_waste_exceeded = False"""
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 10.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        mo.actual_qty = 9.8  # actual_waste = 2%, deviation = -8%
        self.assertFalse(
            mo.is_waste_exceeded,
            "is_waste_exceeded phải False khi deviation âm"
        )

    # =========================================================
    # NHÓM 6: Edge cases tính toán
    # =========================================================

    def test_21_actual_qty_greater_than_product_qty(self):
        """
        actual_qty > product_qty → actual_waste_rate âm, deviation âm,
        is_waste_exceeded = False.
        qty=10, actual_qty=11 → actual_waste = (10-11)/10*100 = -10%
        """
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 10.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        mo.actual_qty = 11.0
        self.assertAlmostEqual(
            mo.actual_waste_rate, -10.0, places=2,
            msg="actual_waste_rate phải âm khi actual_qty > product_qty"
        )
        self.assertFalse(
            mo.is_waste_exceeded,
            "is_waste_exceeded phải False khi actual_qty > product_qty"
        )

    def test_22_product_qty_zero_no_division_error(self):
        """
        actual_qty = 0 không được gây ZeroDivisionError.
        Tất cả computed fields phải trả về 0.
        """
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 1.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        mo.actual_qty = 0.0
        try:
            _ = mo.actual_waste_rate
            _ = mo.waste_rate_deviation
            _ = mo.is_waste_exceeded
        except ZeroDivisionError:
            self.fail("ZeroDivisionError khi actual_qty = 0")
        self.assertAlmostEqual(mo.actual_waste_rate, 0.0, places=2)
        self.assertFalse(mo.is_waste_exceeded)

    def test_23_decimal_qty_calculation(self):
        """
        Số thập phân lẻ: qty=3, actual_qty=2.7
        actual_waste = (3-2.7)/3*100 = 10%
        deviation = 10% - 10% = 0%
        """
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 3.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        mo.actual_qty = 2.7
        self.assertAlmostEqual(
            mo.actual_waste_rate, 10.0, places=2,
            msg="actual_waste_rate phải là 10% với qty thập phân"
        )
        self.assertAlmostEqual(
            mo.waste_rate_deviation, 0.0, places=2,
            msg="deviation phải là 0% khi actual = expected"
        )

    def test_24_large_qty_calculation(self):
        """
        Số lượng lớn: qty=1000, actual_qty=850
        actual_waste = (1000-850)/1000*100 = 15%
        deviation = 15% - 10% = 5% → is_waste_exceeded = True
        """
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 1000.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        mo.actual_qty = 850.0
        self.assertAlmostEqual(mo.actual_waste_rate, 15.0, places=2)
        self.assertAlmostEqual(mo.waste_rate_deviation, 5.0, places=2)
        self.assertTrue(mo.is_waste_exceeded)

    # =========================================================
    # NHÓM 7: Thay đổi BoM sau khi tạo MO
    # =========================================================

    def test_25_change_bom_on_mo_updates_expected_waste_rate(self):
        """
        Đổi BoM trên MO → expected_waste_rate phải cập nhật theo BoM mới.
        """
        bom_new = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tra_sua.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'expected_waste_rate': 25.0,
        })
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 10.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        self.assertAlmostEqual(mo.expected_waste_rate, 10.0, places=2)
        mo.bom_id = bom_new
        self.assertAlmostEqual(
            mo.expected_waste_rate, 25.0, places=2,
            msg="expected_waste_rate phải cập nhật khi đổi BoM"
        )

    def test_26_remove_bom_from_mo_resets_expected_waste_rate(self):
        """
        Xóa BoM khỏi MO → expected_waste_rate phải về 0.
        """
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 10.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        self.assertAlmostEqual(mo.expected_waste_rate, 10.0, places=2)
        mo.bom_id = False
        self.assertAlmostEqual(
            mo.expected_waste_rate, 0.0, places=2,
            msg="expected_waste_rate phải về 0 khi xóa BoM"
        )

    # =========================================================
    # NHÓM 8: Thay đổi expected_waste_rate trên BoM
    # =========================================================

    def test_27_update_bom_waste_rate_recomputes_mo(self):
        """
        Sửa expected_waste_rate trên BoM → MO đang dùng BoM đó
        phải recompute expected_waste_rate.
        """
        bom_editable = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tra_sua.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'expected_waste_rate': 5.0,
        })
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 10.0,
            'bom_id': bom_editable.id,
            'product_uom_id': self.uom_unit.id,
        })
        self.assertAlmostEqual(mo.expected_waste_rate, 5.0, places=2)
        bom_editable.expected_waste_rate = 20.0
        self.assertAlmostEqual(
            mo.expected_waste_rate, 20.0, places=2,
            msg="MO phải recompute expected_waste_rate khi BoM thay đổi"
        )

    def test_28_update_bom_waste_rate_recomputes_deviation(self):
        """
        Sửa expected_waste_rate trên BoM → deviation và is_waste_exceeded
        trên MO đã có actual_qty phải recompute lại.
        qty=10, actual_qty=8 → actual_waste=20%
        Ban đầu expected=10% → deviation=10% → exceeded=True
        Sau khi đổi expected=20% → deviation=0% → exceeded=False
        """
        bom_editable = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tra_sua.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'expected_waste_rate': 10.0,
        })
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 10.0,
            'bom_id': bom_editable.id,
            'product_uom_id': self.uom_unit.id,
        })
        mo.actual_qty = 8.0
        self.assertTrue(mo.is_waste_exceeded)
        bom_editable.expected_waste_rate = 20.0
        self.assertAlmostEqual(mo.waste_rate_deviation, 0.0, places=2)
        self.assertFalse(
            mo.is_waste_exceeded,
            "is_waste_exceeded phải False sau khi BoM cập nhật expected=20%"
        )

    # =========================================================
    # NHÓM 9: Cập nhật actual_qty nhiều lần
    # =========================================================

    def test_29_update_actual_qty_multiple_times(self):
        """
        Nhập actual_qty nhiều lần → computed fields luôn recompute đúng.
        """
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 10.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        # Lần 1: actual_qty=8 → actual_waste=20%, deviation=10% → exceeded
        mo.actual_qty = 8.0
        self.assertAlmostEqual(mo.actual_waste_rate, 20.0, places=2)
        self.assertTrue(mo.is_waste_exceeded)
        # Lần 2: actual_qty=9.5 → actual_waste=5%, deviation=-5% → không exceeded
        mo.actual_qty = 9.5
        self.assertAlmostEqual(mo.actual_waste_rate, 5.0, places=2)
        self.assertAlmostEqual(mo.waste_rate_deviation, -5.0, places=2)
        self.assertFalse(mo.is_waste_exceeded)
        # Lần 3: actual_qty=8.6 → actual_waste=14%, deviation=4% → exceeded
        mo.actual_qty = 8.6
        self.assertAlmostEqual(mo.actual_waste_rate, 14.0, places=2)
        self.assertTrue(mo.is_waste_exceeded)

    def test_30_reset_actual_qty_to_zero(self):
        """
        Nhập actual_qty rồi reset về 0 → các field phải về 0,
        is_waste_exceeded = False.
        """
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 10.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        mo.actual_qty = 8.0
        self.assertTrue(mo.is_waste_exceeded)
        mo.actual_qty = 0.0
        self.assertAlmostEqual(mo.actual_waste_rate, 0.0, places=2)
        self.assertAlmostEqual(mo.waste_rate_deviation, 0.0, places=2)
        self.assertFalse(
            mo.is_waste_exceeded,
            "is_waste_exceeded phải False khi reset actual_qty về 0"
        )

    # =========================================================
    # NHÓM 10: Ngưỡng 3% chính xác
    # =========================================================

    def test_31_deviation_just_above_3_percent(self):
        """
        deviation > 3% → is_waste_exceeded = True.
        qty=100, actual_qty=85.9
        actual_waste = (100-85.9)/100*100 = 14.1%
        deviation = 14.1% - 10% = 4.1%
        """
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 100.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        mo.actual_qty = 85.9
        self.assertGreater(mo.waste_rate_deviation, 3.0)
        self.assertTrue(
            mo.is_waste_exceeded,
            "is_waste_exceeded phải True khi deviation > 3%"
        )

    def test_32_deviation_just_below_3_percent(self):
        """
        deviation < 3% → is_waste_exceeded = False.
        qty=100, actual_qty=87.1
        actual_waste = (100-87.1)/100*100 = 12.9%
        deviation = 12.9% - 10% = 2.9%
        """
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 100.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        mo.actual_qty = 87.1
        self.assertLess(mo.waste_rate_deviation, 3.0)
        self.assertFalse(
            mo.is_waste_exceeded,
            "is_waste_exceeded phải False khi deviation < 3%"
        )

    def test_33_deviation_exactly_3_percent(self):
        """
        deviation = 3.0% chính xác → is_waste_exceeded = False
        (ngưỡng là STRICTLY > 3%, không phải >= 3%)
        qty=100, actual_qty=87 → actual_waste=13%, deviation=3%
        """
        mo = self.env['mrp.production'].create({
            'product_id': self.product_tra_sua.id,
            'product_qty': 100.0,
            'bom_id': self.bom_tra_sua.id,
            'product_uom_id': self.uom_unit.id,
        })
        mo.actual_qty = 87.0
        self.assertAlmostEqual(mo.waste_rate_deviation, 3.0, places=2)
        self.assertFalse(
            mo.is_waste_exceeded,
            "is_waste_exceeded phải False khi deviation = đúng 3% (không vượt)"
        )