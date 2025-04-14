from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging

_logger = logging.getLogger(__name__)

class WhatsAppTemplate(models.Model):
    _name = 'whatsapp.template'
    _description = 'WhatsApp Message Template'
    
    name = fields.Char(string='Name', required=True)
    template_name = fields.Char(string='Template Name', required=True,
                             help='Template name as configured in WhatsApp Business API')
    language_code = fields.Char(string='Language Code', required=True, default='en_US',
                             help='Language code for the template (e.g., en_US)')
    
    component_type = fields.Selection([
        ('header', 'Header'),
        ('body', 'Body'),
        ('footer', 'Footer'),
        ('buttons', 'Buttons')
    ], string='Component Type', default='body', required=True)
    
    template_text = fields.Text(string='Template Text', required=True,
                             help='Template text with variable placeholders like {{1}}, {{2}}')
    placeholder_description = fields.Text(string='Placeholder Description',
                                       help='Description of the placeholders for reference')
    
    is_active = fields.Boolean(string='Active', default=True)
    
    # Fields for syncing with Meta
    meta_template_id = fields.Char(string='Meta Template ID', readonly=True,
                                help='ID of the template in Meta Business API')
    meta_template_status = fields.Selection([
        ('approved', 'Approved'),
        ('pending', 'Pending'),
        ('rejected', 'Rejected'),
        ('not_synced', 'Not Synced')
    ], string='Template Status', default='not_synced', readonly=True)
    
    def sync_from_meta(self):
        """Sync templates from Meta WhatsApp Business API"""
        config = self.env['whatsapp.config'].get_active_config()
        
        import requests
        url = f"https://graph.facebook.com/{config.api_version}/{config.whatsapp_business_account_id}/message_templates"
        headers = {
            'Authorization': f'Bearer {config.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                templates_data = response.json().get('data', [])
                for template in templates_data:
                    template_name = template.get('name')
                    template_id = template.get('id')
                    language = template.get('language', 'en_US')
                    status = template.get('status', 'not_synced')
                    
                    # Get components
                    components = template.get('components', [])
                    body_text = ""
                    
                    for component in components:
                        if component.get('type') == 'BODY':
                            body_text = component.get('text', '')
                    
                    # Check if template already exists
                    existing_template = self.search([
                        ('template_name', '=', template_name),
                        ('language_code', '=', language)
                    ], limit=1)
                    
                    if existing_template:
                        existing_template.write({
                            'meta_template_id': template_id,
                            'meta_template_status': status.lower(),
                            'template_text': body_text,
                        })
                    else:
                        self.create({
                            'name': template_name,
                            'template_name': template_name,
                            'language_code': language,
                            'component_type': 'body',
                            'template_text': body_text,
                            'meta_template_id': template_id,
                            'meta_template_status': status.lower(),
                        })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Templates synchronized successfully!'),
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                _logger.error("WhatsApp Template Sync Error: %s", response.text)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Error'),
                        'message': _(f'Sync failed: {response.text}'),
                        'sticky': False,
                        'type': 'danger',
                    }
                }
        except Exception as e:
            _logger.error("WhatsApp Template Sync Exception: %s", str(e))
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
