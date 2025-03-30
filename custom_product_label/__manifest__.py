{
    'name': 'Custom Product Label',
    'version': '17.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Customize product label format for inventory',
    'description': """
Custom Product Label
===================
This module customizes the product label format to include:
- Product name
- Barcode image
- Barcode number
- Default location
""",
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['stock', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'report/product_label_templates.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
