# -*- coding: utf-8 -*-
{
    'name': 'Chấm Điểm Nhà Cung Cấp - Châu Viên',
    'version': '1.0',
    'category': 'Purchase',
    'summary': 'Đánh giá và đề xuất nhà cung cấp tối ưu dựa trên breakdown 100 điểm',
    'author': 'Châu Viên & Admin Group',
    'depends': ['purchase', 'stock', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'Data/evaluation_criteria_data.xml',
        'views/vendor_evaluation_views.xml',
        'views/res_partner_views.xml',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}