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
    api_url = fields.Char('API URL', default='https://in.app.myoperator.com/api', required=True, 
                         help="MyOperator API endpoint")
    webhook_url = fields.Char('Webhook URL', default='https://yourserver.com/myoperator/webhook', 
                             help="URL that will receive events from MyOperator")
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
            # Build API URL
            api_url = self.api_url
            
            # Set user agent to mimic a browser
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
            
            # Create a session to maintain cookies
            session = requests.Session()
            
            # Prepare different authentication headers
            headers = {
                'User-Agent': user_agent,
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'X-API-KEY': self.api_token,
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json',
                'Origin': 'https://in.app.myoperator.com',
                'Referer': 'https://in.app.myoperator.com/',
            }
            
            # Try a direct API request with the headers
            _logger.info("Testing connection to MyOperator API: %s", api_url)
            
            # Check if this is a MyOperator Public API or a different type of API
            is_public_api = 'public_api' in api_url or 'public-api' in api_url
            
            # If this is the public API, we might need to use a different approach
            if is_public_api:
                _logger.info("Detected MyOperator Public API, trying with public access method")
                
                # For public API, we will try to create a complete URL with the token
                api_request_url = f"{api_url}"
                
                # Try different authentication methods for public API
                auth_methods = [
                    # Method 1: Token as query parameter
                    {'url': f"{api_url}?token={self.api_token}", 'headers': headers},
                    # Method 2: Auth as query parameter
                    {'url': f"{api_url}?auth={self.api_token}", 'headers': headers},
                    # Method 3: API key as query parameter
                    {'url': f"{api_url}?api_key={self.api_token}", 'headers': headers},
                    # Method 4: Key as query parameter
                    {'url': f"{api_url}?key={self.api_token}", 'headers': headers},
                    # Method 5: X-API-KEY header only
                    {'url': api_url, 'headers': {**headers, 'X-API-KEY': self.api_token}},
                    # Method 6: Bearer token header only
                    {'url': api_url, 'headers': {**headers, 'Authorization': f'Bearer {self.api_token}'}},
                    # Method 7: Token in path for REST APIs
                    {'url': f"{api_url}/{self.api_token}", 'headers': headers},
                ]
                
                # Try each method
                for i, method in enumerate(auth_methods):
                    try:
                        _logger.info(f"Trying authentication method {i+1}")
                        response = session.get(method['url'], headers=method['headers'], timeout=15)
                        
                        # Check if we got a valid response
                        if response.status_code == 200:
                            try:
                                # Try to parse as JSON
                                result = response.json()
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
                                        'message': _('Connection to MyOperator successful! Method %s worked.') % (i+1),
                                        'sticky': False,
                                        'type': 'success',
                                    }
                                }
                            except json.JSONDecodeError:
                                # Not JSON but still 200 OK
                                if "<!DOCTYPE html>" not in response.text:  # Avoid HTML responses
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
                                            'message': _('Connection to MyOperator successful! Method %s worked (non-JSON response).') % (i+1),
                                            'sticky': False,
                                            'type': 'success',
                                        }
                                    }
                        
                        # If we received Cloudflare challenge or similar
                        if "Just a moment..." in response.text:
                            _logger.info("Received Cloudflare challenge, API might be protected")
                    except Exception as e:
                        _logger.debug(f"Method {i+1} failed: {str(e)}")
                
                # If we reach here, all methods failed
                
                # Try making a POST request instead of GET for token verification
                try:
                    _logger.info("Trying POST request for token verification")
                    post_data = {"token": self.api_token}
                    post_response = session.post(api_url, json=post_data, headers=headers, timeout=15)
                    
                    if post_response.status_code == 200:
                        try:
                            result = post_response.json()
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
                                    'message': _('Connection to MyOperator successful using POST verification!'),
                                    'sticky': False,
                                    'type': 'success',
                                }
                            }
                        except:
                            pass
                except:
                    pass
            
            # If we're still here, the connection failed
            
            # The response indicates Cloudflare or similar protection
            error_message = (
                "HTTP Error: 403 - Could not authenticate with the MyOperator API. The API appears to be "
                "protected by Cloudflare or similar service that prevents programmatic access. Please: \n"
                "1. Verify your API token is correct\n"
                "2. Contact MyOperator support to get the correct API endpoint and authentication method\n"
                "3. Check if your IP address needs to be whitelisted\n"
                "4. Confirm if the API requires special headers or authentication method"
            )
            
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
                    'message': _('Connection failed: API access is restricted. Please contact MyOperator support for correct API access details.'),
                    'sticky': False,
                    'type': 'danger',
                }
            }
        except Exception as e:
            # Catch all other exceptions
            error_message = f"Unexpected error: {str(e)}"
            _logger.exception("Error in MyOperator connection test: %s", error_message)
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
    
    def _get_api_url(self):
        """
        Returns properly formatted API URL
        """
        self.ensure_one()
        # Return the base API URL - we'll add specific endpoints in each method
        return self.api_url
    
    def _get_headers(self):
        """
        Returns common headers for API requests
        """
        return {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
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
            # Get base API URL
            api_url = self._get_api_url()
            
            # Call logs endpoint - adjust based on actual API
            calls_endpoint = f"{api_url}/call/logs"
            
            # Prepare headers
            headers = self._get_headers()
            
            # If last sync time is available, only fetch calls after that time
            params = {'limit': 100}
            if self.last_call_sync:
                # Format datetime to MyOperator expected format - adjust format if needed
                last_sync = self.last_call_sync.strftime('%Y-%m-%d %H:%M:%S')
                params['from_date'] = last_sync
            
            # Make API call to get call logs with timeout
            response = requests.get(calls_endpoint, headers=headers, params=params, timeout=20)
            
            # Check response before parsing
            if response.status_code != 200:
                _logger.error("HTTP error when syncing calls: %s", response.status_code)
                return False
                
            # Handle possible JSON parsing errors
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                _logger.error("JSON parsing error when syncing calls: %s", str(e))
                return False
            
            # Extract call data from response - adjust based on actual API response structure
            if (result.get('success') == True or 
                result.get('status') == 'success' or 
                result.get('status') == 200 or 
                result.get('code') == 200):
                
                # Get the call data array - adjust path based on actual API response
                calls_data = []
                if isinstance(result.get('data'), list):
                    calls_data = result.get('data')
                elif isinstance(result.get('data'), dict) and 'calls' in result.get('data'):
                    calls_data = result.get('data').get('calls', [])
                elif 'calls' in result:
                    calls_data = result.get('calls', [])
                elif 'records' in result:
                    calls_data = result.get('records', [])
                
                calls_count = 0
                
                for call_data in calls_data:
                    # Get the call ID - may have different key names
                    call_id = (call_data.get('id') or 
                              call_data.get('call_id') or 
                              call_data.get('uuid'))
                    
                    if not call_id:
                        _logger.warning("Call data missing ID, skipping: %s", call_data)
                        continue
                    
                    # Check if call already exists in our system
                    existing_call = Call.search([
                        ('myoperator_call_id', '=', call_id),
                    ], limit=1)
                    
                    if not existing_call:
                        # Get phone number - may have different key names
                        phone = (call_data.get('phone') or 
                                call_data.get('caller_number') or 
                                call_data.get('from') or
                                call_data.get('customer_number'))
                        
                        # Create new call record - adjust field mapping as needed
                        call_values = {
                            'myoperator_call_id': call_id,
                            'phone': phone,
                            'call_type': (call_data.get('type') or 
                                         call_data.get('call_type') or
                                         call_data.get('direction') or
                                         'incoming'),
                            'status': (call_data.get('status') or 
                                      call_data.get('call_status')),
                            'duration': (call_data.get('duration', 0) or 
                                        call_data.get('call_duration', 0)),
                            'start_time': (call_data.get('start_time') or 
                                          call_data.get('timestamp') or
                                          call_data.get('created_at')),
                            'end_time': (call_data.get('end_time') or 
                                        call_data.get('hangup_time')),
                            'recording_url': (call_data.get('recording_url', '') or 
                                            call_data.get('recording', '')),
                            'agent': (call_data.get('agent', '') or 
                                     call_data.get('agent_name', '') or
                                     call_data.get('assigned_to', '')),
                            'config_id': self.id,
                            'raw_data': json.dumps(call_data),
                        }
                        
                        # Try to find partner by phone
                        if phone:
                            partner = self.env['res.partner'].search([
                                '|',
                                ('phone', '=', phone),
                                ('mobile', '=', phone),
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
                error_message = (result.get('message') or 
                               result.get('error') or 
                               result.get('error_message') or 
                               'Unknown error')
                _logger.error("Failed to sync calls from MyOperator: %s", error_message)
                return False
                
        except requests.exceptions.RequestException as e:
            _logger.exception("Network error while synchronizing calls from MyOperator: %s", str(e))
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
            # Get base API URL
            api_url = self._get_api_url()
            
            # WhatsApp messages endpoint - using the URL you provided as a hint
            messages_endpoint = f"{api_url}/whatsapp/messages"
            
            # Prepare headers
            headers = self._get_headers()
            
            # If last sync time is available, only fetch messages after that time
            params = {'limit': 100}
            if self.last_message_sync:
                # Format datetime to MyOperator expected format - adjust format if needed
                last_sync = self.last_message_sync.strftime('%Y-%m-%d %H:%M:%S')
                params['from_date'] = last_sync
            
            # Make API call to get messages with timeout
            response = requests.get(messages_endpoint, headers=headers, params=params, timeout=20)
            
            # Check response before parsing
            if response.status_code != 200:
                _logger.error("HTTP error when syncing messages: %s", response.status_code)
                return False
                
            # Handle possible JSON parsing errors
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                _logger.error("JSON parsing error when syncing messages: %s", str(e))
                return False
            
            # Extract message data from response - adjust based on actual API response structure
            if (result.get('success') == True or 
                result.get('status') == 'success' or 
                result.get('status') == 200 or 
                result.get('code') == 200):
                
                # Get the message data array - adjust path based on actual API response
                messages_data = []
                if isinstance(result.get('data'), list):
                    messages_data = result.get('data')
                elif isinstance(result.get('data'), dict) and 'messages' in result.get('data'):
                    messages_data = result.get('data').get('messages', [])
                elif 'messages' in result:
                    messages_data = result.get('messages', [])
                elif 'records' in result:
                    messages_data = result.get('records', [])
                
                messages_count = 0
                
                for message_data in messages_data:
                    # Get the message ID - may have different key names
                    message_id = (message_data.get('id') or 
                                 message_data.get('message_id') or 
                                 message_data.get('uuid'))
                    
                    if not message_id:
                        _logger.warning("Message data missing ID, skipping: %s", message_data)
                        continue
                    
                    # Check if message already exists in our system
                    existing_message = Message.search([
                        ('myoperator_message_id', '=', message_id),
                    ], limit=1)
                    
                    if not existing_message:
                        # Get phone number - may have different key names
                        phone = (message_data.get('phone') or 
                                message_data.get('to') or 
                                message_data.get('customer_number') or
                                message_data.get('recipient'))
                        
                        # Create new message record - adjust field mapping as needed
                        message_values = {
                            'myoperator_message_id': message_id,
                            'phone': phone,
                            'direction': (message_data.get('direction') or 
                                         ('outbound' if message_data.get('is_outbound') else 'inbound')),
                            'message_type': (message_data.get('type') or 
                                           message_data.get('message_type') or
                                           'text'),
                            'content': (message_data.get('content') or 
                                       message_data.get('body') or
                                       message_data.get('text') or
                                       ''),
                            'status': (message_data.get('status') or 
                                      message_data.get('delivery_status')),
                            'timestamp': (message_data.get('timestamp') or 
                                         message_data.get('created_at') or
                                         message_data.get('sent_at')),
                            'media_url': (message_data.get('media_url', '') or 
                                         message_data.get('file_url', '') or
                                         message_data.get('attachment', '')),
                            'config_id': self.id,
                            'raw_data': json.dumps(message_data),
                        }
                        
                        # Try to find partner by phone
                        if phone:
                            partner = self.env['res.partner'].search([
                                '|',
                                ('phone', '=', phone),
                                ('mobile', '=', phone),
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
                error_message = (result.get('message') or 
                               result.get('error') or 
                               result.get('error_message') or 
                               'Unknown error')
                _logger.error("Failed to sync messages from MyOperator: %s", error_message)
                return False
                
        except requests.exceptions.RequestException as e:
            _logger.exception("Network error while synchronizing messages from MyOperator: %s", str(e))
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