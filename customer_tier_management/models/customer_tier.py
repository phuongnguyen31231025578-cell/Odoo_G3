from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CustomerTier(models.Model):
    _name = 'customer.tier'
    _description = 'Customer Tier'
    _order = 'min_points asc, sequence asc, id asc'

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Integer(default=10)
    min_points = fields.Float(required=True, tracking=True)
    auto_discount_percent = fields.Float(default=0.0)
    color = fields.Integer()
    active = fields.Boolean(default=True)

    @api.constrains('min_points')
    def _check_min_points(self):
        for rec in self:
            if rec.min_points < 0:
                raise ValidationError(_('Minimum points must be greater than or equal to 0.'))

            dup = self.search([
                ('id', '!=', rec.id),
                ('min_points', '=', rec.min_points),
            ], limit=1)
            if dup:
                raise ValidationError(_('Minimum points must be unique.'))

            if rec.min_points == 0:
                other_zero = self.search_count([
                    ('id', '!=', rec.id),
                    ('min_points', '=', 0.0),
                ])
                if other_zero:
                    raise ValidationError(_('Only one tier with min_points = 0 is allowed.'))

    @api.constrains('active')
    def _check_active_default_tier(self):
        for rec in self:
            if rec.active is False and rec.min_points == 0:
                raise ValidationError(_('Default tier (min_points = 0) cannot be archived.'))

    @api.model
    def _get_tier_by_points(self, points):
        pts = points or 0.0
        tier = self.search([('active', '=', True), ('min_points', '<=', pts)], order='min_points desc', limit=1)
        if not tier:
            tier = self.search([('active', '=', True)], order='min_points asc', limit=1)
        return tier

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    def write(self, vals):
        return super().write(vals)
