# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import ValidationError


class LoyaltyProgram(models.Model):
    _inherit = 'loyalty.program'

    @api.constrains(
        'name', 'program_type', 'applies_on',
        'rule_ids', 'reward_ids',
    )
    def _check_duplicate_program(self):
        for program in self:
            self._validate_no_duplicate(program)

    def _validate_no_duplicate(self, program):
        """
        Chặn lưu nếu thỏa mãn một trong hai trường hợp:

        TH1: Trùng tên (bất kể tiêu chí A/B/C có giống hay không)
        TH2: Không trùng tên nhưng trùng CẢ 3 tiêu chí:
             A. Rule  : minimum_qty + minimum_amount + reward_point_amount + reward_point_mode
             B. Reward: Quét tất cả các loại (Discount, Product, Shipping) dựa trên các trường đặc trưng
             C. Program: program_type + applies_on
        """
        # Tập các chương trình khác đang active (exclude chính nó khi edit)
        other_programs = self.env['loyalty.program'].search([
            ('id', '!=', program.id),
            ('active', '=', True),
        ])

        # ── TH1: Trùng tên ──────────────────────────────────────────────────
        duplicate_name = other_programs.filtered(
            lambda p: p.name and p.name.strip().lower() == (program.name or '').strip().lower()
        )
        if duplicate_name:
            conflicting = duplicate_name[0]
            raise ValidationError(_(
                "Chương trình khuyến mãi bị trùng lặp!\n\n"
                "Tên \"%(name)s\" đã tồn tại trong chương trình: \"%(conflict)s\" (ID: %(cid)s).\n\n"
                "Vui lòng đặt tên khác để phân biệt các chương trình.",
                name=program.name,
                conflict=conflicting.name,
                cid=conflicting.id,
            ))

        # ── TH2: Không trùng tên, kiểm tra 3 tiêu chí ──────────────────────
        # Tiêu chí C — Program-level filter (thu hẹp tập so sánh)
        candidates_c = other_programs.filtered(
            lambda p:
                p.program_type == program.program_type and
                p.applies_on == program.applies_on
        )
        if not candidates_c:
            return  # Không còn ứng viên nào → không trùng

        # Tiêu chí A — Rule snapshot của chương trình đang lưu
        program_rule_snapshots = self._get_rule_snapshots(program)

        # Tiêu chí B — Reward snapshot của chương trình đang lưu
        program_reward_snapshots = self._get_reward_snapshots(program)

        for candidate in candidates_c:
            candidate_rule_snapshots = self._get_rule_snapshots(candidate)
            candidate_reward_snapshots = self._get_reward_snapshots(candidate)

            # Tiêu chí A: có ít nhất 1 rule của program khớp hoàn toàn với 1 rule của candidate
            match_a = self._snapshots_have_common(
                program_rule_snapshots, candidate_rule_snapshots
            )
            if not match_a:
                continue

            # Tiêu chí B: có ít nhất 1 reward của program khớp hoàn toàn với 1 reward của candidate
            match_b = self._snapshots_have_common(
                program_reward_snapshots, candidate_reward_snapshots
            )
            if not match_b:
                continue

            # Cả 3 tiêu chí A + B + C đều khớp → chặn
            raise ValidationError(_(
                "Chương trình khuyến mãi bị trùng lặp!\n\n"
                "Chương trình \"%(name)s\" trùng toàn bộ 3 tiêu chí "
                "(Loại chương trình, Quy tắc tích điểm, Phan thưởng) "
                "với chương trình: \"%(conflict)s\" (ID: %(cid)s).\n\n"
                "Vui lòng điều chỉnh ít nhất một tiêu chí để phân biệt.",
                name=program.name,
                conflict=candidate.name,
                cid=candidate.id,
            ))

    # ── Helpers ─────────────────────────────────────────────────────────────

    @api.model
    def _get_rule_snapshots(self, program):
        """
        Trả về list các frozenset đại diện cho từng rule của chương trình.
        Tiêu chí A: minimum_qty + minimum_amount + reward_point_amount + reward_point_mode
        """
        snapshots = []
        for rule in program.rule_ids:
            snapshot = frozenset({
                ('minimum_qty', rule.minimum_qty),
                ('minimum_amount', rule.minimum_amount),
                ('reward_point_amount', rule.reward_point_amount),
                ('reward_point_mode', rule.reward_point_mode),
            })
            snapshots.append(snapshot)
        return snapshots

    @api.model
    def _get_reward_snapshots(self, program):
        """
        Trả về list các frozenset đại diện cho từng reward của chương trình.
        Hỗ trợ đầy đủ các loại: discount, product (tặng sản phẩm/voucher), shipping (miễn phí vận chuyển)
        """
        snapshots = []
        for reward in program.reward_ids:
            # 1. Các tiêu chí chung mà loại reward nào cũng có
            reward_fields = [
                ('reward_type', reward.reward_type),
                ('required_points', reward.required_points),
            ]

            # 2. Phân tách chi tiết theo từng loại Reward để bốc đúng trường dữ liệu
            if reward.reward_type == 'discount':
                discount_val = getattr(reward, 'discount', getattr(reward, 'discount_percentage', 0.0))
                reward_fields.extend([
                    ('discount', discount_val),
                    ('discount_amount', getattr(reward, 'discount_amount', 0.0)),
                    ('discount_applicability', reward.discount_applicability),
                    ('discount_mode', getattr(reward, 'discount_mode', False)),
                ])
                
            elif reward.reward_type == 'product':
                product_id = reward.reward_product_id.id if reward.reward_product_id else False
                reward_fields.extend([
                    ('reward_product_id', product_id),
                    ('reward_product_qty', getattr(reward, 'reward_product_qty', 1)),
                ])
                
            elif reward.reward_type == 'shipping':
                pass

            snapshot = frozenset(reward_fields)
            snapshots.append(snapshot)
        return snapshots

    @api.model
    def _snapshots_have_common(self, snapshots_a, snapshots_b):
        """Kiểm tra có ít nhất 1 snapshot chung giữa 2 tập không."""
        set_b = set(snapshots_b)
        return any(s in set_b for s in snapshots_a)