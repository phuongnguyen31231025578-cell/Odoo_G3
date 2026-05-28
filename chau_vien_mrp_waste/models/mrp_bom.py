from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    x_waste_rate = fields.Float(
        string="Waste Rate (%)",
        default=0.0,
        help="Expected material waste rate for this Bill of Materials.",
    )

    @api.constrains("x_waste_rate")
    def _check_x_waste_rate(self):
        for bom in self:
            if bom.x_waste_rate < 0:
                raise ValidationError("Waste Rate (%) không được nhỏ hơn 0.")
            if bom.x_waste_rate > 100:
                raise ValidationError("Waste Rate (%) không được lớn hơn 100.")