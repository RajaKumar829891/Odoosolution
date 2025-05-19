{
    'name': 'Fleet Booking System',
    'version': '17.0.1.0.0',
    'category': 'Services/Fleet',
    'summary': 'Manage fleet bookings and transportation orders',
    'description': """
        Fleet Booking System for Odoo 17
        ===============================
        This module provides functionality for managing fleet bookings, 
        creating orders, tracking status changes, and managing customers,
        drivers, vehicles, and transportation details.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base', 
        'mail', 
        'web', 
        'hr',
        'simply_fleet',  # Dependency on Simply Fleet
    ],
    'data': [
        # Security first
        'security/fleet_booking_security.xml',
        'security/ir.model.access.csv',
        
        # Data files
        'data/fleet_booking_init_data.xml',
        'data/fleet_status_data.xml',
        'data/fleet_booking_data.xml',
        
        # Wizards
        'wizards/driver_assign_wizard_views.xml',
        'wizards/payment_register_wizard_views.xml',
        'wizards/import_simply_fleet_vehicles_views.xml',
        
        # Views
        'views/fleet_booking_views.xml',
        'views/fleet_booking_status_views.xml',
        'views/fleet_route_views.xml',
        'views/customer_views.xml',
        'views/driver_views.xml',
        'views/transport_views.xml',
        'views/vehicle_views.xml',
        'views/vehicle_views_ext.xml',  # Only form view inheritance
        'views/import_menu.xml',        # Separate file for menu
        'views/templates.xml',
        'views/menu_views.xml',
        'views/assets.xml',
        
        # Reports
        'reports/fleet_booking_reports.xml',
        'reports/report_fleet_booking_invoice.xml',
    ],
    'demo': [],
    'post_init_hook': 'AIzaSyB6yP-T09O2hB-cEG8d0-WhPXcSJnDkgro',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'fleet_booking/static/src/css/fleet_booking.css',
            'fleet_booking/static/src/css/google_maps_route.css',
            'fleet_booking/static/src/js/fleet_booking.js',
            'fleet_booking/static/src/js/google_maps_route_widget.js',
            'fleet_booking/static/src/xml/fleet_booking_templates.xml',
            'fleet_booking/static/src/js/google_maps_widget.js',
            'fleet_booking/static/src/xml/google_maps_widget.xml',
            'fleet_booking/static/src/xml/google_maps_route_widget.xml',
        ],
    },
    'images': ['static/description/icon.png'],
}