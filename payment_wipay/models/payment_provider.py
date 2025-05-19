# File: models/payment_provider.py
import hashlib
import logging
import requests
from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('wipay', 'WiPay')],
        ondelete={'wipay': 'set default'},
    )
    wipay_account_number = fields.Char(
        string="WiPay Account Number", 
        help="The WiPay account number used for this provider"
    )
    wipay_api_key = fields.Char(
        string="WiPay API Key",
        help="The API key used to authenticate with WiPay"
    )
    wipay_environment = fields.Selection(
        selection=[('sandbox', 'Sandbox'), ('live', 'Live')],
        string="WiPay Environment",
        default='sandbox'
    )
    wipay_fee_structure = fields.Selection(
        selection=[
            ('customer_pay', 'Customer Pays Fee'),
            ('merchant_absorb', 'Merchant Absorbs Fee'),
            ('split', 'Split Fee')
        ],
        string="Fee Structure",
        default='merchant_absorb'
    )
    wipay_country_code = fields.Selection(
        selection=[('TT', 'Trinidad & Tobago'), ('JM', 'Jamaica'), ('BB', 'Barbados')],
        string="WiPay Country Code",
        default='TT'
    )
    wipay_currency = fields.Selection(
        selection=[('TTD', 'TTD'), ('JMD', 'JMD'), ('USD', 'USD')],
        string="WiPay Currency",
        default='TTD'
    )
    
    @api.model
    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        """ Override of payment to filter out WiPay providers for unsupported currencies. """
        providers = super()._get_compatible_providers(*args, currency_id=currency_id, **kwargs)

        currency = self.env['res.currency'].browse(currency_id).exists()
        if currency:
            for provider in providers.filtered(lambda p: p.code == 'wipay'):
                # If the provider's currency doesn't match the payment currency, filter it out
                if currency.name not in ['TTD', 'JMD', 'USD'] or currency.name != provider.wipay_currency:
                    providers -= provider

        return providers
    
    def _get_supported_payment_methods(self):
        """ Override of payment to return supported payment methods. """
        self.ensure_one()
        res = super()._get_supported_payment_methods()
        if self.code != 'wipay':
            return res
            
        return self.env.ref('payment_wipay.payment_method_wipay')
    
    def _wipay_get_api_url(self):
        self.ensure_one()
        if self.wipay_country_code == 'TT':
            base_url = 'https://tt.wipayfinancial.com'
        elif self.wipay_country_code == 'JM':
            base_url = 'https://jm.wipayfinancial.com'
        elif self.wipay_country_code == 'BB':
            base_url = 'https://bb.wipayfinancial.com'
        else:
            base_url = 'https://tt.wipayfinancial.com'  # Default to TT
        
        return f"{base_url}/plugins/payments/request"
        
    def _get_wipay_payment_form_data(self, payment_info):
        """Prepare the data for the WiPay payment form."""
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        tx = self.env['payment.transaction'].search([('reference', '=', payment_info['reference'])])
        
        data = {
            'account_number': self.wipay_account_number,
            'avs': '0',  # Default to non-AVS
            'country_code': self.wipay_country_code,
            'currency': self.wipay_currency,
            'environment': self.wipay_environment,
            'fee_structure': self.wipay_fee_structure,
            'method': 'credit_card',
            'order_id': payment_info['reference'],
            'origin': f'Odoo-{self.company_id.name}',
            'response_url': urls.url_join(base_url, '/payment/wipay/return'),
            'total': "{:.2f}".format(payment_info['amount']),
            'version': '1.0.0',
        }
        
        # Optional Customer Info (prefilled if available)
        if tx.partner_id:
            partner = tx.partner_id
            data.update({
                'name': partner.name if partner.name else '',
                'email': partner.email if partner.email else '',
                'phone': partner.phone if partner.phone else ''
            })
            # Address info for optional AVS
            if partner.street:
                data.update({
                    'addr1': partner.street,
                    'city': partner.city if partner.city else '',
                    'country': partner.country_id.code if partner.country_id else '',
                    'state': partner.state_id.code if partner.state_id else '',
                    'zipcode': partner.zip if partner.zip else ''
                })
                if partner.street2:
                    data['addr2'] = partner.street2
        
        return data
    
    def _process_payment_data(self, data):
        self.ensure_one()
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            _logger.info("Sending payment request to WiPay for reference %s", data.get('order_id'))
            response = requests.post(self._wipay_get_api_url(), data=data, headers=headers, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            _logger.exception("Error while communicating with WiPay: %s", e)
            raise ValidationError(_("WiPay: Could not establish the connection to the API."))
    
    def _verify_wipay_signature(self, data):
        """Verify the data signature."""
        self.ensure_one()
        received_hash = data.get('hash')
        
        # Cannot verify without the hash
        if not received_hash:
            return False
            
        # The hash is calculated using: transaction_id + total + API Key
        string_to_hash = data.get('transaction_id') + data.get('total') + self.wipay_api_key
        calculated_hash = hashlib.md5(string_to_hash.encode()).hexdigest()
        
        return calculated_hash == received_hash