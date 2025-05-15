{
    'name': 'MyOperator Integration',
    'version': '17.0.1.0.0',
    'category': 'CRM',
    'summary': 'Integrate MyOperator call and WhatsApp services with Odoo',
    'description': """
        MyOperator Integration Module for Odoo
        =====================================
        
        This module integrates MyOperator call and WhatsApp services with Odoo.
        Features:
        - Configure MyOperator API credentials
        - Sync call logs from MyOperator
        - Sync WhatsApp messages from MyOperator
        - Make outbound calls directly from Odoo
        - Send WhatsApp messages directly from Odoo
        - Link customers with their communication history
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'contacts',
        'mail',
        'web',
    ],
    'data': [
        'security/myoperator_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/myoperator_data.xml',
        'wizard/views/myoperator_sync_wizard_views.xml',
        'wizard/views/myoperator_whatsapp_wizard_views.xml',
        'views/myoperator_config_views.xml',
        'views/myoperator_call_views.xml',
        'views/myoperator_message_views.xml',
        'views/res_partner_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Only include essential JavaScript and CSS
            'myoperator_integration/static/src/css/myoperator_style.css',
        ],
    },
    'demo': [],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}