/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";

patch(PartnerLine.prototype, {

    getPartnerLoyaltyPoints(partner) {
        if (!partner) return 0;
        const loyaltyCards = this.pos.models['loyalty.card']?.getAll() || [];
        const partnerCards = loyaltyCards.filter(
            (card) => card.partner_id?.[0] === partner.id || card.partner_id === partner.id
        );
        return partnerCards.reduce((sum, card) => sum + (card.points || 0), 0);
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