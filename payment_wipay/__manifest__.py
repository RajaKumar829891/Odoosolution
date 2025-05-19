# File: __manifest__.py
{
    'name': 'WiPay Payment Provider',
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'summary': 'Payment Provider: WiPay Implementation',
    'description': """
WiPay Payment Provider for Odoo
===============================
WiPay is a Caribbean payment processor supporting credit/debit cards.
This module integrates WiPay's payment API with Odoo.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': ['payment'],
    'data': [
        'views/payment_provider_views.xml',
        'views/payment_wipay_templates.xml',
        'data/payment_provider_data.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_wipay/static/src/scss/payment_wipay.scss',
            'payment_wipay/static/src/js/payment_form.js',
        ],
    },
    'application': False,
    'installable': True,
    'post_init_hook': '_create_missing_payment_provider',
}