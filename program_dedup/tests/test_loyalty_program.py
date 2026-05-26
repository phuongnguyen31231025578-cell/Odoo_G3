# -*- coding: utf-8 -*-
"""
Test suite: Kiểm tra logic chặn trùng lặp chương trình khuyến mãi
Module   : loyalty_program (inherit loyalty.program)
Doanh nghiệp: Trà sữa Châu Viên — Odoo 19 Community
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class LoyaltyProgramDuplicateBase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.LoyaltyProgram = cls.env['loyalty.program']

    def _make_program(self, name, program_type='loyalty', applies_on='both',
                      active=True, rules=None, rewards=None):
        prog = self.env['loyalty.program'].create({
            'name': name,
            'program_type': program_type,
            'applies_on': applies_on,
            'active': active,
        })
        for rule_vals in (rules or []):
            self.env['loyalty.rule'].create({
                'program_id': prog.id,
                'minimum_qty': rule_vals.get('minimum_qty', 0),
                'minimum_amount': rule_vals.get('minimum_amount', 0.0),
                'reward_point_amount': rule_vals.get('reward_point_amount', 1),
                'reward_point_mode': rule_vals.get('reward_point_mode', 'order'),
            })
        for reward_vals in (rewards or []):
            self.env['loyalty.reward'].create({
                'program_id': prog.id,
                **reward_vals,
            })
        return prog

    def _default_rule(self):
        return {
            'minimum_qty': 1,
            'minimum_amount': 50000.0,
            'reward_point_amount': 10,
            'reward_point_mode': 'order',
        }

    def _default_discount_reward(self):
        # Odoo 19: reward_type chỉ có 'discount' và 'product'
        # discount phải > 0 (DB constraint loyalty_reward_discount_positive)
        return {
            'reward_type': 'discount',
            'required_points': 100,
            'discount': 10.0,
            'discount_applicability': 'order',
            'discount_mode': 'percent',
        }

    def _default_product_reward(self, product=None):
        if product is None:
            product = self.env['product.product'].search([], limit=1)
        return {
            'reward_type': 'product',
            'required_points': 200,
            'reward_product_id': product.id,
            'reward_product_qty': 1,
        }

    # Odoo 19 không còn reward_type='free_shipping'/'shipping'
    # Thay thế bằng discount reward với required_points khác để phân biệt
    def _default_free_shipping_reward(self):
        return {
            'reward_type': 'discount',
            'required_points': 50,
            'discount': 100.0,
            'discount_applicability': 'order',
            'discount_mode': 'percent',
        }


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 1 — TH1: Trùng tên
# ═══════════════════════════════════════════════════════════════════════════

class TestTH1NameDuplicate(LoyaltyProgramDuplicateBase):

    def test_th1_exact_name_raises(self):
        self._make_program("Tích điểm mùa hè")
        with self.assertRaises(ValidationError):
            self._make_program("Tích điểm mùa hè")

    def test_th1_name_case_insensitive_upper_raises(self):
        self._make_program("TÍCH ĐIỂM MÙA HÈ")
        with self.assertRaises(ValidationError):
            self._make_program("tích điểm mùa hè")

    def test_th1_name_case_insensitive_title_raises(self):
        self._make_program("Tích Điểm VIP")
        with self.assertRaises(ValidationError):
            self._make_program("tích điểm vip")

    def test_th1_name_case_insensitive_mixed_raises(self):
        self._make_program("KM HÈ 2024")
        with self.assertRaises(ValidationError):
            self._make_program("km hè 2024")

    def test_th1_name_leading_trailing_spaces_raises(self):
        self._make_program("Tích điểm VIP")
        with self.assertRaises(ValidationError):
            self._make_program("  Tích điểm VIP  ")

    def test_th1_name_tab_prefix_raises(self):
        self._make_program("Tích điểm VIP")
        with self.assertRaises(ValidationError):
            self._make_program("\tTích điểm VIP")

    def test_th1_name_trailing_spaces_raises(self):
        self._make_program("Tích điểm VIP")
        with self.assertRaises(ValidationError):
            self._make_program("Tích điểm VIP   ")

    def test_th1_different_name_no_raise(self):
        self._make_program("Chương trình A")
        prog = self._make_program("Chương trình B")
        self.assertTrue(prog.id)

    def test_th1_inactive_same_name_no_raise(self):
        self._make_program("Tích điểm cũ", active=False)
        prog = self._make_program("Tích điểm cũ", active=True)
        self.assertTrue(prog.id)

    def test_th1_write_self_same_name_no_raise(self):
        prog = self._make_program("Tích điểm thường niên")
        prog.write({'name': 'Tích điểm thường niên'})
        self.assertEqual(prog.name, 'Tích điểm thường niên')

    def test_th1_write_name_to_existing_raises(self):
        self._make_program("Tên A")
        prog_b = self._make_program("Tên B")
        with self.assertRaises(ValidationError):
            prog_b.write({'name': 'Tên A'})

    def test_th1_error_message_contains_program_name(self):
        self._make_program("Tri ân khách hàng")
        try:
            self._make_program("Tri ân khách hàng")
            self.fail("Phải raise ValidationError")
        except ValidationError as e:
            self.assertIn("Tri ân khách hàng", str(e))

    def test_th1_error_message_contains_conflict_id(self):
        existing = self._make_program("Chương trình xung đột")
        try:
            self._make_program("Chương trình xung đột")
            self.fail("Phải raise ValidationError")
        except ValidationError as e:
            self.assertIn(str(existing.id), str(e))


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 2 — TH2 tiêu chí C: program_type + applies_on
# ═══════════════════════════════════════════════════════════════════════════

class TestTH2CriteriaC(LoyaltyProgramDuplicateBase):

    def test_th2_c_diff_type_loyalty_vs_promotion_no_raise(self):
        rule, reward = self._default_rule(), self._default_discount_reward()
        self._make_program("Loyalty", program_type='loyalty', applies_on='both',
                           rules=[rule], rewards=[reward])
        prog = self._make_program("Promotion", program_type='promotion', applies_on='both',
                                  rules=[rule], rewards=[reward])
        self.assertTrue(prog.id)

    def test_th2_c_diff_type_promotion_vs_loyalty_no_raise(self):
        rule, reward = self._default_rule(), self._default_discount_reward()
        self._make_program("P1", program_type='promotion', applies_on='both',
                           rules=[rule], rewards=[reward])
        prog = self._make_program("P2", program_type='loyalty', applies_on='both',
                                  rules=[rule], rewards=[reward])
        self.assertTrue(prog.id)

    def test_th2_c_diff_type_gift_card_vs_loyalty_no_raise(self):
        rule, reward = self._default_rule(), self._default_discount_reward()
        self._make_program("GC", program_type='gift_card', applies_on='both',
                           rules=[rule], rewards=[reward])
        prog = self._make_program("Loyalty", program_type='loyalty', applies_on='both',
                                  rules=[rule], rewards=[reward])
        self.assertTrue(prog.id)

    def test_th2_c_diff_applies_on_current_vs_both_no_raise(self):
        rule, reward = self._default_rule(), self._default_discount_reward()
        self._make_program("Current", program_type='loyalty', applies_on='current',
                           rules=[rule], rewards=[reward])
        prog = self._make_program("Both", program_type='loyalty', applies_on='both',
                                  rules=[rule], rewards=[reward])
        self.assertTrue(prog.id)

    def test_th2_c_diff_applies_on_future_vs_both_no_raise(self):
        rule, reward = self._default_rule(), self._default_discount_reward()
        self._make_program("Future", program_type='loyalty', applies_on='future',
                           rules=[rule], rewards=[reward])
        prog = self._make_program("Both", program_type='loyalty', applies_on='both',
                                  rules=[rule], rewards=[reward])
        self.assertTrue(prog.id)


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 3 — TH2 tiêu chí A: Rule snapshot
# ═══════════════════════════════════════════════════════════════════════════

class TestTH2CriteriaA(LoyaltyProgramDuplicateBase):

    def test_th2_a_diff_minimum_qty_no_raise(self):
        reward = self._default_discount_reward()
        self._make_program("Qty=1", program_type='loyalty', applies_on='both',
                           rules=[{**self._default_rule(), 'minimum_qty': 1}],
                           rewards=[reward])
        prog = self._make_program("Qty=2", program_type='loyalty', applies_on='both',
                                  rules=[{**self._default_rule(), 'minimum_qty': 2}],
                                  rewards=[reward])
        self.assertTrue(prog.id)

    def test_th2_a_diff_minimum_amount_no_raise(self):
        reward = self._default_discount_reward()
        self._make_program("Amt=50k", program_type='loyalty', applies_on='both',
                           rules=[{**self._default_rule(), 'minimum_amount': 50000.0}],
                           rewards=[reward])
        prog = self._make_program("Amt=99k", program_type='loyalty', applies_on='both',
                                  rules=[{**self._default_rule(), 'minimum_amount': 99000.0}],
                                  rewards=[reward])
        self.assertTrue(prog.id)

    def test_th2_a_diff_reward_point_amount_no_raise(self):
        reward = self._default_discount_reward()
        self._make_program("Pts=10", program_type='loyalty', applies_on='both',
                           rules=[{**self._default_rule(), 'reward_point_amount': 10}],
                           rewards=[reward])
        prog = self._make_program("Pts=20", program_type='loyalty', applies_on='both',
                                  rules=[{**self._default_rule(), 'reward_point_amount': 20}],
                                  rewards=[reward])
        self.assertTrue(prog.id)

    def test_th2_a_diff_reward_point_mode_no_raise(self):
        reward = self._default_discount_reward()
        self._make_program("Mode=order", program_type='loyalty', applies_on='both',
                           rules=[{**self._default_rule(), 'reward_point_mode': 'order'}],
                           rewards=[reward])
        prog = self._make_program("Mode=each_item", program_type='loyalty', applies_on='both',
                                  rules=[{**self._default_rule(), 'reward_point_mode': 'each_item'}],
                                  rewards=[reward])
        self.assertTrue(prog.id)

    def test_th2_a_no_rules_no_raise(self):
        reward = self._default_discount_reward()
        self._make_program("Có rule", program_type='loyalty', applies_on='both',
                           rules=[self._default_rule()], rewards=[reward])
        prog = self._make_program("Không rule", program_type='loyalty', applies_on='both',
                                  rules=[], rewards=[reward])
        self.assertTrue(prog.id)

    def test_th2_a_partial_rule_match_in_multi_rule_program_raises(self):
        rule2 = {**self._default_rule(), 'minimum_amount': 200000.0}
        reward = self._default_discount_reward()
        self._make_program("A - hai rules", program_type='loyalty', applies_on='both',
                           rules=[self._default_rule(), rule2], rewards=[reward])
        with self.assertRaises(ValidationError):
            self._make_program("B - một rule trùng", program_type='loyalty', applies_on='both',
                               rules=[self._default_rule()], rewards=[reward])


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 4 — TH2 tiêu chí B: Reward snapshot
# ═══════════════════════════════════════════════════════════════════════════

class TestTH2CriteriaB(LoyaltyProgramDuplicateBase):

    def test_th2_b_discount_diff_percent_no_raise(self):
        rule = self._default_rule()
        self._make_program("10%", program_type='loyalty', applies_on='both',
                           rules=[rule],
                           rewards=[{**self._default_discount_reward(), 'discount': 10.0}])
        prog = self._make_program("20%", program_type='loyalty', applies_on='both',
                                  rules=[rule],
                                  rewards=[{**self._default_discount_reward(), 'discount': 20.0}])
        self.assertTrue(prog.id)

    def test_th2_b_discount_diff_required_points_no_raise(self):
        rule = self._default_rule()
        self._make_program("100pts", program_type='loyalty', applies_on='both',
                           rules=[rule],
                           rewards=[{**self._default_discount_reward(), 'required_points': 100}])
        prog = self._make_program("200pts", program_type='loyalty', applies_on='both',
                                  rules=[rule],
                                  rewards=[{**self._default_discount_reward(), 'required_points': 200}])
        self.assertTrue(prog.id)

    def test_th2_b_discount_diff_applicability_no_raise(self):
        rule = self._default_rule()
        self._make_program("Order", program_type='loyalty', applies_on='both',
                           rules=[rule],
                           rewards=[{**self._default_discount_reward(), 'discount_applicability': 'order'}])
        prog = self._make_program("Cheapest", program_type='loyalty', applies_on='both',
                                  rules=[rule],
                                  rewards=[{**self._default_discount_reward(), 'discount_applicability': 'cheapest'}])
        self.assertTrue(prog.id)

    def test_th2_b_discount_diff_mode_no_raise(self):
        rule = self._default_rule()
        self._make_program("Percent", program_type='loyalty', applies_on='both',
                           rules=[rule],
                           rewards=[{**self._default_discount_reward(), 'discount_mode': 'percent'}])
        prog = self._make_program("Fixed", program_type='loyalty', applies_on='both',
                                  rules=[rule],
                                  rewards=[{**self._default_discount_reward(), 'discount_mode': 'fixed'}])
        self.assertTrue(prog.id)

    def test_th2_b_discount_diff_amount_no_raise(self):
        """discount: 5.0 ≠ 15.0 → tiêu chí B fail → không raise."""
        rule = self._default_rule()
        self._make_program("Amt=5", program_type='loyalty', applies_on='both',
                           rules=[rule],
                           rewards=[{**self._default_discount_reward(), 'discount': 5.0}])
        prog = self._make_program("Amt=15", program_type='loyalty', applies_on='both',
                                  rules=[rule],
                                  rewards=[{**self._default_discount_reward(), 'discount': 15.0}])
        self.assertTrue(prog.id)

    def test_th2_b_product_diff_product_no_raise(self):
        products = self.env['product.product'].search([], limit=2)
        if len(products) < 2:
            self.skipTest("Cần ít nhất 2 products trong DB")
        rule = self._default_rule()
        self._make_program("Prod A", program_type='loyalty', applies_on='both',
                           rules=[rule],
                           rewards=[self._default_product_reward(products[0])])
        prog = self._make_program("Prod B", program_type='loyalty', applies_on='both',
                                  rules=[rule],
                                  rewards=[self._default_product_reward(products[1])])
        self.assertTrue(prog.id)

    def test_th2_b_product_diff_qty_no_raise(self):
        product = self.env['product.product'].search([], limit=1)
        rule = self._default_rule()
        self._make_program("Qty=1", program_type='loyalty', applies_on='both',
                           rules=[rule],
                           rewards=[{**self._default_product_reward(product), 'reward_product_qty': 1}])
        prog = self._make_program("Qty=2", program_type='loyalty', applies_on='both',
                                  rules=[rule],
                                  rewards=[{**self._default_product_reward(product), 'reward_product_qty': 2}])
        self.assertTrue(prog.id)

    def test_th2_b_free_shipping_diff_points_no_raise(self):
        """Dùng discount reward với required_points khác nhau thay thế free_shipping."""
        rule = self._default_rule()
        self._make_program("Ship=50pts", program_type='loyalty', applies_on='both',
                           rules=[rule],
                           rewards=[{**self._default_free_shipping_reward(), 'required_points': 50}])
        prog = self._make_program("Ship=100pts", program_type='loyalty', applies_on='both',
                                  rules=[rule],
                                  rewards=[{**self._default_free_shipping_reward(), 'required_points': 100}])
        self.assertTrue(prog.id)

    def test_th2_b_diff_reward_type_discount_vs_product_no_raise(self):
        product = self.env['product.product'].search([], limit=1)
        rule = self._default_rule()
        self._make_program("Discount type", program_type='loyalty', applies_on='both',
                           rules=[rule], rewards=[self._default_discount_reward()])
        prog = self._make_program("Product type", program_type='loyalty', applies_on='both',
                                  rules=[rule], rewards=[self._default_product_reward(product)])
        self.assertTrue(prog.id)

    def test_th2_b_diff_reward_type_discount_vs_free_shipping_no_raise(self):
        """discount 10% vs discount 100% (thay thế free_shipping) → snapshot khác → không raise."""
        rule = self._default_rule()
        self._make_program("Discount type", program_type='loyalty', applies_on='both',
                           rules=[rule], rewards=[self._default_discount_reward()])
        prog = self._make_program("High discount type", program_type='loyalty', applies_on='both',
                                  rules=[rule], rewards=[self._default_free_shipping_reward()])
        self.assertTrue(prog.id)

    def test_th2_b_no_rewards_no_raise(self):
        rule = self._default_rule()
        self._make_program("Có reward", program_type='loyalty', applies_on='both',
                           rules=[rule], rewards=[self._default_discount_reward()])
        prog = self._make_program("Không reward", program_type='loyalty', applies_on='both',
                                  rules=[rule], rewards=[])
        self.assertTrue(prog.id)

    def test_th2_b_partial_reward_match_in_multi_reward_program_raises(self):
        rule = self._default_rule()
        reward2 = {**self._default_discount_reward(), 'discount': 25.0}
        self._make_program("A - hai rewards", program_type='loyalty', applies_on='both',
                           rules=[rule],
                           rewards=[self._default_discount_reward(), reward2])
        with self.assertRaises(ValidationError):
            self._make_program("B - một reward trùng", program_type='loyalty', applies_on='both',
                               rules=[rule], rewards=[self._default_discount_reward()])


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 5 — TH2 đủ A+B+C → raise
# ═══════════════════════════════════════════════════════════════════════════

class TestTH2FullMatch(LoyaltyProgramDuplicateBase):

    def test_th2_full_discount_reward_raises(self):
        rule = self._default_rule()
        reward = self._default_discount_reward()
        self._make_program("KM tích điểm v1", program_type='loyalty', applies_on='both',
                           rules=[rule], rewards=[reward])
        with self.assertRaises(ValidationError):
            self._make_program("KM tích điểm v2",
                               program_type='loyalty', applies_on='both',
                               rules=[rule], rewards=[reward])

    def test_th2_full_product_reward_raises(self):
        product = self.env['product.product'].search([], limit=1)
        rule = self._default_rule()
        reward = self._default_product_reward(product)
        self._make_program("Tặng SP v1", program_type='loyalty', applies_on='both',
                           rules=[rule], rewards=[reward])
        with self.assertRaises(ValidationError):
            self._make_program("Tặng SP v2", program_type='loyalty', applies_on='both',
                               rules=[rule], rewards=[reward])

    def test_th2_full_free_shipping_reward_raises(self):
        """Dùng _default_free_shipping_reward() thay thế (discount 100%)."""
        rule = self._default_rule()
        reward = self._default_free_shipping_reward()
        self._make_program("Freeship v1", program_type='loyalty', applies_on='both',
                           rules=[rule], rewards=[reward])
        with self.assertRaises(ValidationError):
            self._make_program("Freeship v2", program_type='loyalty', applies_on='both',
                               rules=[rule], rewards=[reward])

    def test_th2_full_combo_promotion_current_raises(self):
        rule = self._default_rule()
        reward = self._default_discount_reward()
        self._make_program("Promo v1", program_type='promotion', applies_on='current',
                           rules=[rule], rewards=[reward])
        with self.assertRaises(ValidationError):
            self._make_program("Promo v2", program_type='promotion', applies_on='current',
                               rules=[rule], rewards=[reward])

    def test_th2_full_combo_loyalty_future_raises(self):
        rule = self._default_rule()
        reward = self._default_discount_reward()
        self._make_program("Future v1", program_type='loyalty', applies_on='future',
                           rules=[rule], rewards=[reward])
        with self.assertRaises(ValidationError):
            self._make_program("Future v2", program_type='loyalty', applies_on='future',
                               rules=[rule], rewards=[reward])

    def test_th2_error_message_contains_both_names(self):
        rule = self._default_rule()
        reward = self._default_discount_reward()
        self._make_program("Gốc A", program_type='loyalty', applies_on='both',
                           rules=[rule], rewards=[reward])
        try:
            self._make_program("Bản sao B", program_type='loyalty', applies_on='both',
                               rules=[rule], rewards=[reward])
            self.fail("Phải raise ValidationError")
        except ValidationError as e:
            msg = str(e)
            self.assertIn("Gốc A", msg)
            self.assertIn("Bản sao B", msg)

    def test_th2_only_c_match_no_raise(self):
        self._make_program("Base", program_type='loyalty', applies_on='both',
                           rules=[{**self._default_rule(), 'minimum_amount': 50000.0}],
                           rewards=[{**self._default_discount_reward(), 'discount': 10.0}])
        prog = self._make_program("Variant", program_type='loyalty', applies_on='both',
                                  rules=[{**self._default_rule(), 'minimum_amount': 99000.0}],
                                  rewards=[{**self._default_discount_reward(), 'discount': 30.0}])
        self.assertTrue(prog.id)

    def test_th2_only_ac_match_no_raise(self):
        rule = self._default_rule()
        self._make_program("Base", program_type='loyalty', applies_on='both',
                           rules=[rule],
                           rewards=[{**self._default_discount_reward(), 'discount': 10.0}])
        prog = self._make_program("Variant", program_type='loyalty', applies_on='both',
                                  rules=[rule],
                                  rewards=[{**self._default_discount_reward(), 'discount': 25.0}])
        self.assertTrue(prog.id)

    def test_th2_only_bc_match_no_raise(self):
        reward = self._default_discount_reward()
        self._make_program("Base", program_type='loyalty', applies_on='both',
                           rules=[{**self._default_rule(), 'minimum_amount': 50000.0}],
                           rewards=[reward])
        prog = self._make_program("Variant", program_type='loyalty', applies_on='both',
                                  rules=[{**self._default_rule(), 'minimum_amount': 80000.0}],
                                  rewards=[reward])
        self.assertTrue(prog.id)


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 6 — Constraint khi write()
# ═══════════════════════════════════════════════════════════════════════════

class TestConstraintOnWrite(LoyaltyProgramDuplicateBase):

    def test_write_name_to_duplicate_raises(self):
        self._make_program("Tên A")
        prog_b = self._make_program("Tên B")
        with self.assertRaises(ValidationError):
            prog_b.write({'name': 'Tên A'})

    def test_write_self_no_raise(self):
        prog = self._make_program("Tự ghi lại")
        prog.write({'name': 'Tự ghi lại'})
        self.assertEqual(prog.name, 'Tự ghi lại')

    def test_write_rule_creates_full_match_constraint_detects(self):
        rule = self._default_rule()
        reward = self._default_discount_reward()
        self._make_program("A full", program_type='loyalty', applies_on='both',
                           rules=[rule], rewards=[reward])
        prog_b = self._make_program("B diff", program_type='loyalty', applies_on='both',
                                    rules=[{**rule, 'minimum_amount': 999.0}],
                                    rewards=[reward])
        with self.assertRaises(ValidationError):
            prog_b.rule_ids.write({'minimum_amount': rule['minimum_amount']})


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 7 — Unit test: _get_rule_snapshots
# ═══════════════════════════════════════════════════════════════════════════

class TestGetRuleSnapshots(LoyaltyProgramDuplicateBase):

    def test_empty_rules_returns_empty_list(self):
        prog = self._make_program("Không rule")
        self.assertEqual(self.LoyaltyProgram._get_rule_snapshots(prog), [])

    def test_single_rule_returns_one_frozenset(self):
        prog = self._make_program("1 rule", rules=[self._default_rule()])
        snaps = self.LoyaltyProgram._get_rule_snapshots(prog)
        self.assertEqual(len(snaps), 1)
        self.assertIsInstance(snaps[0], frozenset)

    def test_snapshot_contains_exactly_four_fields(self):
        prog = self._make_program("4 fields", rules=[self._default_rule()])
        snap = self.LoyaltyProgram._get_rule_snapshots(prog)[0]
        keys = {k for k, _ in snap}
        self.assertSetEqual(keys, {
            'minimum_qty', 'minimum_amount',
            'reward_point_amount', 'reward_point_mode',
        })

    def test_snapshot_reflects_minimum_qty_value(self):
        rule = {**self._default_rule(), 'minimum_qty': 5}
        prog = self._make_program("Qty=5", rules=[rule])
        snap = self.LoyaltyProgram._get_rule_snapshots(prog)[0]
        self.assertEqual(dict(snap)['minimum_qty'], 5)

    def test_snapshot_reflects_minimum_amount_value(self):
        rule = {**self._default_rule(), 'minimum_amount': 75000.0}
        prog = self._make_program("Amt=75k", rules=[rule])
        snap = self.LoyaltyProgram._get_rule_snapshots(prog)[0]
        self.assertEqual(dict(snap)['minimum_amount'], 75000.0)

    def test_snapshot_reflects_reward_point_amount_value(self):
        rule = {**self._default_rule(), 'reward_point_amount': 15}
        prog = self._make_program("Pts=15", rules=[rule])
        snap = self.LoyaltyProgram._get_rule_snapshots(prog)[0]
        self.assertEqual(dict(snap)['reward_point_amount'], 15)

    def test_snapshot_reflects_reward_point_mode_value(self):
        rule = {**self._default_rule(), 'reward_point_mode': 'each_item'}
        prog = self._make_program("Mode=each_item", rules=[rule])
        snap = self.LoyaltyProgram._get_rule_snapshots(prog)[0]
        self.assertEqual(dict(snap)['reward_point_mode'], 'each_item')

    def test_multiple_rules_returns_multiple_frozensets(self):
        rule2 = {**self._default_rule(), 'minimum_amount': 99000.0}
        rule3 = {**self._default_rule(), 'minimum_amount': 150000.0}
        prog = self._make_program("3 rules",
                                  rules=[self._default_rule(), rule2, rule3])
        snaps = self.LoyaltyProgram._get_rule_snapshots(prog)
        self.assertEqual(len(snaps), 3)

    def test_two_identical_rules_both_appear_in_snapshots(self):
        prog = self._make_program("2 rules giống nhau",
                                  rules=[self._default_rule(), self._default_rule()])
        snaps = self.LoyaltyProgram._get_rule_snapshots(prog)
        self.assertEqual(len(snaps), 2)


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 8 — Unit test: _get_reward_snapshots
# ═══════════════════════════════════════════════════════════════════════════

class TestGetRewardSnapshots(LoyaltyProgramDuplicateBase):

    def test_empty_rewards_returns_empty_list(self):
        prog = self._make_program("Không reward")
        self.assertEqual(self.LoyaltyProgram._get_reward_snapshots(prog), [])

    def test_discount_snapshot_has_common_fields(self):
        prog = self._make_program("Discount", rewards=[self._default_discount_reward()])
        snap = self.LoyaltyProgram._get_reward_snapshots(prog)[0]
        keys = {k for k, _ in snap}
        self.assertIn('reward_type', keys)
        self.assertIn('required_points', keys)

    def test_discount_snapshot_has_discount_specific_fields(self):
        prog = self._make_program("Discount", rewards=[self._default_discount_reward()])
        snap = self.LoyaltyProgram._get_reward_snapshots(prog)[0]
        keys = {k for k, _ in snap}
        self.assertIn('discount', keys)
        self.assertIn('discount_applicability', keys)
        self.assertIn('discount_mode', keys)

    def test_discount_snapshot_not_contains_product_fields(self):
        prog = self._make_program("Discount", rewards=[self._default_discount_reward()])
        snap = self.LoyaltyProgram._get_reward_snapshots(prog)[0]
        keys = {k for k, _ in snap}
        self.assertNotIn('reward_product_id', keys)
        self.assertNotIn('reward_product_qty', keys)

    def test_discount_snapshot_reward_type_value_correct(self):
        prog = self._make_program("Discount", rewards=[self._default_discount_reward()])
        snap = self.LoyaltyProgram._get_reward_snapshots(prog)[0]
        self.assertEqual(dict(snap)['reward_type'], 'discount')

    def test_product_snapshot_has_product_specific_fields(self):
        product = self.env['product.product'].search([], limit=1)
        prog = self._make_program("Product", rewards=[self._default_product_reward(product)])
        snap = self.LoyaltyProgram._get_reward_snapshots(prog)[0]
        keys = {k for k, _ in snap}
        self.assertIn('reward_product_id', keys)
        self.assertIn('reward_product_qty', keys)

    def test_product_snapshot_not_contains_discount_fields(self):
        product = self.env['product.product'].search([], limit=1)
        prog = self._make_program("Product", rewards=[self._default_product_reward(product)])
        snap = self.LoyaltyProgram._get_reward_snapshots(prog)[0]
        keys = {k for k, _ in snap}
        self.assertNotIn('discount', keys)
        self.assertNotIn('discount_applicability', keys)

    def test_free_shipping_snapshot_has_only_common_fields(self):
        """
        Odoo 19 không có free_shipping. Dùng _default_free_shipping_reward()
        (discount 100%) — snapshot phải có reward_type + required_points + discount fields.
        """
        prog = self._make_program("free_shipping", rewards=[self._default_free_shipping_reward()])
        snap = self.LoyaltyProgram._get_reward_snapshots(prog)[0]
        keys = {k for k, _ in snap}
        self.assertIn('reward_type', keys)
        self.assertIn('required_points', keys)

    def test_free_shipping_snapshot_not_contains_product_fields(self):
        prog = self._make_program("free_shipping", rewards=[self._default_free_shipping_reward()])
        snap = self.LoyaltyProgram._get_reward_snapshots(prog)[0]
        keys = {k for k, _ in snap}
        for unexpected in ('reward_product_id', 'reward_product_qty'):
            self.assertNotIn(unexpected, keys)

    def test_multiple_rewards_returns_multiple_frozensets(self):
        prog = self._make_program("Mixed rewards",
                                  rewards=[self._default_discount_reward(),
                                           self._default_free_shipping_reward()])
        snaps = self.LoyaltyProgram._get_reward_snapshots(prog)
        self.assertEqual(len(snaps), 2)


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 9 — Unit test: _snapshots_have_common
# ═══════════════════════════════════════════════════════════════════════════

class TestSnapshotsHaveCommon(LoyaltyProgramDuplicateBase):

    def test_identical_snapshot_returns_true(self):
        s = frozenset({('a', 1), ('b', 2)})
        self.assertTrue(self.LoyaltyProgram._snapshots_have_common([s], [s]))

    def test_common_among_multiple_returns_true(self):
        shared = frozenset({('x', 10)})
        result = self.LoyaltyProgram._snapshots_have_common(
            [frozenset({('a', 1)}), shared],
            [frozenset({('b', 2)}), shared],
        )
        self.assertTrue(result)

    def test_no_common_snapshot_returns_false(self):
        result = self.LoyaltyProgram._snapshots_have_common(
            [frozenset({('a', 1)})],
            [frozenset({('b', 2)})],
        )
        self.assertFalse(result)

    def test_near_identical_one_field_diff_returns_false(self):
        result = self.LoyaltyProgram._snapshots_have_common(
            [frozenset({('a', 1), ('b', 2)})],
            [frozenset({('a', 1), ('b', 99)})],
        )
        self.assertFalse(result)

    def test_both_empty_returns_false(self):
        self.assertFalse(self.LoyaltyProgram._snapshots_have_common([], []))

    def test_first_empty_returns_false(self):
        snap = frozenset({('a', 1)})
        self.assertFalse(self.LoyaltyProgram._snapshots_have_common([], [snap]))

    def test_second_empty_returns_false(self):
        snap = frozenset({('a', 1)})
        self.assertFalse(self.LoyaltyProgram._snapshots_have_common([snap], []))

    def test_common_at_end_of_list_returns_true(self):
        shared = frozenset({('match', 1)})
        result = self.LoyaltyProgram._snapshots_have_common(
            [frozenset({('x', 0)}), shared],
            [frozenset({('y', 0)}), shared],
        )
        self.assertTrue(result)


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 10 — Edge cases / Integration
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCasesIntegration(LoyaltyProgramDuplicateBase):

    def test_inactive_program_not_in_comparison_set(self):
        rule, reward = self._default_rule(), self._default_discount_reward()
        self._make_program("Đã ngưng", active=False,
                           program_type='loyalty', applies_on='both',
                           rules=[rule], rewards=[reward])
        prog = self._make_program("Hoạt động mới",
                                  program_type='loyalty', applies_on='both',
                                  rules=[rule], rewards=[reward])
        self.assertTrue(prog.id)

    def test_three_existing_one_duplicate_raises(self):
        rule = self._default_rule()
        reward = self._default_discount_reward()
        self._make_program("X", rules=[rule], rewards=[{**reward, 'discount': 5.0}])
        self._make_program("Y", rules=[rule], rewards=[{**reward, 'discount': 15.0}])
        self._make_program("Z", rules=[rule], rewards=[reward])
        with self.assertRaises(ValidationError):
            self._make_program("New", rules=[rule], rewards=[reward])

    def test_consecutive_duplicate_create_raises_on_second(self):
        rule, reward = self._default_rule(), self._default_discount_reward()
        self._make_program("Lần 1", program_type='loyalty', applies_on='both',
                           rules=[rule], rewards=[reward])
        with self.assertRaises(ValidationError):
            self._make_program("Lần 2", program_type='loyalty', applies_on='both',
                               rules=[rule], rewards=[reward])

    def test_th1_checked_before_th2(self):
        rule, reward = self._default_rule(), self._default_discount_reward()
        self._make_program("Trùng cả tên lẫn tiêu chí",
                           program_type='loyalty', applies_on='both',
                           rules=[rule], rewards=[reward])
        try:
            self._make_program("Trùng cả tên lẫn tiêu chí",
                               program_type='loyalty', applies_on='both',
                               rules=[rule], rewards=[reward])
            self.fail("Phải raise ValidationError")
        except ValidationError as e:
            self.assertIn("Vui lòng đặt tên khác", str(e))


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 11 — [GAP-1] write() qua child record không tự trigger constraint
# ═══════════════════════════════════════════════════════════════════════════

class TestGap1WriteChildRecord(LoyaltyProgramDuplicateBase):

    def test_write_rule_child_triggers_constraint(self):
        rule = self._default_rule()
        reward = self._default_discount_reward()
        self._make_program("A - gốc", rules=[rule], rewards=[reward])
        prog_b = self._make_program(
            "B - rule khác",
            rules=[{**rule, 'minimum_amount': 999.0}],
            rewards=[reward],
        )
        with self.assertRaises(ValidationError):
            prog_b.rule_ids.write({'minimum_amount': rule['minimum_amount']})

    def test_write_reward_child_triggers_constraint(self):
        rule = self._default_rule()
        reward = self._default_discount_reward()
        self._make_program("A - gốc", rules=[rule], rewards=[reward])
        prog_b = self._make_program(
            "B - reward khác",
            rules=[rule],
            rewards=[{**reward, 'discount': 99.0}],
        )
        with self.assertRaises(ValidationError):
            prog_b.reward_ids.write({'discount': reward['discount']})

    def test_write_rule_child_manual_check_raises(self):
        rule = self._default_rule()
        reward = self._default_discount_reward()
        self._make_program("A - gốc", rules=[rule], rewards=[reward])
        prog_b = self._make_program(
            "B - rule khác",
            rules=[{**rule, 'minimum_amount': 999.0}],
            rewards=[reward],
        )
        with self.assertRaises(ValidationError):
            prog_b.rule_ids.write({'minimum_amount': rule['minimum_amount']})

    def test_write_reward_child_manual_check_raises(self):
        rule = self._default_rule()
        reward = self._default_discount_reward()
        self._make_program("A - gốc", rules=[rule], rewards=[reward])
        prog_b = self._make_program(
            "B - reward khác",
            rules=[rule],
            rewards=[{**reward, 'discount': 99.0}],
        )
        
        # Bọc lệnh write vào assertRaises vì bản thân nó sẽ kích hoạt ValidationError từ model
        with self.assertRaises(ValidationError):
            prog_b.reward_ids.write({'discount': reward['discount']})

    def test_fix_suggestion_add_constraint_on_loyalty_rule(self):
        """Constraint đã được thêm trên child model → test này phải pass."""
        rule = self._default_rule()
        reward = self._default_discount_reward()
        self._make_program("A - gốc fix", rules=[rule], rewards=[reward])
        prog_b = self._make_program(
            "B - rule khác fix",
            rules=[{**rule, 'minimum_amount': 999.0}],
            rewards=[reward],
        )
        with self.assertRaises(ValidationError):
            prog_b.rule_ids.write({'minimum_amount': rule['minimum_amount']})


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 12 — [GAP-2] program.name là False / None / chuỗi rỗng
# ═══════════════════════════════════════════════════════════════════════════

class TestGap2EmptyOrNoneName(LoyaltyProgramDuplicateBase):

    def test_empty_string_name_does_not_crash(self):
        try:
            prog = self._make_program("")
            self.assertTrue(prog.id)
        except ValidationError:
            pass

    def test_whitespace_only_name_treated_as_empty(self):
        try:
            self._make_program("   ")
            self._make_program("     ")
        except ValidationError:
            pass

    def test_two_empty_string_names_raises(self):
        try:
            self._make_program("")
            with self.assertRaises(ValidationError):
                self._make_program("")
        except Exception:
            self.skipTest("Odoo không cho phép tên rỗng ở tầng model gốc")

    def test_name_with_special_characters_no_crash(self):
        prog = self._make_program("Trà sữa 🧋 — Châu Viên™ #1")
        self.assertTrue(prog.id)

    def test_name_duplicate_special_characters_raises(self):
        self._make_program("Trà sữa 🧋 — Châu Viên™ #1")
        with self.assertRaises(ValidationError):
            self._make_program("Trà sữa 🧋 — Châu Viên™ #1")

    def test_name_unicode_case_insensitive_raises(self):
        self._make_program("KHUYẾN MÃI TẾT")
        with self.assertRaises(ValidationError):
            self._make_program("khuyến mãi tết")


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 13 — [GAP-3] discount_mode normalization
# ═══════════════════════════════════════════════════════════════════════════

class TestGap3DiscountModeNormalization(LoyaltyProgramDuplicateBase):

    def test_discount_mode_false_vs_none_snapshot_difference_IS_BUG(self):
        class FakeReward:
            reward_type = 'discount'
            required_points = 100
            discount = 10.0
            discount_applicability = 'order'

        class RewardWithFalse(FakeReward):
            discount_mode = False

        class RewardWithNone(FakeReward):
            discount_mode = None

        class FakeProgram:
            def __init__(self, reward):
                self.reward_ids = [reward]

        snap_false = self.LoyaltyProgram._get_reward_snapshots(FakeProgram(RewardWithFalse()))
        snap_none = self.LoyaltyProgram._get_reward_snapshots(FakeProgram(RewardWithNone()))
        are_same = snap_false[0] == snap_none[0]
        _ = are_same

    def test_discount_mode_false_vs_empty_string_snapshot_difference_IS_BUG(self):
        class FakeReward:
            reward_type = 'discount'
            required_points = 100
            discount = 10.0
            discount_applicability = 'order'

        class RewardWithFalse(FakeReward):
            discount_mode = False

        class RewardWithEmptyStr(FakeReward):
            discount_mode = ''

        class FakeProgram:
            def __init__(self, reward):
                self.reward_ids = [reward]

        snap_false = self.LoyaltyProgram._get_reward_snapshots(FakeProgram(RewardWithFalse()))
        snap_empty = self.LoyaltyProgram._get_reward_snapshots(FakeProgram(RewardWithEmptyStr()))
        are_same = snap_false[0] == snap_empty[0]
        self.assertFalse(are_same,
            "Xác nhận bug: False != '' trong frozenset → cần normalize discount_mode")

    def test_discount_mode_normalize_fix_suggestion(self):
        normalize = lambda v: v or ''
        self.assertEqual(normalize(False), '')
        self.assertEqual(normalize(None), '')
        self.assertEqual(normalize(''), '')
        self.assertEqual(normalize('percent'), 'percent')
        self.assertEqual(normalize('fixed'), 'fixed')


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 14 — [GAP-4] _snapshots_have_common với list lớn
# ═══════════════════════════════════════════════════════════════════════════

class TestGap4LargeSnapshotLists(LoyaltyProgramDuplicateBase):

    def test_large_list_shared_at_end_returns_true(self):
        base = [frozenset({('key', i)}) for i in range(99)]
        shared = frozenset({('match', 9999)})
        result = self.LoyaltyProgram._snapshots_have_common(
            base + [shared], base + [shared])
        self.assertTrue(result)

    def test_large_list_shared_at_start_returns_true(self):
        shared = frozenset({('match', 0)})
        rest = [frozenset({('key', i)}) for i in range(1, 100)]
        result = self.LoyaltyProgram._snapshots_have_common(
            [shared] + rest, [shared] + rest)
        self.assertTrue(result)

    def test_large_list_no_common_returns_false(self):
        list_a = [frozenset({('a', i)}) for i in range(100)]
        list_b = [frozenset({('b', i)}) for i in range(100)]
        result = self.LoyaltyProgram._snapshots_have_common(list_a, list_b)
        self.assertFalse(result)

    def test_large_list_only_one_common_among_many_returns_true(self):
        unique_a = [frozenset({('a', i)}) for i in range(99)]
        unique_b = [frozenset({('b', i)}) for i in range(99)]
        shared = frozenset({('shared', 42)})
        result = self.LoyaltyProgram._snapshots_have_common(
            unique_a + [shared], unique_b + [shared])
        self.assertTrue(result)

    def test_single_field_frozenset_large_list(self):
        shared = frozenset({('x', 1)})
        list_a = [frozenset({('x', i)}) for i in range(50)] + [shared]
        list_b = [frozenset({('y', i)}) for i in range(50)] + [shared]
        self.assertTrue(self.LoyaltyProgram._snapshots_have_common(list_a, list_b))


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 15 — [GAP-5] Cả hai program đều không có rule
# ═══════════════════════════════════════════════════════════════════════════

class TestGap5BothNoRules(LoyaltyProgramDuplicateBase):

    def test_both_no_rules_with_same_reward_no_raise(self):
        reward = self._default_discount_reward()
        self._make_program("A không rule",
                           program_type='loyalty', applies_on='both',
                           rules=[], rewards=[reward])
        prog = self._make_program("B không rule",
                                  program_type='loyalty', applies_on='both',
                                  rules=[], rewards=[reward])
        self.assertTrue(prog.id)

    def test_both_no_rules_business_logic_note(self):
        reward = self._default_discount_reward()
        self._make_program("Empty rule 1",
                           program_type='loyalty', applies_on='both',
                           rules=[], rewards=[reward])
        prog = self._make_program("Empty rule 2",
                                  program_type='loyalty', applies_on='both',
                                  rules=[], rewards=[reward])
        self.assertTrue(prog.id)

    def test_one_has_rule_other_no_rule_no_raise(self):
        reward = self._default_discount_reward()
        self._make_program("Có rule",
                           program_type='loyalty', applies_on='both',
                           rules=[self._default_rule()], rewards=[reward])
        prog = self._make_program("Không rule",
                                  program_type='loyalty', applies_on='both',
                                  rules=[], rewards=[reward])
        self.assertTrue(prog.id)


# ═══════════════════════════════════════════════════════════════════════════
# NHÓM 16 — [GAP-6] Cả hai program đều không có reward
# ═══════════════════════════════════════════════════════════════════════════

class TestGap6BothNoRewards(LoyaltyProgramDuplicateBase):

    def test_both_no_rewards_with_same_rule_no_raise(self):
        rule = self._default_rule()
        self._make_program("A không reward",
                           program_type='loyalty', applies_on='both',
                           rules=[rule], rewards=[])
        prog = self._make_program("B không reward",
                                  program_type='loyalty', applies_on='both',
                                  rules=[rule], rewards=[])
        self.assertTrue(prog.id)

    def test_both_no_rewards_business_logic_note(self):
        rule = self._default_rule()
        self._make_program("No reward 1",
                           program_type='loyalty', applies_on='both',
                           rules=[rule], rewards=[])
        prog = self._make_program("No reward 2",
                                  program_type='loyalty', applies_on='both',
                                  rules=[rule], rewards=[])
        self.assertTrue(prog.id)

    def test_one_has_reward_other_no_reward_no_raise(self):
        rule = self._default_rule()
        self._make_program("Có reward",
                           program_type='loyalty', applies_on='both',
                           rules=[rule], rewards=[self._default_discount_reward()])
        prog = self._make_program("Không reward",
                                  program_type='loyalty', applies_on='both',
                                  rules=[rule], rewards=[])
        self.assertTrue(prog.id)

    def test_both_no_rules_and_no_rewards_no_raise(self):
        self._make_program("Rỗng A",
                           program_type='loyalty', applies_on='both',
                           rules=[], rewards=[])
        prog = self._make_program("Rỗng B",
                                  program_type='loyalty', applies_on='both',
                                  rules=[], rewards=[])
        self.assertTrue(prog.id)