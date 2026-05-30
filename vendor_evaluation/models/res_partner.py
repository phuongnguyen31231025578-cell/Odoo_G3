# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Cờ đánh dấu NCC đã đủ điều kiện chấm điểm (đã có ít nhất 1 PO xác nhận).
    # NCC mới (chưa có PO) -> KHÔNG áp dụng tính điểm.
    x_is_evaluated = fields.Boolean(
        string='Đã đánh giá',
        default=False,
        copy=False,
        help='True khi NCC đã có ít nhất 1 đơn mua hàng (PO) xác nhận. '
             'NCC mới chưa có PO sẽ không được chấm điểm.',
    )

    # (1) CHẤT LƯỢNG - tối đa 45đ - QUẢN LÝ NHẬP TAY
    x_quality_score = fields.Float(
        string='Điểm chất lượng (≤ 45)',
        default=0.0,
        help='Quản lý nhập tay: đánh giá chất lượng hàng hóa của NCC (0 - 45 điểm).',
    )

    # (2) GIAO HÀNG ĐÚNG HẠN - tối đa 25đ - TỰ ĐỘNG TÍNH
    x_delivery_score = fields.Float(
        string='Điểm giao hàng (≤ 25)',
        default=0.0,
        readonly=True,
        copy=False,
        help='Tự động tính từ tỷ lệ phiếu nhập kho ĐÚNG HẠN (không thuộc nhóm Late) của NCC.',
    )

    # (3) GIÁ CẢ - tối đa 30đ - TỰ ĐỘNG TÍNH
    x_price_score = fields.Float(
        string='Điểm giá cả (≤ 30)',
        default=0.0,
        readonly=True,
        copy=False,
        help='Tự động tính bằng cách so sánh giá chào của NCC với các NCC khác cùng bán sản phẩm.',
    )

    # TỔNG ĐIỂM = Chất lượng + Giao hàng + Giá (tự cộng)
    x_vendor_rating = fields.Float(
        string='Điểm uy tín tổng (/100)',
        compute='_compute_vendor_rating',
        store=True,
        copy=False,
        help='Tổng = Chất lượng (nhập tay) + Giao hàng + Giá (tự động). '
             'NCC mới chưa đánh giá sẽ để 0.',
    )

    @api.constrains('x_quality_score')
    def _check_quality_score(self):
        for partner in self:
            if partner.x_quality_score < 0 or partner.x_quality_score > 45:
                raise ValidationError(_('Điểm chất lượng phải nằm trong khoảng 0 đến 45.'))

    @api.depends('x_quality_score', 'x_delivery_score', 'x_price_score', 'x_is_evaluated')
    def _compute_vendor_rating(self):
        for partner in self:
            if partner.x_is_evaluated:
                partner.x_vendor_rating = (
                    (partner.x_quality_score or 0.0)
                    + (partner.x_delivery_score or 0.0)
                    + (partner.x_price_score or 0.0)
                )
            else:
                partner.x_vendor_rating = 0.0

    # ──────────────────────────────────────────────────────────────────────
    #  TÍNH ĐIỂM TỰ ĐỘNG
    # ──────────────────────────────────────────────────────────────────────
    def _compute_delivery_score_value(self):
        """ Điểm giao hàng (≤25) = 25 * tỷ lệ phiếu nhập kho đúng hạn.
            Một phiếu bị coi là TRỄ (Late) khi ngày hoàn tất > ngày hẹn giao. """
        self.ensure_one()
        pickings = self.env['stock.picking'].search([
            ('picking_type_code', '=', 'incoming'),
            ('state', '=', 'done'),
            ('purchase_id.partner_id', '=', self.id),
        ])
        if not pickings:
            # Đã có PO nhưng chưa nhận hàng -> chưa có phiếu trễ -> tạm cho tối đa
            return 25.0
        on_time = 0
        for pk in pickings:
            scheduled = pk.scheduled_date
            actual = pk.date_done or scheduled
            # Đúng hạn nếu không có ngày hẹn, hoặc hoàn tất <= ngày hẹn
            if not scheduled or (actual and actual <= scheduled):
                on_time += 1
        rate = on_time / len(pickings)
        return round(25.0 * rate, 2)

    def _compute_price_score_value(self):
        """ Điểm giá cả (≤30) = 30 * trung bình tỷ lệ (giá thấp nhất / giá của NCC)
            trên từng sản phẩm mà NCC chào bán. NCC chào giá rẻ nhất -> đạt tối đa. """
        self.ensure_one()
        seller_infos = self.env['product.supplierinfo'].search([('partner_id', '=', self.id)])
        ratios = []
        for si in seller_infos:
            if si.price <= 0:
                continue
            competitors = self.env['product.supplierinfo'].search([
                ('product_tmpl_id', '=', si.product_tmpl_id.id),
                ('price', '>', 0),
            ])
            prices = competitors.mapped('price')
            if not prices:
                continue
            min_price = min(prices)
            ratios.append(min_price / si.price)
        if not ratios:
            # Không có bảng giá để so sánh -> tạm cho tối đa
            return 30.0
        avg_ratio = sum(ratios) / len(ratios)
        return round(min(30.0, 30.0 * avg_ratio), 2)

    def _recompute_evaluation(self):
        """ Tính lại điểm TỰ ĐỘNG (Giao hàng + Giá) cho từng NCC.
            Điểm Chất lượng do quản lý nhập tay nên không đụng tới. """
        PurchaseOrder = self.env['purchase.order']
        for partner in self:
            if partner.supplier_rank <= 0:
                continue
            po_count = PurchaseOrder.search_count([
                ('partner_id', '=', partner.id),
                ('state', 'in', ('purchase', 'done')),
            ])
            if po_count == 0:
                # NCC mới chưa có PO -> không chấm điểm
                partner.write({
                    'x_is_evaluated': False,
                    'x_delivery_score': 0.0,
                    'x_price_score': 0.0,
                })
                continue
            partner.write({
                'x_is_evaluated': True,
                'x_delivery_score': partner._compute_delivery_score_value(),
                'x_price_score': partner._compute_price_score_value(),
            })

    def action_recompute_evaluation(self):
        """ Nút bấm tính lại điểm thủ công trên form NCC. """
        self._recompute_evaluation()
        return True

    @api.model
    def _cron_recompute_vendor_evaluation(self):
        """ Tác vụ định kỳ: tính lại điểm cho toàn bộ NCC. """
        vendors = self.search([('supplier_rank', '>', 0)])
        vendors._recompute_evaluation()
        return True