# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """ Thủ kho bấm nút Xác nhận nhập kho -> Hệ thống tự đối chiếu thời gian và tính điểm tiến độ """
        res = super(StockPicking, self).button_validate()
        for picking in self:
            if picking.picking_type_code == 'incoming' and picking.state == 'done' and picking.purchase_id:
                po = picking.purchase_id
                vendor = po.partner_id
                
                # Tính điểm tiến độ giao hàng đúng hạn (Tối đa 25 điểm)
                scheduled_date = po.date_planned
                actual_date = picking.date_done or fields.Datetime.now()

                # Không có ngày hẹn (đơn nhập tay) hoặc giao đúng/sớm hạn -> 25 điểm tối đa
                if not scheduled_date or actual_date <= scheduled_date:
                    delivery_score = 25.0
                else:
                    delay_days = (actual_date - scheduled_date).days
                    delivery_score = max(0.0, 25.0 - (delay_days * 2.0)) # Cứ trễ 1 ngày bị trừ phạt 2 điểm
                
                vendor.x_delivery_score = delivery_score
                # Tính tổng điểm = Chất lượng (45) + Giá (30) + Tiến độ vừa chấm (Tối đa 25)
                total_rating = (vendor.x_quality_score or 45.0) + (vendor.x_price_score or 30.0) + delivery_score
                vendor.write({'x_vendor_rating': round(total_rating, 2)})
                
                po.message_post(body=_("Hệ thống Odoo 19: Đã đối chiếu tiến độ nhập kho. Điểm tiến độ: %s/25. Tổng uy tín NCC: %s/100.") % (delivery_score, round(total_rating, 2)))
        return res