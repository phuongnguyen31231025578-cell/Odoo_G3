# -*- coding: utf-8 -*-
from odoo import models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _load_pos_data_fields(self, config):
        result = super()._load_pos_data_fields(config)
        result += ['pos_loyalty_points', 'loyalty_rank']
        return result

    @api.model
    def _load_pos_data_search_read(self, data, config):
        result = super()._load_pos_data_search_read(data, config)
        # Re-read with our extra fields
        domain = self._load_pos_data_domain(data, config)
        fields = self._load_pos_data_fields(config)
        partners = self.search_read(domain, fields, load=False)
        return partners