{
    'name': 'WhatsApp Integration',
    'version': '1.0',
    'category': 'Marketing',
    'summary': 'Integration with WhatsApp Business API',
    'description': """
        This module provides basic integration with Meta's WhatsApp Business API.
        Features:
        - Configure WhatsApp Business API credentials
        - Send WhatsApp messages from Odoo
        - Receive and process incoming WhatsApp messages
        - Template management for WhatsApp messages
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/whatsapp_config_views.xml',
        'views/whatsapp_template_views.xml',
        'views/whatsapp_message_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
