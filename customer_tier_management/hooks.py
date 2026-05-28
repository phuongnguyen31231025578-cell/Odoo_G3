import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    if not hasattr(env, 'registry'):
        env = api.Environment(env, SUPERUSER_ID, {})

    tier_model = env['customer.tier']

    zero_tiers = tier_model.search([('min_points', '=', 0.0)])
    if len(zero_tiers) == 0:
        tier_model.create({
            'name': 'Basic',
            'sequence': 1,
            'min_points': 0.0,
            'auto_discount_percent': 0.0,
            'color': 0,
            'active': True,
        })
    elif len(zero_tiers) > 1:
        _logger.warning('Found multiple tiers with min_points=0. Please keep exactly one default tier.')


def pre_init_hook(cr):
    pass


def uninstall_hook(env):
    pass


def post_load():
    pass


def post_init_hook_legacy(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    post_init_hook(env)
