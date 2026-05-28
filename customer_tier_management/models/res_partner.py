import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_tier_id = fields.Many2one('customer.tier', string='Current Tier', tracking=True)
    x_last_tier_update = fields.Datetime(string='Last Tier Update', readonly=True)

    x_total_loyalty_points = fields.Float(
        string='Total Loyalty Points',
        compute='_compute_total_loyalty_points',
        store=False,
        readonly=True,
    )

    x_tier_history_count = fields.Integer(compute='_compute_tier_history_count')

    def _compute_total_loyalty_points(self):
        has_loyalty = 'loyalty.card' in self.env
        if not has_loyalty:
            _logger.warning('Loyalty module is not installed; x_total_loyalty_points will always be 0 and no realtime update will occur.')

        for partner in self:
            if not has_loyalty:
                partner.x_total_loyalty_points = 0.0
                continue
            cards = self.env['loyalty.card'].search([('partner_id', '=', partner.id)])
            partner.x_total_loyalty_points = sum((c.points or 0.0) for c in cards)

    def _compute_tier_history_count(self):
        history_model = self.env['customer.tier.history']
        grouped = history_model.read_group([('partner_id', 'in', self.ids)], ['partner_id'], ['partner_id'])
        count_map = {g['partner_id'][0]: g['partner_id_count'] for g in grouped}
        for partner in self:
            partner.x_tier_history_count = count_map.get(partner.id, 0)

    def action_view_tier_history(self):
        self.ensure_one()
        return {
            'name': _('Tier History'),
            'type': 'ir.actions.act_window',
            'res_model': 'customer.tier.history',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def _update_customer_tier(self, reason=''):
        tier_model = self.env['customer.tier']
        history_model = self.env['customer.tier.history']

        for partner in self:
            points = partner.x_total_loyalty_points or 0.0
            new_tier = tier_model._get_tier_by_points(points)
            if not new_tier:
                continue

            old_tier = partner.x_tier_id
            if old_tier and old_tier.id == new_tier.id:
                continue
            if not old_tier and not new_tier:
                continue

            history_model.create({
                'partner_id': partner.id,
                'old_tier_id': old_tier.id if old_tier else False,
                'new_tier_id': new_tier.id,
                'change_date': fields.Datetime.now(),
                'reason': reason or _('Batch update'),
                'triggered_by_user_id': self.env.user.id if self.env.user else False,
            })

            partner.write({
                'x_tier_id': new_tier.id,
                'x_last_tier_update': fields.Datetime.now(),
            })

    @api.model
    def _update_all_customer_tiers(self, batch_size=200):
        _logger.info('Start batch update customer tiers; batch_size=%s', batch_size)
        domain = [('customer_rank', '>', 0)]
        total = self.search_count(domain)
        offset = 0

        while True:
            partners = self.search(domain, offset=offset, limit=batch_size, order='id asc')
            if not partners:
                break

            partners._compute_total_loyalty_points()
            partners._update_customer_tier(reason='Batch update')

            offset += batch_size
            _logger.info('Updated %s/%s customers', min(offset, total), total)

        _logger.info('Completed batch update customer tiers')
        return True
