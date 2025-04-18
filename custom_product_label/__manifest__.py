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
- Support for 50*25mm label format
""",
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['stock', 'product'],
    'data': [
        # Start with just the template file
        'report/product_label_templates.xml',
        # Then add this back after a successful update
        # 'views/product_views.xml',
        # 'views/product_label_layout_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
