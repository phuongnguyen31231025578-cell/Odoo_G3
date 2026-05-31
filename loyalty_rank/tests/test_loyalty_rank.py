# -*- coding: utf-8 -*-
"""
Test suite: Kiểm tra logic phân hạng khách hàng theo điểm loyalty
Module   : loyalty_rank (inherit res.partner + loyalty.card)
Doanh nghiệp: Trà sữa Châu Viên — Odoo 19 Community
"""

from odoo.tests.common import TransactionCase


class LoyaltyRankBase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.LoyaltyProgram = cls.env['loyalty.program']
        cls.LoyaltyCard = cls.env['loyalty.card']

    def _make_partner(self, name, email=None, phone=None):
        return self.Partner.create({
            'name': name,
            'email': email,
            'phone': phone,
        })

    def _make_loyalty_program(self, name='Test Program'):
        return self.LoyaltyProgram.create({
            'name': name,
            'program_type': 'loyalty',
            'applies_on': 'both',
        })

    def _make_loyalty_card(self, partner, program, points=0.0):
        return self.LoyaltyCard.create({
            'partner_id': partner.id,
            'program_id': program.id,
            'points': points,
        })

    def _set_points(self, card, points):
        card.write({'points': points})


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 1 — Phân hạng theo ngưỡng điểm
# ═══════════════════════════════════════════════════════════════════════════

class TestRankThresholds(LoyaltyRankBase):

    def test_zero_points_is_normal(self):
        partner = self._make_partner("KH Thường")
        prog = self._make_loyalty_program("P1")
        self._make_loyalty_card(partner, prog, points=0)
        self.assertEqual(partner.loyalty_rank, 'normal')
        self.assertEqual(partner.loyalty_rank_label, 'Thường')

    def test_49_points_is_normal(self):
        partner = self._make_partner("KH 49 điểm")
        prog = self._make_loyalty_program("P2")
        self._make_loyalty_card(partner, prog, points=49)
        self.assertEqual(partner.loyalty_rank, 'normal')

    def test_50_points_is_bronze(self):
        partner = self._make_partner("KH Đồng min")
        prog = self._make_loyalty_program("P3")
        self._make_loyalty_card(partner, prog, points=50)
        self.assertEqual(partner.loyalty_rank, 'bronze')
        self.assertEqual(partner.loyalty_rank_label, 'Đồng')

    def test_109_points_is_bronze(self):
        partner = self._make_partner("KH Đồng max")
        prog = self._make_loyalty_program("P4")
        self._make_loyalty_card(partner, prog, points=109)
        self.assertEqual(partner.loyalty_rank, 'bronze')

    def test_110_points_is_silver(self):
        partner = self._make_partner("KH Bạc min")
        prog = self._make_loyalty_program("P5")
        self._make_loyalty_card(partner, prog, points=110)
        self.assertEqual(partner.loyalty_rank, 'silver')
        self.assertEqual(partner.loyalty_rank_label, 'Bạc')

    def test_174_points_is_silver(self):
        partner = self._make_partner("KH Bạc max")
        prog = self._make_loyalty_program("P6")
        self._make_loyalty_card(partner, prog, points=174)
        self.assertEqual(partner.loyalty_rank, 'silver')

    def test_175_points_is_gold(self):
        partner = self._make_partner("KH Vàng min")
        prog = self._make_loyalty_program("P7")
        self._make_loyalty_card(partner, prog, points=175)
        self.assertEqual(partner.loyalty_rank, 'gold')
        self.assertEqual(partner.loyalty_rank_label, 'Vàng')

    def test_254_points_is_gold(self):
        partner = self._make_partner("KH Vàng max")
        prog = self._make_loyalty_program("P8")
        self._make_loyalty_card(partner, prog, points=254)
        self.assertEqual(partner.loyalty_rank, 'gold')

    def test_255_points_is_diamond(self):
        partner = self._make_partner("KH Kim Cương min")
        prog = self._make_loyalty_program("P9")
        self._make_loyalty_card(partner, prog, points=255)
        self.assertEqual(partner.loyalty_rank, 'diamond')
        self.assertEqual(partner.loyalty_rank_label, 'Kim Cương')

    def test_999_points_is_diamond(self):
        partner = self._make_partner("KH Kim Cương max")
        prog = self._make_loyalty_program("P10")
        self._make_loyalty_card(partner, prog, points=999)
        self.assertEqual(partner.loyalty_rank, 'diamond')

    def test_boundary_exactly_50_is_bronze_not_normal(self):
        partner = self._make_partner("Boundary 50")
        prog = self._make_loyalty_program("P11")
        self._make_loyalty_card(partner, prog, points=50)
        self.assertNotEqual(partner.loyalty_rank, 'normal')
        self.assertEqual(partner.loyalty_rank, 'bronze')

    def test_boundary_exactly_110_is_silver_not_bronze(self):
        partner = self._make_partner("Boundary 110")
        prog = self._make_loyalty_program("P12")
        self._make_loyalty_card(partner, prog, points=110)
        self.assertNotEqual(partner.loyalty_rank, 'bronze')
        self.assertEqual(partner.loyalty_rank, 'silver')

    def test_boundary_exactly_175_is_gold_not_silver(self):
        partner = self._make_partner("Boundary 175")
        prog = self._make_loyalty_program("P13")
        self._make_loyalty_card(partner, prog, points=175)
        self.assertNotEqual(partner.loyalty_rank, 'silver')
        self.assertEqual(partner.loyalty_rank, 'gold')

    def test_boundary_exactly_255_is_diamond_not_gold(self):
        partner = self._make_partner("Boundary 255")
        prog = self._make_loyalty_program("P14")
        self._make_loyalty_card(partner, prog, points=255)
        self.assertNotEqual(partner.loyalty_rank, 'gold')
        self.assertEqual(partner.loyalty_rank, 'diamond')


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 2 — Tổng điểm từ nhiều loyalty card
# ═══════════════════════════════════════════════════════════════════════════

