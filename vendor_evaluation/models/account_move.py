# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        """ Kế toán xác nhận hóa đơn -> Chạy đối chiếu số lượng đặt """
        for move in self:
            if move.move_type == 'in_invoice':
                for line in move.invoice_line_ids:
                    purchase_line = line.purchase_line_id
                    # Rẽ nhánh: Nếu số lượng trên hóa đơn không khớp với số lượng đặt mua trên PO -> Chặn báo lỗi
                    if purchase_line and line.quantity != purchase_line.product_qty:
                        raise UserError(_("Sai lệch dữ liệu đối chiếu! Sản phẩm '%s' có số lượng trên hóa đơn (%s) không khớp với PO gốc (%s).") % (line.product_id.name, line.quantity, purchase_line.product_qty))
        return super(AccountMove, self).action_post()