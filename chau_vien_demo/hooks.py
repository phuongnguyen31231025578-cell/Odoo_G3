# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from odoo import fields

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """ Sau khi cài: seed một số PO + phiếu nhập kho (đúng/trễ hạn) để chức năng
        vendor_evaluation có dữ liệu chấm điểm THẬT ngay (điểm Giao hàng + Giá).
        Bọc try/except để KHÔNG bao giờ làm hỏng quá trình cài đặt. """
    try:
        _seed_vendor_evaluation(env)
    except Exception as exc:  # noqa: BLE001
        _logger.warning("chau_vien_demo: bỏ qua seed đánh giá NCC (%s)", exc)


def _seed_vendor_evaluation(env):
    PurchaseOrder = env['purchase.order']

    # (vendor xmlid, product xmlid, qty/đơn, [số ngày trễ cho từng đơn nhập])
    #   0 = đúng hạn, >0 = trễ ngần ấy ngày
    scenarios = [
        ('chau_vien_demo.supplier_la_tra', 'chau_vien_demo.prod_la_luc_tra', 10, [0, 0, 0]),   # 3/3 đúng hạn -> 25/25
        ('chau_vien_demo.supplier_duong',  'chau_vien_demo.prod_duong',      50, [0, 0, 3]),   # 2/3 đúng hạn -> ~16.7/25
        ('chau_vien_demo.supplier_bao_bi', 'chau_vien_demo.prod_ly_m',       500, [0, 5]),     # 1/2 đúng hạn -> 12.5/25
    ]

    base = fields.Datetime.now() - timedelta(days=15)

    for vendor_xml, product_xml, qty, late_days_list in scenarios:
        vendor = env.ref(vendor_xml, raise_if_not_found=False)
        product = env.ref(product_xml, raise_if_not_found=False)
        if not vendor or not product:
            continue
        # Idempotent: nếu NCC đã có PO thì bỏ qua (tránh seed trùng khi cài lại)
        if PurchaseOrder.search_count([('partner_id', '=', vendor.id)]):
            continue

        for idx, days_late in enumerate(late_days_list):
            scheduled = base + timedelta(days=idx)          # các đơn cách nhau 1 ngày
            done = scheduled + timedelta(days=days_late)    # trễ "days_late" ngày

            po = PurchaseOrder.create({
                'partner_id': vendor.id,
                'date_planned': scheduled,
                'order_line': [(0, 0, {
                    'product_id': product.id,
                    'name': product.name,
                    'product_qty': qty,
                    'price_unit': product.standard_price or 1.0,
                    'date_planned': scheduled,
                })],
            })
            po.button_confirm()

            for picking in po.picking_ids:
                for move in picking.move_ids:
                    move.quantity = move.product_uom_qty
                    move.picked = True
                picking.button_validate()
                # Ghi đè ngày để mô phỏng đúng/trễ hạn đúng kịch bản
                picking.write({'scheduled_date': scheduled, 'date_done': done})

        # Tính lại điểm sau khi đã có đủ lịch sử nhập kho (ngày đã mô phỏng)
        vendor._recompute_evaluation()
        _logger.info(
            "chau_vien_demo: %s -> Giao hàng %.1f/25 | Giá %.1f/30 | Tổng %.1f/100",
            vendor.name, vendor.x_delivery_score, vendor.x_price_score, vendor.x_vendor_rating,
        )