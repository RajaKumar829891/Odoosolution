# File: models/payment_transaction.py
import logging
import pprint
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    wipay_transaction_id = fields.Char('WiPay Transaction ID')

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return WiPay-specific rendering values.
        
        Note: self.ensure_one() from the parent method.
        
        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'wipay':
            return res

        # Prepare the payment data for WiPay API
        provider_sudo = self.provider_id.sudo()
        payment_info = {
            'reference': self.reference,
            'amount': self.amount,
            'currency_code': self.currency_id.name,
            'partner_id': self.partner_id.id,
        }
        
        # Get the payment form data for WiPay
        form_data = provider_sudo._get_wipay_payment_form_data(payment_info)
        
        # Process the payment data through WiPay API
        payment_data = provider_sudo._process_payment_data(form_data)
        
        # If successful, the payment_data should contain a URL to redirect to
        # If not, we'll handle the error
        if payment_data and 'url' in payment_data:
            self.wipay_transaction_id = payment_data.get('transaction_id', '')
            
            # In Odoo 17, we need to return the redirect_url directly
            # instead of api_url and inputs
            return {'redirect_url': payment_data['url']}
        else:
            _logger.error("WiPay: No payment URL received for transaction %s", self.reference)
            raise ValidationError(_("WiPay: Error processing the payment, please try again."))

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on WiPay notification data.
        
        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the transaction is not found
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'wipay' or tx:
            return tx

        # Find the transaction based on the order_id (our reference)
        order_id = notification_data.get('order_id')
        if not order_id:
            raise ValidationError(_("WiPay: Missing order reference in the notification data."))
            
        tx = self.search([('reference', '=', order_id)])
        if not tx:
            raise ValidationError(_("WiPay: No transaction found matching reference %s", order_id))
            
        return tx

    def _process_notification_data(self, notification_data):
        """ Override of payment to process the notification data based on WiPay standards.
        
        Note: self.ensure_one() from the parent method.
        
        :param dict notification_data: The notification data sent by the provider
        :return: None
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'wipay':
            return

        # Update transaction fields with WiPay data
        self.provider_reference = notification_data.get('transaction_id', '')
        self.wipay_transaction_id = notification_data.get('transaction_id', '')
        
        # Process the payment outcome based on status
        status = notification_data.get('status')
        if status == 'success':
            self._set_done()
            # Log successful transaction details
            _logger.info(
                "WiPay payment transaction with reference %s: %s", 
                self.reference, notification_data.get('message', 'Payment successful')
            )
        elif status == 'failed':
            self._set_canceled(
                "WiPay: " + notification_data.get('message', 'Payment failed')
            )
        else:
            self._set_error(
                "WiPay: " + notification_data.get('message', 'Unknown payment status')
            )