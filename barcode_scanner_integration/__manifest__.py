{
    'name': 'Barcode Scanner Integration',
    'version': '17.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Integration for Helett HT20 Barcode Scanner',
    'sequence': -100,
    'description': """
        This module provides integration for Helett HT20 Barcode Scanner with Odoo 17.
        Features:
        - Inventory counting
        - Product transfers
        - Stock adjustments
    """,
    'author': 'Your Name',
    'depends': [
        'base',
        'stock',
        'barcodes',
        'web'
    ],
    'data': [
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            '/barcode_scanner_integration/static/src/js/barcode_handler.js',
            'barcode_scanner_integration/static/src/xml/barcode_handler.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
