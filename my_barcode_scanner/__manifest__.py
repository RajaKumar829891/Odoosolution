{
    'name': 'Mobile Barcode Scanner',
    'version': '1.0',
    'category': 'Hidden',  # Already set correctly
    'summary': 'Scan barcodes using mobile camera',
    'description': """
        This module allows scanning barcodes using the mobile device camera.
        It can be used for inventory management, sales, and other operations.
        Integrates with Simply Fleet module for Work Orders.
    """,
    'author': 'Your Name',
    'website': 'https://www.yourwebsite.com',
    'depends': ['base', 'web', 'stock', 'simply_fleet'],
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/barcode_scanner_views.xml',
        'views/work_order_views.xml',
        'views/assets.xml',
        'data/ir_ui_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'my_barcode_scanner/static/src/js/barcode_scanner.js',
            'my_barcode_scanner/static/src/js/barcode_widget.js',
            'my_barcode_scanner/static/src/scss/barcode_scanner.scss',
        ],
        'web.assets_qweb': [
            'my_barcode_scanner/static/src/js/barcode_scanner.js',
            'my_barcode_scanner/static/src/js/barcode_widget.js', 
            'my_barcode_scanner/static/src/js/barcode_handler_nextline.js',
            'my_barcode_scanner/static/src/scss/barcode_scanner.scss',
            'my_barcode_scanner/static/src/xml/barcode_templates.xml',
            'my_barcode_scanner/static/src/xml/mobile_scanner_templates.xml',
        ],
    },
    'installable': True,
    'application': False,  # Already set correctly
    'auto_install': False, # Already set correctly
    'license': 'LGPL-3',
    
    # Add these additional settings to further hide the module
    'visible': False,      # Makes the module invisible in UI
    'hidden': True         # Additional flag to hide the module
}
