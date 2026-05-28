from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestCustomerTier(TransactionCase):
    """Tests for customer_tier_management."""

    def setUp(self):
        """Prepare reusable records without violating unique min_points."""
        super().setUp()
        self.Tier = self.env['customer.tier']
        self.Partner = self.env['res.partner']
        self.History = self.env['customer.tier.history']

        self.tier_basic = self.Tier.search([('min_points', '=', 0.0)], limit=1)
        if not self.tier_basic:
            self.tier_basic = self.Tier.create({'name': 'Basic', 'min_points': 0, 'sequence': 1})

        self.tier_silver = self.Tier.search([('min_points', '=', 100.0)], limit=1)
        if not self.tier_silver:
            self.tier_silver = self.Tier.create({'name': 'Silver', 'min_points': 100, 'sequence': 10})

        self.tier_gold = self.Tier.search([('min_points', '=', 500.0)], limit=1)
        if not self.tier_gold:
            self.tier_gold = self.Tier.create({'name': 'Gold', 'min_points': 500, 'sequence': 20})

    def _create_loyalty_program(self, name='Program Test'):
        return self.env['loyalty.program'].create({
            'name': name,
            'program_type': 'loyalty',
            'applies_on': 'both',
            'trigger': 'auto',
        })

    def test_create_tier_and_get_by_points(self):
        """a) test_create_tier_and_get_by_points"""
        tier = self.Tier._get_tier_by_points(120)
        self.assertEqual(tier, self.tier_silver)
        tier = self.Tier._get_tier_by_points(700)
        self.assertEqual(tier, self.tier_gold)
        tier = self.Tier._get_tier_by_points(10)
        self.assertEqual(tier, self.tier_basic)

    def test_partner_tier_update_on_points_change(self):
        """b) Realtime: loyalty.card.write(points) must auto-update partner tier (no manual call)."""
        if 'loyalty.card' not in self.env:
            self.skipTest('Module loyalty is not installed')

        program = self._create_loyalty_program('Program Realtime')
        partner = self.Partner.create({'name': 'Partner A', 'customer_rank': 1})
        card = self.env['loyalty.card'].create({
            'partner_id': partner.id,
            'program_id': program.id,
            'points': 50,
        })

        partner.invalidate_recordset(['x_tier_id', 'x_total_loyalty_points'])
        self.assertEqual(partner.x_tier_id, self.tier_basic)

        card.write({'points': 150})
        partner.invalidate_recordset(['x_tier_id', 'x_total_loyalty_points'])
        self.assertEqual(partner.x_tier_id, self.tier_silver)

    def test_tier_history_logging(self):
        """c) test_tier_history_logging"""
        if 'loyalty.card' not in self.env:
            self.skipTest('Module loyalty is not installed')

        program = self._create_loyalty_program('Program History')
        partner = self.Partner.create({'name': 'Partner B', 'customer_rank': 1})
        card = self.env['loyalty.card'].create({
            'partner_id': partner.id,
            'program_id': program.id,
            'points': 0,
        })

        card.write({'points': 600})

        history = self.History.search([('partner_id', '=', partner.id)], order='id desc', limit=1)
        self.assertTrue(history)
        self.assertEqual(history.new_tier_id, self.tier_gold)

    def test_batch_update(self):
        """d) test_batch_update"""
        if 'loyalty.card' not in self.env:
            self.skipTest('Module loyalty is not installed')

        program = self._create_loyalty_program('Program Batch')
        p1 = self.Partner.create({'name': 'P1', 'customer_rank': 1})
        p2 = self.Partner.create({'name': 'P2', 'customer_rank': 1})

        self.env['loyalty.card'].create({'partner_id': p1.id, 'program_id': program.id, 'points': 110.0})
        self.env['loyalty.card'].create({'partner_id': p2.id, 'program_id': program.id, 'points': 510.0})

        self.Partner._update_all_customer_tiers(batch_size=1)

        p1.invalidate_recordset(['x_tier_id'])
        p2.invalidate_recordset(['x_tier_id'])
        self.assertEqual(p1.x_tier_id, self.tier_silver)
        self.assertEqual(p2.x_tier_id, self.tier_gold)

    def test_unique_min_points(self):
        """e) test_unique_min_points"""
        with self.assertRaises(ValidationError):
            self.Tier.create({'name': 'Duplicate', 'min_points': 100})

    def test_default_tier_creation(self):
        """After install, there must be exactly one tier with min_points=0 and non-empty name."""
        zero_tiers = self.Tier.search([('min_points', '=', 0.0)])
        self.assertGreaterEqual(len(zero_tiers), 1)
        self.assertEqual(len(zero_tiers), 1)
        self.assertTrue(zero_tiers[0].name and zero_tiers[0].name.strip())

    def test_tier_change_on_reward_redemption(self):
        """When points decrease (redemption), tier must downgrade and history should be created."""
        if 'loyalty.card' not in self.env:
            self.skipTest('Module loyalty is not installed')

        program = self._create_loyalty_program('Program Redemption')
        partner = self.Partner.create({'name': 'Partner Redemption', 'customer_rank': 1})

        card = self.env['loyalty.card'].create({
            'partner_id': partner.id,
            'program_id': program.id,
            'points': 600,
        })
        partner.invalidate_recordset(['x_tier_id'])
        self.assertEqual(partner.x_tier_id, self.tier_gold)

        card.write({'points': 300})
        partner.invalidate_recordset(['x_tier_id'])
        self.assertEqual(partner.x_tier_id, self.tier_silver)

        history = self.History.search([('partner_id', '=', partner.id)], order='id desc', limit=1)
        self.assertTrue(history)
        self.assertEqual(history.new_tier_id, self.tier_silver)

    def test_loyalty_missing_graceful(self):
        """Graceful behavior when loyalty is not installed."""
        if 'loyalty.card' in self.env:
            self.skipTest('Loyalty installed, skipping graceful test')

        partner = self.Partner.create({'name': 'No Loyalty Partner', 'customer_rank': 1})
        partner._update_customer_tier(reason='Admin force update without loyalty')
        partner.invalidate_recordset(['x_tier_id'])
        self.assertEqual(partner.x_tier_id, self.tier_basic)

    def test_smart_button_and_views(self):
        """UI checks: smart button + tier field exists in inherited views."""
        form_view = self.env['ir.ui.view'].search([
            ('inherit_id.model', '=', 'res.partner'),
            ('type', '=', 'form'),
            ('arch_db', 'ilike', 'x_tier_id')
        ], limit=1)
        self.assertTrue(form_view, 'KhÃ´ng tÃ¬m tháº¥y form view káº¿ thá»«a cÃ³ chá»©a x_tier_id')
        self.assertIn('action_view_tier_history', form_view.arch_db)
        self.assertIn('x_tier_id', form_view.arch_db)

        search_view = self.env['ir.ui.view'].search([
            ('inherit_id.model', '=', 'res.partner'),
            ('type', '=', 'search'),
            ('arch_db', 'ilike', 'x_tier_id'),
        ], limit=1)
        self.assertTrue(search_view, 'KhÃ´ng tÃ¬m tháº¥y search view káº¿ thá»«a cá»§a res.partner')
        self.assertIn('x_tier_id', search_view.arch_db)
        self.assertIn("'group_by':'x_tier_id'", search_view.arch_db)
        self.assertIn('group_by', search_view.arch_db)
