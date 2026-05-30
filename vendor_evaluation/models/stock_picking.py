# -*- coding: utf-8 -*-
from odoo import models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """ Thủ kho xác nhận nhập kho -> tự động tính lại điểm đánh giá NCC
            (điểm Giao hàng đúng hạn + Giá cả). """
        res = super(StockPicking, self).button_validate()

        vendors = self.env['res.partner']
        for picking in self:
            if (picking.picking_type_code == 'incoming'
                    and picking.state == 'done'
                    and picking.purchase_id
                    and picking.purchase_id.partner_id):
                vendors |= picking.purchase_id.partner_id

        if vendors:
            vendors._recompute_evaluation()
            for picking in self:
                po = picking.purchase_id
                if po and po.partner_id in vendors:
                    po.message_post(body=_(
                        "Hệ thống Odoo 19: Đã cập nhật điểm đánh giá NCC sau khi nhập kho. "
                        "Giao hàng: %(d)s/25 · Giá: %(p)s/30 · Tổng uy tín: %(t)s/100.",
                        d=po.partner_id.x_delivery_score,
                        p=po.partner_id.x_price_score,
                        t=po.partner_id.x_vendor_rating,
                    ))
        return res