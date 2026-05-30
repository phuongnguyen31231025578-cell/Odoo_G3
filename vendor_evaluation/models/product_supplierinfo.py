# -*- coding: utf-8 -*-
from odoo import models, api


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    def _affected_vendors(self):
        """ Các NCC (đã đánh giá) cùng bán những sản phẩm liên quan -> cần tính lại điểm giá. """
        tmpls = self.mapped('product_tmpl_id')
        if not tmpls:
            return self.env['res.partner']
        infos = self.env['product.supplierinfo'].search([('product_tmpl_id', 'in', tmpls.ids)])
        return infos.mapped('partner_id').filtered(lambda v: v.x_is_evaluated)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._affected_vendors()._recompute_evaluation()
        return records

    def write(self, vals):
        # Gom NCC bị ảnh hưởng TRƯỚC và SAU khi đổi giá/sản phẩm/đối tác
        vendors = self.env['res.partner']
        trigger = any(f in vals for f in ('price', 'partner_id', 'product_tmpl_id', 'min_qty'))
        if trigger:
            vendors |= self._affected_vendors()
        res = super().write(vals)
        if trigger:
            vendors |= self._affected_vendors()
            vendors._recompute_evaluation()
        return res

    def unlink(self):
        vendors = self._affected_vendors()
        res = super().unlink()
        vendors._recompute_evaluation()
        return res