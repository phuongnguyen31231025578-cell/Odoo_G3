# -*- coding: utf-8 -*-
{
    'name': 'Châu Viên - Dữ liệu Demo',
    'version': '19.0.1.0.0',
    'summary': 'Dữ liệu mẫu chạy demo end-to-end cho 4 module nghiệp vụ Châu Viên',
    'description': """
        Seed dữ liệu demo cho buổi trình bày:
        - 3 nhà cung cấp (điểm uy tín cao / trung bình / dưới sàn 40)
        - Nguyên vật liệu thô + Bán thành phẩm (trà nền, trân châu, pudding)
        - BoM kèm tỷ lệ hao hụt dự kiến (mrp_waste)
        - Bảng giá nhà cung cấp (supplierinfo) phục vụ gợi ý NCC
        - Khách hàng mẫu phục vụ demo phân hạng / loyalty
    """,
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
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}