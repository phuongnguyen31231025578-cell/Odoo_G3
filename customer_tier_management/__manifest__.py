{
    'name': 'Customer Tier Management',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Automatic customer tiering based on loyalty points (realtime)',
    'description': """
        Adds customer loyalty tier management based on accumulated points.
        Updates customer tier in realtime when loyalty points change.
    """,
    'author': 'Your Name',
    'depends': ['base', 'sale', 'crm', 'mail', 'loyalty'],
    'data': [
        'security/ir.model.access.csv',
        'views/customer_tier_views.xml',
        'views/partner_views.xml',
        'views/tier_history_views.xml',
        'data/batch_update_action.xml',
        'views/menu_views.xml',
    ],
    'demo': ['data/demo_data.xml'],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
