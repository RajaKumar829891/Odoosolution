{
    'name': 'Simply Fleet - Diesel Tanker Management',
    'version': '17.0.1.0.0',
    'category': 'Fleet',
    'summary': 'Diesel Tanker Management for Simply Fleet',
    'description': """
        Diesel Tanker Management extension for Simply Fleet
        
        Features:
        - Track diesel tanker fuel capacity
        - Monitor fuel levels with color-coded alerts
        - Manage fuel transfers from tanker to vehicles
        - Integration with existing fuel logs
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['simply_fleet'],
    'data': [
        'security/ir.model.access.csv',
        'data/diesel_tanker_sequence.xml',
        'views/diesel_tanker_views.xml',
        'views/fuel_log_views.xml',
        'views/diesel_tanker_button.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'simply_fleet_diesel_tanker/static/src/css/diesel_tanker.css',
            'simply_fleet_diesel_tanker/static/src/js/diesel_tanker_button.js',
            'simply_fleet_diesel_tanker/static/src/js/fuel_log_kanban.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}