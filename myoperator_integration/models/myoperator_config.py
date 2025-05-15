import json
import logging
import requests
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class MyOperatorConfig(models.Model):
    _name = 'myoperator.config'
    _description = 'MyOperator Configuration'

    name = fields.Char('Name', required=True)
    api_token = fields.Char('API Token', required=True, help="API token from MyOperator panel")
    api_url = fields.Char('API URL', default='https://developers.myoperator.co', required=True, 
                         help="MyOperator API endpoint")
    is_active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, 
                                default=lambda self: self.env.company)
    last_call_sync = fields.Datetime('Last Call Sync', readonly=True)
    last_message_sync = fields.Datetime('Last Message Sync', readonly=True)
    auto_sync = fields.Boolean('Auto Synchronize', default=True)
    sync_interval = fields.Selection([
        ('15', '15 minutes'),
        ('30', '30 minutes'),
        ('60', '1 hour'),
        ('360', '6 hours'),
        ('720', '12 hours'),
        ('1440', '24 hours'),
    ], string='Sync Interval', default='60')
    
    # Connection status tracking
    connection_status = fields.Selection([
        ('not_tested', 'Not Tested'),
        ('connected', 'Connected'),
        ('failed', 'Connection Failed')
    ], string='Connection Status', default='not_tested')
    last_error = fields.Text('Last Error', readonly=True)
    last_checked = fields.Datetime('Last Checked', readonly=True)
    webhook_secret = fields.Char('Webhook Secret', help="Secret key used to validate incoming webhooks")
    
    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'Configuration name must be unique per company!')
    ]
    
    @api.constrains('api_token')
    def _check_api_token(self):
        for record in self:
            if not record.api_token:
                raise ValidationError(_("API Token is required!"))
    
    def action_test_connection(self):
        """Test the connection to MyOperator API"""
        self.ensure_one()
        
        try:
            # Build API URL with token
            api_url = f"{self.api_url}?token={self.api_token}"
            
            # Test API connection by fetching filters which is a lightweight call
            response = requests.get(f"{api_url}/filters")
            result = response.json()
            
            if result.get('status') == 'success':
                self.write({
                    'connection_status': 'connected',
                    'last_error': False,
                    'last_checked': fields.Datetime.now(),
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Test'),
                        'message': _('Connection to MyOperator successful!'),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                error_message = result.get('status', {}).get('message', 'Unknown error')
                self.write({
                    'connection_status': 'failed',
                    'last_error': error_message,
                    'last_checked': fields.Datetime.now(),
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Test'),
                        'message': _('Connection failed: %s') % error_message,
                        'sticky': False,
                        'type': 'danger',
                    }
                }
        except Exception as e:
            self.write({
                'connection_status': 'failed',
                'last_error': str(e),
                'last_checked': fields.Datetime.now(),
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test'),
                    'message': _('Connection failed: %s') % str(e),
                    'sticky': False,
                    'type': 'danger',
                }
            }
    
    def _get_api_url(self):
        """
        Returns properly formatted API URL with token
        """
        self.ensure_one()
        return f"{self.api_url}?token={self.api_token}"
    
    def sync_calls(self):
        """
        Synchronize call logs from MyOperator
        """
        self.ensure_one()
        
        if not self.is_active:
            _logger.info("MyOperator configuration %s is not active, skipping call sync", self.name)
            return False
        
        Call = self.env['myoperator.call']
        
        try:
            # Build API URL with token
            api_url = self._get_api_url()
            
            # Set filters for calls
            filters = "5 AND 8"  # Assuming these IDs are for call logs
            
            # If last sync time is available, only fetch calls after that time
            params = {'filters': filters, 'limit': 100}
            if self.last_call_sync:
                # Format datetime to MyOperator expected format
                last_sync = self.last_call_sync.strftime('%Y-%m-%d %H:%M:%S')
                params['date_from'] = last_sync
            
            # Make API call to get call logs
            response = requests.get(f"{api_url}/logs", params=params)
            result = response.json()
            
            if result.get('status') == 'success':
                calls_data = result.get('status', {}).get('data', [])
                calls_count = 0
                
                for call_data in calls_data:
                    # Check if call already exists in our system
                    existing_call = Call.search([
                        ('myoperator_call_id', '=', call_data.get('id')),
                    ], limit=1)
                    
                    if not existing_call:
                        # Create new call record
                        call_values = {
                            'myoperator_call_id': call_data.get('id'),
                            'phone': call_data.get('phone'),
                            'call_type': call_data.get('type'),
                            'status': call_data.get('status'),
                            'duration': call_data.get('duration', 0),
                            'start_time': call_data.get('start_time'),
                            'end_time': call_data.get('end_time'),
                            'recording_url': call_data.get('recording_url', ''),
                            'agent': call_data.get('agent', ''),
                            'config_id': self.id,
                            'raw_data': json.dumps(call_data),
                        }
                        
                        # Try to find partner by phone
                        if call_data.get('phone'):
                            partner = self.env['res.partner'].search([
                                '|',
                                ('phone', '=', call_data.get('phone')),
                                ('mobile', '=', call_data.get('phone')),
                            ], limit=1)
                            
                            if partner:
                                call_values['partner_id'] = partner.id
                        
                        Call.create(call_values)
                        calls_count += 1
                
                # Update last sync time
                self.write({'last_call_sync': fields.Datetime.now()})
                
                _logger.info("Successfully synchronized %s calls from MyOperator", calls_count)
                return calls_count
            else:
                error_message = result.get('status', {}).get('message', 'Unknown error')
                _logger.error("Failed to sync calls from MyOperator: %s", error_message)
                return False
                
        except Exception as e:
            _logger.exception("Error while synchronizing calls from MyOperator: %s", str(e))
            return False

    def sync_messages(self):
        """
        Synchronize WhatsApp messages from MyOperator
        """
        self.ensure_one()
        
        if not self.is_active:
            _logger.info("MyOperator configuration %s is not active, skipping message sync", self.name)
            return False
        
        Message = self.env['myoperator.message']
        
        try:
            # Build API URL with token
            api_url = self._get_api_url()
            
            # Assuming MyOperator has an API to fetch WhatsApp messages
            # This is a placeholder - you'll need to adjust based on actual API
            params = {'limit': 100}
            if self.last_message_sync:
                # Format datetime to MyOperator expected format
                last_sync = self.last_message_sync.strftime('%Y-%m-%d %H:%M:%S')
                params['date_from'] = last_sync
            
            # Make API call to get messages
            response = requests.get(f"{api_url}/whatsapp/messages", params=params)
            result = response.json()
            
            if result.get('status') == 'success':
                messages_data = result.get('status', {}).get('data', [])
                messages_count = 0
                
                for message_data in messages_data:
                    # Check if message already exists in our system
                    existing_message = Message.search([
                        ('myoperator_message_id', '=', message_data.get('id')),
                    ], limit=1)
                    
                    if not existing_message:
                        # Create new message record
                        message_values = {
                            'myoperator_message_id': message_data.get('id'),
                            'phone': message_data.get('phone'),
                            'direction': message_data.get('direction', 'inbound'),
                            'message_type': message_data.get('type', 'text'),
                            'content': message_data.get('content', ''),
                            'status': message_data.get('status'),
                            'timestamp': message_data.get('timestamp'),
                            'media_url': message_data.get('media_url', ''),
                            'config_id': self.id,
                            'raw_data': json.dumps(message_data),
                        }
                        
                        # Try to find partner by phone
                        if message_data.get('phone'):
                            partner = self.env['res.partner'].search([
                                '|',
                                ('phone', '=', message_data.get('phone')),
                                ('mobile', '=', message_data.get('phone')),
                            ], limit=1)
                            
                            if partner:
                                message_values['partner_id'] = partner.id
                        
                        Message.create(message_values)
                        messages_count += 1
                
                # Update last sync time
                self.write({'last_message_sync': fields.Datetime.now()})
                
                _logger.info("Successfully synchronized %s messages from MyOperator", messages_count)
                return messages_count
            else:
                error_message = result.get('status', {}).get('message', 'Unknown error')
                _logger.error("Failed to sync messages from MyOperator: %s", error_message)
                return False
                
        except Exception as e:
            _logger.exception("Error while synchronizing messages from MyOperator: %s", str(e))
            return False
            
    @api.model
    def _cron_sync_calls(self):
        """
        Cron job method to sync call logs from all active configurations
        """
        configs = self.search([
            ('is_active', '=', True),
            ('auto_sync', '=', True)
        ])
        
        for config in configs:
            try:
                _logger.info("Cron: Syncing call logs from MyOperator configuration '%s'", config.name)
                config.sync_calls()
            except Exception as e:
                _logger.exception("Error in cron job while syncing calls from MyOperator configuration '%s': %s", 
                                config.name, str(e))
    
    @api.model
    def _cron_sync_messages(self):
        """
        Cron job method to sync WhatsApp messages from all active configurations
        """
        configs = self.search([
            ('is_active', '=', True),
            ('auto_sync', '=', True)
        ])
        
        for config in configs:
            try:
                _logger.info("Cron: Syncing WhatsApp messages from MyOperator configuration '%s'", config.name)
                config.sync_messages()
            except Exception as e:
                _logger.exception("Error in cron job while syncing messages from MyOperator configuration '%s': %s", 
                                config.name, str(e))