class TestMultipleCards(LoyaltyRankBase):

    def test_two_cards_sum_correctly(self):
        partner = self._make_partner("KH 2 thẻ")
        prog1 = self._make_loyalty_program("Prog A")
        prog2 = self._make_loyalty_program("Prog B")
        self._make_loyalty_card(partner, prog1, points=30)
        self._make_loyalty_card(partner, prog2, points=30)
        self.assertEqual(partner.pos_loyalty_points, 60)
        self.assertEqual(partner.loyalty_rank, 'bronze')

    def test_three_cards_sum_correctly(self):
        partner = self._make_partner("KH 3 thẻ")
        prog1 = self._make_loyalty_program("Prog C")
        prog2 = self._make_loyalty_program("Prog D")
        prog3 = self._make_loyalty_program("Prog E")
        self._make_loyalty_card(partner, prog1, points=50)
        self._make_loyalty_card(partner, prog2, points=60)
        self._make_loyalty_card(partner, prog3, points=65)
        self.assertEqual(partner.pos_loyalty_points, 175)
        self.assertEqual(partner.loyalty_rank, 'gold')

    def test_no_card_is_normal_rank(self):
        partner = self._make_partner("KH không thẻ")
        self.assertEqual(partner.pos_loyalty_points, 0)
        self.assertEqual(partner.loyalty_rank, 'normal')

    def test_one_card_zero_points_is_normal(self):
        partner = self._make_partner("KH thẻ 0 điểm")
        prog = self._make_loyalty_program("Prog F")
        self._make_loyalty_card(partner, prog, points=0)
        self.assertEqual(partner.pos_loyalty_points, 0)
        self.assertEqual(partner.loyalty_rank, 'normal')

    def test_sum_of_two_cards_crosses_threshold(self):
        """25 + 25 = 50 → vừa đủ Đồng."""
        partner = self._make_partner("KH vừa đủ Đồng")
        prog1 = self._make_loyalty_program("Prog G")
        prog2 = self._make_loyalty_program("Prog H")
        self._make_loyalty_card(partner, prog1, points=25)
        self._make_loyalty_card(partner, prog2, points=25)
        self.assertEqual(partner.loyalty_rank, 'bronze')

    def test_two_cards_total_254_is_gold_not_diamond(self):
        partner = self._make_partner("KH 254 điểm 2 thẻ")
        prog1 = self._make_loyalty_program("Prog I")
        prog2 = self._make_loyalty_program("Prog J")
        self._make_loyalty_card(partner, prog1, points=127)
        self._make_loyalty_card(partner, prog2, points=127)
        self.assertEqual(partner.pos_loyalty_points, 254)
        self.assertEqual(partner.loyalty_rank, 'gold')


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 3 — Recompute khi loyalty card thay đổi
# ═══════════════════════════════════════════════════════════════════════════

