/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";

patch(PartnerLine.prototype, {
    getPartnerLoyaltyPoints(partner) {
        if (!partner) return 0;
        // Thử đọc từ loyalty cards trong POS models trước
        try {
            const allCards = this.pos.models['loyalty.card']
                ? this.pos.models['loyalty.card'].getAll()
                : [];
            const pts = allCards
                .filter(c => c.partner_id === partner.id)
                .reduce((s, c) => s + (c.points || 0), 0);
            if (pts > 0) return pts;
        } catch(e) {}
        // Fallback về stored field
        return partner.pos_loyalty_points || 0;
    },

    getLoyaltyRank(points) {
        if (points >= 255) return '💎 Kim Cương';
        if (points >= 175) return '🥇 Vàng';
        if (points >= 110) return '🥈 Bạc';
        if (points >= 50)  return '🥉 Đồng';
        return '🔘 Thường';
    },

    getRankBadgeClass(points) {
        if (points >= 255) return 'rank-diamond';
        if (points >= 175) return 'rank-gold';
        if (points >= 110) return 'rank-silver';
        if (points >= 50)  return 'rank-bronze';
        return 'rank-normal';
    },
});