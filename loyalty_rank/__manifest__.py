# -*- coding: utf-8 -*-
{
    'name': 'POS Loyalty Rank',
    'version': '19.0.1.0.0',
    'summary': 'Phan hang khach hang theo diem loyalty POS',
    'author': 'Custom',
    'category': 'Point of Sale',
    'depends': [
        'point_of_sale',
        'loyalty',
        'pos_loyalty',
        'crm',
        'contacts',
    ],
    'data': [
        'views/res_partner_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'loyalty_rank/static/src/components/CustomerListScreen.xml',
            'loyalty_rank/static/src/components/CustomerListScreen.js',
            'loyalty_rank/static/src/css/loyalty_rank.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}