class TestRecompute(LoyaltyRankBase):

    def test_write_points_updates_rank(self):
        partner = self._make_partner("KH tăng hạng")
        prog = self._make_loyalty_program("Prog K")
        card = self._make_loyalty_card(partner, prog, points=40)
        self.assertEqual(partner.loyalty_rank, 'normal')
        self._set_points(card, 60)
        self.assertEqual(partner.loyalty_rank, 'bronze')

    def test_write_points_from_bronze_to_silver(self):
        partner = self._make_partner("KH Đồng lên Bạc")
        prog = self._make_loyalty_program("Prog L")
        card = self._make_loyalty_card(partner, prog, points=80)
        self.assertEqual(partner.loyalty_rank, 'bronze')
        self._set_points(card, 120)
        self.assertEqual(partner.loyalty_rank, 'silver')

    def test_write_points_from_silver_to_gold(self):
        partner = self._make_partner("KH Bạc lên Vàng")
        prog = self._make_loyalty_program("Prog M")
        card = self._make_loyalty_card(partner, prog, points=150)
        self.assertEqual(partner.loyalty_rank, 'silver')
        self._set_points(card, 200)
        self.assertEqual(partner.loyalty_rank, 'gold')

    def test_write_points_from_gold_to_diamond(self):
        partner = self._make_partner("KH Vàng lên Kim Cương")
        prog = self._make_loyalty_program("Prog N")
        card = self._make_loyalty_card(partner, prog, points=200)
        self.assertEqual(partner.loyalty_rank, 'gold')
        self._set_points(card, 300)
        self.assertEqual(partner.loyalty_rank, 'diamond')

    def test_write_points_decreases_rank(self):
        """Điểm giảm → hạng giảm (trường hợp hoàn điểm)."""
        partner = self._make_partner("KH giảm hạng")
        prog = self._make_loyalty_program("Prog O")
        card = self._make_loyalty_card(partner, prog, points=200)
        self.assertEqual(partner.loyalty_rank, 'gold')
        self._set_points(card, 40)
        self.assertEqual(partner.loyalty_rank, 'normal')

    def test_create_card_triggers_recompute(self):
        """Tạo thẻ mới → điểm tổng tăng → rank cập nhật."""
        partner = self._make_partner("KH thêm thẻ")
        prog1 = self._make_loyalty_program("Prog P")
        prog2 = self._make_loyalty_program("Prog Q")
        self._make_loyalty_card(partner, prog1, points=40)
        self.assertEqual(partner.loyalty_rank, 'normal')
        self._make_loyalty_card(partner, prog2, points=20)
        self.assertEqual(partner.loyalty_rank, 'bronze')

    def test_pos_loyalty_points_updates_with_write(self):
        partner = self._make_partner("KH điểm tổng")
        prog = self._make_loyalty_program("Prog R")
        card = self._make_loyalty_card(partner, prog, points=100)
        self.assertEqual(partner.pos_loyalty_points, 100)
        self._set_points(card, 200)
        self.assertEqual(partner.pos_loyalty_points, 200)


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 4 — Rank label hiển thị đúng
# ═══════════════════════════════════════════════════════════════════════════

class TestRankLabel(LoyaltyRankBase):

    def test_normal_label(self):
        partner = self._make_partner("Label Thường")
        prog = self._make_loyalty_program("Prog S")
        self._make_loyalty_card(partner, prog, points=0)
        self.assertEqual(partner.loyalty_rank_label, 'Thường')

    def test_bronze_label(self):
        partner = self._make_partner("Label Đồng")
        prog = self._make_loyalty_program("Prog T")
        self._make_loyalty_card(partner, prog, points=50)
        self.assertEqual(partner.loyalty_rank_label, 'Đồng')

    def test_silver_label(self):
        partner = self._make_partner("Label Bạc")
        prog = self._make_loyalty_program("Prog U")
        self._make_loyalty_card(partner, prog, points=110)
        self.assertEqual(partner.loyalty_rank_label, 'Bạc')

    def test_gold_label(self):
        partner = self._make_partner("Label Vàng")
        prog = self._make_loyalty_program("Prog V")
        self._make_loyalty_card(partner, prog, points=175)
        self.assertEqual(partner.loyalty_rank_label, 'Vàng')

    def test_diamond_label(self):
        partner = self._make_partner("Label Kim Cương")
        prog = self._make_loyalty_program("Prog W")
        self._make_loyalty_card(partner, prog, points=255)
        self.assertEqual(partner.loyalty_rank_label, 'Kim Cương')

    def test_rank_and_label_consistent(self):
        """rank và rank_label phải nhất quán với nhau."""
        partner = self._make_partner("Label consistent")
        prog = self._make_loyalty_program("Prog X")
        self._make_loyalty_card(partner, prog, points=175)
        self.assertEqual(partner.loyalty_rank, 'gold')
        self.assertEqual(partner.loyalty_rank_label, 'Vàng')


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 5 — Decimal points
# ═══════════════════════════════════════════════════════════════════════════

