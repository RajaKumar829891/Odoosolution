import json
import logging
from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)

class MyOperatorController(http.Controller):
    
    @http.route('/myoperator/webhook', type='json', auth='none', csrf=False)
    def myoperator_webhook(self, **post):
        """Webhook endpoint for MyOperator events"""
        try:
            # Get the payload
            data = request.jsonrequest
            
            # Validate webhook secret if provided
            webhook_secret = data.get('secret')
            if not webhook_secret:
                _logger.warning("Missing webhook secret in MyOperator webhook request")
                return {'status': 'error', 'message': 'Unauthorized'}
            
            # Find configuration with matching webhook secret
            # Note: You'll need to add a webhook_secret field to myoperator.config model
            config = request.env['myoperator.config'].sudo().search([
                ('webhook_secret', '=', webhook_secret),
                ('is_active', '=', True)
            ], limit=1)
            
            if not config:
                _logger.warning("Invalid webhook secret in MyOperator webhook request")
                return {'status': 'error', 'message': 'Invalid secret'}
            
            # Process the event based on event type
            event_type = data.get('event_type')
            
            if event_type == 'call':
                return self._process_call_event(data, config)
            elif event_type == 'message':
                return self._process_message_event(data, config)
            else:
                _logger.warning("Unknown event type in MyOperator webhook: %s", event_type)
                return {'status': 'error', 'message': 'Unknown event type'}
                
        except Exception as e:
            _logger.exception("Error processing MyOperator webhook: %s", str(e))
            return {'status': 'error', 'message': str(e)}
    
    def _process_call_event(self, data, config):
        """Process call-related events from MyOperator"""
        Call = request.env['myoperator.call'].sudo()
        Partner = request.env['res.partner'].sudo()
        
        call_data = data.get('data', {})
        call_id = call_data.get('id')
        
        # Check if this call already exists
        existing_call = Call.search([
            ('myoperator_call_id', '=', call_id),
            ('config_id', '=', config.id)
        ], limit=1)
        
        # Event sub-type: new, update, end
        event_subtype = data.get('event_subtype')
        
        if event_subtype == 'new' and not existing_call:
            # Create new call record
            call_values = {
                'myoperator_call_id': call_id,
                'config_id': config.id,
                'phone': call_data.get('phone'),
                'call_type': call_data.get('type'),
                'status': call_data.get('status'),
                'start_time': call_data.get('start_time'),
                'raw_data': json.dumps(call_data),
            }
            
            # Try to find partner by phone
            if call_data.get('phone'):
                partner = Partner.search([
                    '|',
                    ('phone', '=', call_data.get('phone')),
                    ('mobile', '=', call_data.get('phone')),
                ], limit=1)
                
                if partner:
                    call_values['partner_id'] = partner.id
            
            Call.create(call_values)
            return {'status': 'success', 'message': 'Call created'}
            
        elif event_subtype == 'update' and existing_call:
            # Update existing call
            existing_call.write({
                'status': call_data.get('status'),
                'duration': call_data.get('duration'),
                'agent': call_data.get('agent'),
                'raw_data': json.dumps(call_data),
            })
            return {'status': 'success', 'message': 'Call updated'}
            
        elif event_subtype == 'end' and existing_call:
            # Update existing call with end details
            existing_call.write({
                'status': call_data.get('status'),
                'duration': call_data.get('duration'),
                'end_time': call_data.get('end_time'),
                'recording_url': call_data.get('recording_url', ''),
                'raw_data': json.dumps(call_data),
            })
            return {'status': 'success', 'message': 'Call ended'}
            
        return {'status': 'warning', 'message': 'No action taken'}
    
    def _process_message_event(self, data, config):
        """Process message-related events from MyOperator"""
        Message = request.env['myoperator.message'].sudo()
        Partner = request.env['res.partner'].sudo()
        
        message_data = data.get('data', {})
        message_id = message_data.get('id')
        
        # Check if this message already exists
        existing_message = Message.search([
            ('myoperator_message_id', '=', message_id),
            ('config_id', '=', config.id)
        ], limit=1)
        
        # Event sub-type: new, status_update
        event_subtype = data.get('event_subtype')
        
        if event_subtype == 'new' and not existing_message:
            # Create new message record
            message_values = {
                'myoperator_message_id': message_id,
                'config_id': config.id,
                'phone': message_data.get('phone'),
                'direction': message_data.get('direction', 'inbound'),
                'message_type': message_data.get('type', 'text'),
                'content': message_data.get('content', ''),
                'status': message_data.get('status'),
                'timestamp': message_data.get('timestamp'),
                'media_url': message_data.get('media_url', ''),
                'raw_data': json.dumps(message_data),
            }
            
            # Try to find partner by phone
            if message_data.get('phone'):
                partner = Partner.search([
                    '|',
                    ('phone', '=', message_data.get('phone')),
                    ('mobile', '=', message_data.get('phone')),
                ], limit=1)
                
                if partner:
                    message_values['partner_id'] = partner.id
            
            Message.create(message_values)
            return {'status': 'success', 'message': 'Message created'}
            
        elif event_subtype == 'status_update' and existing_message:
            # Update existing message status
            existing_message.write({
                'status': message_data.get('status'),
                'raw_data': json.dumps(message_data),
            })
            return {'status': 'success', 'message': 'Message status updated'}
            
        return {'status': 'warning', 'message': 'No action taken'}