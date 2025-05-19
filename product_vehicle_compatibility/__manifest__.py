{
    'name': 'Product Vehicle Compatibility',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Add vehicle compatibility to products',
    'description': """
        This module allows you to specify which vehicles a product/part is compatible with.
        Integrates with Simply Fleet module to manage part compatibility.
        
        Features:
        - Link products with specific vehicles
        - Link products with vehicle types
        - Find compatible parts for vehicles
        - Smart buttons for quick navigation
        - Part finder wizard
    """,
    'author': 'Your Name',
    'website': 'https://www.yourwebsite.com',
    'depends': ['stock', 'product', 'simply_fleet'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/part_finder_views.xml',
        'views/simply_fleet_compatibility_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
