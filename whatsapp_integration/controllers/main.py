from odoo import http
from odoo.http import request
import json
import logging
import werkzeug

_logger = logging.getLogger(__name__)

class WhatsAppController(http.Controller):
    
    @http.route('/whatsapp/webhook', type='http', auth='public', methods=['GET'], csrf=False)
    def whatsapp_webhook_verify(self, **kwargs):
        """Handle the webhook verification from Meta"""
        try:
            # Get the active configuration
            config = request.env['whatsapp.config'].sudo().search([('is_active', '=', True)], limit=1)
            
            if not config:
                return werkzeug.wrappers.Response(
                    status=400,
                    content_type='text/plain',
                    response="No active WhatsApp configuration found."
                )
            
            mode = kwargs.get('hub.mode')
            token = kwargs.get('hub.verify_token')
            challenge = kwargs.get('hub.challenge')
            
            # Verify the token
            if mode == 'subscribe' and token == config.webhook_verify_token:
                if challenge:
                    return werkzeug.wrappers.Response(
                        status=200,
                        content_type='text/plain',
                        response=challenge
                    )
            else:
                return werkzeug.wrappers.Response(
                    status=403,
                    content_type='text/plain',
                    response="Verification failed"
                )
                
        except Exception as e:
            _logger.error("WhatsApp webhook verification error: %s", str(e))
            return werkzeug.wrappers.Response(
                status=500,
                content_type='text/plain',
                response="Internal server error"
            )
    
    @http.route('/whatsapp/webhook', type='json', auth='public', methods=['POST'], csrf=False)
    def whatsapp_webhook_receive(self, **kwargs):
        """Handle incoming webhook events from Meta"""
        try:
            # Get JSON data from the request
            data = request.jsonrequest
            _logger.info("Received webhook data: %s", json.dumps(data))
            
            # Basic validation
            if not data:
                return {'success': False, 'message': 'No data received'}
            
            # Check if it's a WhatsApp message
            entry = data.get('entry', [])
            if not entry:
                return {'success': True}  # Return success to acknowledge receipt
                
            # Process each entry
            for entry_item in entry:
                changes = entry_item.get('changes', [])
                for change in changes:
                    if change.get('field') != 'messages':
                        continue
                        
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    
                    # Process each message
                    for message in messages:
                        message_type = message.get('type')
                        
                        # Process text messages
                        if message_type == 'text':
                            message_data = {
                                'from': message.get('from'),
                                'id': message.get('id'),
                                'timestamp': message.get('timestamp'),
                                'text': message.get('text', {})
                            }
                            
                            # Create a message record
                            request.env['whatsapp.message'].sudo().create_from_webhook(message_data)
            
            # Always return success to acknowledge receipt
            return {'success': True}
            
        except Exception as e:
            _logger.error("WhatsApp webhook processing error: %s", str(e))
            # Still return success to avoid Meta retrying (we can handle errors internally)
            return {'success': True}
