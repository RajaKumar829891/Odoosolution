from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class WhatsAppConfig(models.Model):
    _name = 'whatsapp.config'
    _description = 'WhatsApp Configuration'

    name = fields.Char(string='Configuration Name', required=True)
    is_active = fields.Boolean(string='Active', default=True)
    
    # Meta WhatsApp API credentials
    whatsapp_phone_number_id = fields.Char(string='WhatsApp Phone Number ID', required=True,
                                        help='Phone Number ID from Meta WhatsApp Business API')
    whatsapp_business_account_id = fields.Char(string='WhatsApp Business Account ID', required=True,
                                           help='Business Account ID from Meta WhatsApp Business API')
    access_token = fields.Char(string='Access Token', required=True, 
                             help='Permanent access token from Meta Graph API')
    api_version = fields.Char(string='API Version', default='v18.0', required=True,
                            help='Meta Graph API version')
    webhook_verify_token = fields.Char(string='Webhook Verify Token', required=True,
                                    help='Token used to verify webhook setup')
    
    # Additional configuration fields
    default_message_template_id = fields.Many2one('whatsapp.template', string='Default Message Template')
    
    _sql_constraints = [
        ('whatsapp_phone_number_id_unique', 'UNIQUE(whatsapp_phone_number_id)', 
         'Phone Number ID must be unique!')
    ]
    
    @api.constrains('is_active')
    def _check_active_config(self):
        for record in self:
            if record.is_active and self.search_count([('is_active', '=', True), 
                                                      ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Only one configuration can be active at a time."))
    
    def test_connection(self):
        """Test the connection to the WhatsApp Business API"""
        self.ensure_one()
        
        url = f"https://graph.facebook.com/{self.api_version}/{self.whatsapp_phone_number_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Connection successful!'),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                _logger.error("WhatsApp API Connection Error: %s", response.text)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Error'),
                        'message': _(f'Connection failed: {response.text}'),
                        'sticky': False,
                        'type': 'danger',
                    }
                }
        except Exception as e:
            _logger.error("WhatsApp API Connection Exception: %s", str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _(f'Exception occurred: {str(e)}'),
                    'sticky': False,
                    'type': 'danger',
                }
            }
            
    @api.model
    def get_active_config(self):
        """Get the active WhatsApp configuration"""
        config = self.search([('is_active', '=', True)], limit=1)
        if not config:
            raise ValidationError(_("No active WhatsApp configuration found."))
        return config
