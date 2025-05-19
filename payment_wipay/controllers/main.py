import logging
import pprint
from werkzeug.urls import url_encode
from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)

class WiPayController(http.Controller):
    
    @http.route('/payment/wipay/return', type='http', auth='public', csrf=False)
    def wipay_return(self, **data):
        """ Process the notification data sent by WiPay after redirection """
        _logger.info("handling redirection from WiPay with data:\n%s", pprint.pformat(data))
        
        # Find the transaction based on the reference
        reference = data.get('order_id')
        if not reference:
            raise ValidationError("No transaction reference found in the response")
            
        tx = request.env['payment.transaction'].sudo().search([('reference', '=', reference)])
        if not tx:
            raise ValidationError("No transaction found matching reference %s" % reference)
            
        # Handle different response statuses
        status = data.get('status', 'error')
        if status == 'success':
            tx._handle_notification_data('wipay', data)
            return request.redirect('/payment/status')
        else:
            # Payment failed - handle the error
            error_message = data.get('message', 'Payment failed')
            params = {
                'reference': reference,
                'error': error_message
            }
            return request.redirect('/payment/failed?' + url_encode(params))