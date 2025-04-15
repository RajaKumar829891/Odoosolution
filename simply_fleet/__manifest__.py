{
   'name': 'Simply Fleet',
   'version': '17.0.1.0.2',
   'category': 'Fleet',
   'summary': 'Vehicle Fleet Management System with Advanced Document Tracking',
   'sequence': 1,
   'description': """
       Simply Fleet Management System for managing your vehicle fleet.
       
       Features:
       - Vehicle Management
       - Advanced Vehicle Documents Management
           * Multiple Document Types Support
           * Document Expiry Tracking
           * Automated Reminders
           * Document Status Monitoring
       - Fuel Log Management
       - Smart Document Alerts
       - Document Analytics
       - Driver Management & Tracking
       - Vehicle Inspection Management
       - Work Order Management
           * Inspection-based Work Orders
           * Parts Management Integration
           * Maintenance Task Tracking
           * Cost Management
   """,
   'author': 'Your Company',
   'website': 'https://www.yourcompany.com',
   'depends': [
       'base',
       'mail',
       'web',
       'hr',  # Added HR dependency for driver management
       'stock',  # Added for parts management in work orders
       'uom',  # Added for unit of measure support in parts
   ],
   'data': [
       # Security - Note the order
       'security/simply_fleet_security.xml',
       'security/ir.model.access.csv',
       
       # Data
       'data/simply_fleet_sequence.xml',
       'data/mail_template_data.xml',
       'data/document_cron.xml',
       'data/battery_sequence.xml',
       'data/work_order_sequence.xml',  # New sequence for work orders
       
       # Views
       'views/simply_fleet_views.xml',
       'views/simply_fleet_menus.xml',
       'views/vehicle_group_views.xml',
       'views/hr_views.xml',
       'views/fleet_manager_assignment_views.xml',
       'views/fuel_log_mobile_views.xml',
       'views/battery_views.xml',
       'views/tyre_views.xml',
       'views/vehicle_image_views.xml',
       'views/simply_fleet_camera_views.xml',
       'views/vehicle_asset_views.xml',
       'views/simply_fleet_inspection_views.xml',
       'views/simply_fleet_inspection_template_views.xml',
       'views/simply_fleet_work_order_views.xml',  # New work order views
       'views/barcode_wizard_views.xml',
   ],
   # Assets Configuration
   'assets': {
       'web.assets_backend': [
           '/simply_fleet/static/src/css/mobile_styles.css',
           '/simply_fleet/static/src/js/barcode_handler.js',
           '/simply_fleet/static/src/css/vehicle_kanban.css',
           '/simply_fleet/static/src/css/vehicle_kanban.css',
       ],
   },
   'demo': [],
   'installable': True,
   'application': True,
   'auto_install': False,
   'license': 'LGPL-3',
   'post_init_hook': 'post_init_hook',
}
