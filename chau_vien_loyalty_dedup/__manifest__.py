# -*- coding: utf-8 -*-
{
    'name': 'Châu Viên - Loyalty Program Duplicate Check',
    'version': '19.0.1.0.0',
    'category': 'Loyalty',
    'summary': 'Chặn tạo chương trình khuyến mãi trùng lặp trên Odoo 19',
    'description': """
        Module kiểm tra và ngăn chặn tạo chương trình loyalty trùng lặp.

        Quy tắc chặn:
        - TH1: Trùng tên chương trình (bất kể tiêu chí A/B/C)
        - TH2: Không trùng tên nhưng trùng cả 3 tiêu chí:
            A. Rule: minimum_qty + minimum_purchase + reward_point_amount + reward_point_mode
            B. Reward: discount_percentage + required_points + discount_applicability
            C. Program-level: program_type + applies_on
    """,
    'author': 'Như Thanh',
    'depends': ['loyalty', 'point_of_sale'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
