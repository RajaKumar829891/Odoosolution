import logging
import json
import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class MyOperatorMessage(models.Model):
    _name = 'myoperator.message'
    _description = 'MyOperator WhatsApp Message'
    _order = 'timestamp DESC'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Reference', compute='_compute_name', store=True)
    myoperator_message_id = fields.Char('MyOperator Message ID', required=True, 
                                       help="Unique identifier of the message in MyOperator system")
    config_id = fields.Many2one('myoperator.config', string='Configuration', required=True, 
                                ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Contact')
    phone = fields.Char('Phone Number')
    direction = fields.Selection([
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ], string='Direction', default='inbound')
    message_type = fields.Selection([
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('location', 'Location'),
        ('contact', 'Contact'),
        ('template', 'Template'),
    ], string='Message Type', default='text')
    content = fields.Text('Content')
    status = fields.Selection([
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ], string='Status')
    timestamp = fields.Datetime('Timestamp')
    media_url = fields.Char('Media URL')
    user_id = fields.Many2one('res.users', string='User')
    company_id = fields.Many2one('res.company', string='Company', related='config_id.company_id', 
                                store=True, readonly=True)
    raw_data = fields.Text('Raw Data', help="JSON data received from MyOperator API")
    
    @api.depends('myoperator_message_id', 'phone', 'partner_id')
    def _compute_name(self):
        for message in self:
            if message.partner_id:
                message.name = f"{message.partner_id.name} - {message.timestamp}"
            else:
                message.name = f"{message.phone or 'Unknown'} - {message.timestamp}"
    
    def action_create_partner(self):
        """Create a new partner from message data"""
        self.ensure_one()
        
        if not self.phone:
            raise UserError(_("Cannot create contact without phone number"))
        
        if self.partner_id:
            raise UserError(_("This message is already linked to a contact"))
        
        # Create a new partner
        partner_vals = {
            'name': self.phone,  # Default name to phone number, can be updated later
            'mobile': self.phone,
            'is_company': False,
        }
        
        partner = self.env['res.partner'].create(partner_vals)
        self.partner_id = partner.id
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': partner.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_media(self):
        """Open media URL in a new browser tab"""
        self.ensure_one()
        
        if not self.media_url:
            raise UserError(_("No media URL available for this message"))
        
        return {
            'type': 'ir.actions.act_url',
            'url': self.media_url,
            'target': 'new',
        }
    
    @api.model
    def send_message(self, phone, content, message_type='text', media_url=None, user_id=None):
        """
        Send a WhatsApp message via MyOperator API
        
        Args:
            phone (str): Phone number to send message to
            content (str): Message content
            message_type (str, optional): Type of message. Defaults to 'text'.
            media_url (str, optional): URL of media to send. Defaults to None.
            user_id (int, optional): User ID sending the message. Defaults to current user.
        
        Returns:
            dict: Result of the API call
        """
        if not user_id:
            user_id = self.env.user.id
            
        user = self.env['res.users'].browse(user_id)
        
        # Get active configuration
        config = self.env['myoperator.config'].search([
            ('is_active', '=', True),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if not config:
            raise UserError(_("No active MyOperator configuration found"))
        
        try:
            # Build API URL with token
            api_url = config._get_api_url()
            
            # Prepare message data
            message_data = {
                'phone': phone,
                'content': content,
                'type': message_type,
            }
            
            if media_url and message_type in ['image', 'video', 'audio', 'document']:
                message_data['media_url'] = media_url
            
            # Make API call to send message
            response = requests.post(f"{api_url}/whatsapp/send", data=json.dumps(message_data), 
                                    headers={'Content-Type': 'application/json'})
            result = response.json()
            
            if result.get('status') == 'success':
                # Message sent successfully
                message_id = result.get('status', {}).get('data', {}).get('id')
                
                # Try to find partner by phone
                partner_id = False
                if phone:
                    partner = self.env['res.partner'].search([
                        '|',
                        ('phone', '=', phone),
                        ('mobile', '=', phone),
                    ], limit=1)
                    
                    if partner:
                        partner_id = partner.id
                
                # Create message record
                self.create({
                    'myoperator_message_id': message_id,
                    'config_id': config.id,
                    'phone': phone,
                    'direction': 'outbound',
                    'message_type': message_type,
                    'content': content,
                    'status': 'sent',  # Initial status
                    'timestamp': fields.Datetime.now(),
                    'media_url': media_url,
                    'user_id': user_id,
                    'partner_id': partner_id,
                    'raw_data': json.dumps(result),
                })
                
                return {
                    'status': 'success',
                    'message': _("Message sent successfully"),
                    'message_id': message_id,
                }
            else:
                error_message = result.get('status', {}).get('message', 'Unknown error')
                _logger.error("Failed to send WhatsApp message via MyOperator: %s", error_message)
                
                return {
                    'status': 'error',
                    'message': _("Failed to send message: %s") % error_message,
                }
        except Exception as e:
            _logger.exception("Error while sending WhatsApp message via MyOperator: %s", str(e))
            
            return {
                'status': 'error',
                'message': _("Error: %s") % str(e),
            }