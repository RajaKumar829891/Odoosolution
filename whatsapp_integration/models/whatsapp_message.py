from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
import json
import logging
import re
from datetime import datetime

_logger = logging.getLogger(__name__)

class WhatsAppMessage(models.Model):
    _name = 'whatsapp.message'
    _description = 'WhatsApp Message'
    _rec_name = 'subject'
    _order = 'create_date desc'
    
    subject = fields.Char(string='Subject', required=True)
    message_body = fields.Text(string='Message Body', required=True)
    recipient_number = fields.Char(string='Recipient Number', required=True,
                               help='Phone number with country code (e.g., +1234567890)')
    template_id = fields.Many2one('whatsapp.template', string='Message Template')
    template_parameters = fields.Text(string='Template Parameters', 
                                   help='JSON format parameters to replace placeholders in template')
    
    # For tracking purposes
    partner_id = fields.Many2one('res.partner', string='Related Contact')
    model = fields.Char(string='Related Document Model')
    res_id = fields.Integer(string='Related Document ID')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed')
    ], string='Status', default='draft', required=True)
    
    direction = fields.Selection([
        ('outgoing', 'Outgoing'),
        ('incoming', 'Incoming')
    ], string='Direction', default='outgoing', required=True)
    
    error_message = fields.Text(string='Error Message')
    meta_message_id = fields.Char(string='Meta Message ID', readonly=True)
    sent_datetime = fields.Datetime(string='Sent Date', readonly=True)
    delivered_datetime = fields.Datetime(string='Delivered Date', readonly=True)
    read_datetime = fields.Datetime(string='Read Date', readonly=True)
    
    def send_message(self):
        self.ensure_one()
        
        if self.state != 'draft':
            raise ValidationError(_("Only draft messages can be sent."))
        
        # Get active configuration
        config = self.env['whatsapp.config'].get_active_config()
        
        # Prepare API call parameters
        url = f"https://graph.facebook.com/{config.api_version}/{config.whatsapp_phone_number_id}/messages"
        headers = {
            'Authorization': f'Bearer {config.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Format phone number (ensure it has "+" prefix and no spaces)
        formatted_number = self.recipient_number.strip()
        if not formatted_number.startswith('+'):
            formatted_number = '+' + formatted_number
        
        # Remove any spaces or special characters
        formatted_number = re.sub(r'[^+0-9]', '', formatted_number)
        
        # Prepare the request payload
        if self.template_id:
            # For template messages
            try:
                parameters = []
                if self.template_parameters:
                    # Parse the template parameters from JSON
                    params_data = json.loads(self.template_parameters)
                    for param in params_data:
                        parameters.append({
                            "type": "text",
                            "text": param
                        })
                
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": formatted_number,
                    "type": "template",
                    "template": {
                        "name": self.template_id.template_name,
                        "language": {
                            "code": self.template_id.language_code
                        },
                        "components": []
                    }
                }
                
                # Add parameters if available
                if parameters:
                    payload["template"]["components"] = [
                        {
                            "type": "body",
                            "parameters": parameters
                        }
                    ]
            except Exception as e:
                self.write({
                    'state': 'failed',
                    'error_message': f"Template parameter parsing error: {str(e)}"
                })
                return False
        else:
            # For regular text messages
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": formatted_number,
                "type": "text",
                "text": {
                    "body": self.message_body
                }
            }
        
        # Send the message
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response_data = response.json()
            
            if response.status_code == 200:
                # Extract message ID from response
                meta_message_id = response_data.get('messages', [{}])[0].get('id', '')
                
                # Update the record
                self.write({
                    'state': 'sent',
                    'meta_message_id': meta_message_id,
                    'sent_datetime': fields.Datetime.now(),
                })
                return True
            else:
                error_message = response_data.get('error', {}).get('message', 'Unknown error')
                self.write({
                    'state': 'failed',
                    'error_message': f"API Error: {error_message}"
                })
                _logger.error("WhatsApp Message Send Error: %s", response.text)
                return False
                
        except Exception as e:
            self.write({
                'state': 'failed',
                'error_message': f"Exception: {str(e)}"
            })
            _logger.error("WhatsApp Message Send Exception: %s", str(e))
            return False
            
    @api.model
    def create_from_webhook(self, data):
        """Create message record from webhook data"""
        try:
            # Extract relevant data
            sender = data.get('from', '')
            message_body = data.get('text', {}).get('body', '')
            message_id = data.get('id', '')
            timestamp = data.get('timestamp', '')
            
            # Try to find the related partner
            partner = self.env['res.partner'].search([
                '|', 
                ('phone', '=', sender),
                ('mobile', '=', sender)
            ], limit=1)
            
            # Create the message
            self.create({
                'subject': f"Message from {sender}",
                'message_body': message_body,
                'recipient_number': sender,
                'partner_id': partner.id if partner else False,
                'direction': 'incoming',
                'state': 'delivered',
                'meta_message_id': message_id,
                'delivered_datetime': fields.Datetime.now(),
            })
            
            return True
        except Exception as e:
            _logger.error("Error creating message from webhook: %s", str(e))
            return False
