# -*- coding: utf-8 -*-
{
    'name': 'Châu Viên - Dữ liệu Demo',
    'version': '19.0.1.0.0',
    'summary': 'Dữ liệu mẫu chạy demo end-to-end cho 4 module nghiệp vụ Châu Viên',
    'description': "Seed dữ liệu demo Châu Viên: NCC, nguyên vật liệu, BoM, bảng giá NCC, "
                   "khách hàng và lịch sử nhập kho để chấm điểm nhà cung cấp.",
    'author': 'Nhóm G3 - Châu Viên',
    'category': 'Tools',
    'depends': [
        'vendor_evaluation',
        'mrp_waste',
        'customer_tier_management',
        'program_dedup',
    ],
    'data': [
        'data/chau_vien_catalog.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}