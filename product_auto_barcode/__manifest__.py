{
    'name': 'Product Auto Barcode',
    'version': '17.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Automatically generate barcodes for products',
    'description': """
        Automatically generates unique barcodes for products in Odoo 17 Community.
    """,
    'depends': ['product'],
    'data': [
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
