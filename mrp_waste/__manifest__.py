# -*- coding: utf-8 -*-
{
    'name': 'Chau Vien - MRP Waste Tracking',
    'version': '19.0.1.0.0',
    'summary': 'Theo dõi tỷ lệ hao hụt dự kiến và thực tế trong sản xuất bán thành phẩm',
    'author': 'Chau Vien',
    'category': 'Manufacturing',
    'depends': ['mrp'],
    'data': [
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}