class TestDecimalPoints(LoyaltyRankBase):

    def test_49_99_is_normal(self):
        partner = self._make_partner("KH 49.99")
        prog = self._make_loyalty_program("Prog Y")
        self._make_loyalty_card(partner, prog, points=49.99)
        self.assertEqual(partner.loyalty_rank, 'normal')

    def test_50_01_is_bronze(self):
        partner = self._make_partner("KH 50.01")
        prog = self._make_loyalty_program("Prog Z")
        self._make_loyalty_card(partner, prog, points=50.01)
        self.assertEqual(partner.loyalty_rank, 'bronze')

    def test_decimal_sum_crosses_threshold(self):
        """62.5 + 47.6 = 110.1 → Bạc."""
        partner = self._make_partner("KH decimal sum")
        prog1 = self._make_loyalty_program("Prog AA")
        prog2 = self._make_loyalty_program("Prog BB")
        self._make_loyalty_card(partner, prog1, points=62.5)
        self._make_loyalty_card(partner, prog2, points=47.6)
        self.assertGreaterEqual(partner.pos_loyalty_points, 110)
        self.assertEqual(partner.loyalty_rank, 'silver')

    def test_254_99_is_gold_not_diamond(self):
        partner = self._make_partner("KH 254.99")
        prog = self._make_loyalty_program("Prog CC")
        self._make_loyalty_card(partner, prog, points=254.99)
        self.assertEqual(partner.loyalty_rank, 'gold')

    def test_255_00_is_diamond(self):
        partner = self._make_partner("KH 255.00")
        prog = self._make_loyalty_program("Prog DD")
        self._make_loyalty_card(partner, prog, points=255.00)
        self.assertEqual(partner.loyalty_rank, 'diamond')


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 6 — Nhiều partner độc lập
# ═══════════════════════════════════════════════════════════════════════════

class TestMultiplePartners(LoyaltyRankBase):

    def test_two_partners_independent_ranks(self):
        prog = self._make_loyalty_program("Shared Prog")
        p1 = self._make_partner("KH A")
        p2 = self._make_partner("KH B")
        self._make_loyalty_card(p1, prog, points=30)
        self._make_loyalty_card(p2, prog, points=200)
        self.assertEqual(p1.loyalty_rank, 'normal')
        self.assertEqual(p2.loyalty_rank, 'gold')

    def test_card_of_one_partner_does_not_affect_another(self):
        prog = self._make_loyalty_program("Shared Prog 2")
        p1 = self._make_partner("KH C")
        p2 = self._make_partner("KH D")
        card1 = self._make_loyalty_card(p1, prog, points=40)
        self._make_loyalty_card(p2, prog, points=40)
        self._set_points(card1, 300)
        self.assertEqual(p1.loyalty_rank, 'diamond')
        self.assertEqual(p2.loyalty_rank, 'normal')

    def test_all_five_ranks_at_once(self):
        prog = self._make_loyalty_program("All ranks prog")
        partners_points = [
            ("Thường", 0, 'normal'),
            ("Đồng", 50, 'bronze'),
            ("Bạc", 110, 'silver'),
            ("Vàng", 175, 'gold'),
            ("Kim Cương", 255, 'diamond'),
        ]
        for name, pts, expected_rank in partners_points:
            p = self._make_partner(f"KH {name}")
            self._make_loyalty_card(p, prog, points=pts)
            self.assertEqual(p.loyalty_rank, expected_rank,
                             f"KH {name} ({pts} điểm) phải là {expected_rank}")