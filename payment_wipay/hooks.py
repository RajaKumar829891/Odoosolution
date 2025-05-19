# File: hooks.py
from odoo import api, SUPERUSER_ID

def _create_missing_payment_provider(env):
    """Create a payment provider for WiPay if not already existing."""
    if not env['payment.provider'].search([('code', '=', 'wipay')]):
        env['payment.provider'].create({
            'name': 'WiPay',
            'code': 'wipay',
            'state': 'test',
            'company_id': env.ref('base.main_company').id,
            'wipay_account_number': '1234567890',
            'wipay_api_key': '123',
            'wipay_environment': 'sandbox',
            'wipay_fee_structure': 'merchant_absorb',
            'wipay_country_code': 'TT',
            'wipay_currency': 'TTD',
        })