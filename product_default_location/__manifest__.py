{
    'name': 'Product Default Location',
    'version': '17.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Show default location field on product form',
    'description': """
        This module adds a default location field to the product form view
        allowing users to specify a product location while creating a product.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['stock'],
    'data': [
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
