{
    'name': 'Dynamic Bluetooth Printer',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Dynamic discovery and connection for Bluetooth thermal printers',
    'description': """
        Scan for, connect to, and print labels on Bluetooth thermal printers directly from ODOO.
        Designed for SHREYANS 58mm and similar thermal printers.
        
        Features:
        - Real-time Bluetooth device scanning
        - Dynamic printer selection and connection
        - Custom label generation for products
        - Integrated with ODOO Inventory workflow
    """,
    'author': 'Your Name',
    'website': 'https://www.yourwebsite.com',
    'depends': [
        'stock',
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/print_label_wizard_views.xml',  # Load wizards first
        'views/wizard_actions.xml',              # Then the actions
        'views/bluetooth_printer_views.xml',     # Then other views
        'views/bluetooth_printer_discovery_views.xml',  # New discovery wizard view
        'views/product_views.xml',               # Product views last
        'data/system_params.xml',                # Default system parameters
    ],
    
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
