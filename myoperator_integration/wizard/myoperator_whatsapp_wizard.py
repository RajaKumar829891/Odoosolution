from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MyOperatorWhatsAppWizard(models.TransientModel):
    _name = 'myoperator.whatsapp.wizard'
    _description = 'Send WhatsApp Message Wizard'

    partner_id = fields.Many2one('res.partner', string='Contact')
    phone = fields.Char('Phone Number', required=True)
    message_type = fields.Selection([
        ('text', 'Text'),
        ('image', 'Image'),
        ('document', 'Document'),
    ], string='Message Type', default='text', required=True)
    content = fields.Text('Message', required=True)
    attachment = fields.Binary('Attachment')
    attachment_filename = fields.Char('Attachment Filename')
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            # Use mobile number if available, otherwise use phone
            self.phone = self.partner_id.mobile or self.partner_id.phone
    
    def action_send_message(self):
        """Send WhatsApp message via MyOperator"""
        self.ensure_one()
        
        if not self.phone:
            raise UserError(_("Phone number is required to send WhatsApp message"))
        
        if not self.content:
            raise UserError(_("Message content is required"))
        
        # Media handling (this is a simplified version)
        media_url = None
        if self.message_type in ['image', 'document'] and self.attachment:
            # In a real implementation, you would upload the attachment to a cloud storage
            # or to MyOperator directly, and get a URL in return
            # For now, we'll just handle text messages
            raise UserError(_("Attachments are not supported in this version"))
        
        # Send the message
        result = self.env['myoperator.message'].send_message(
            phone=self.phone,
            content=self.content,
            message_type=self.message_type,
            media_url=media_url
        )
        
        # Show result notification
        if result.get('status') == 'success':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Message Sent'),
                    'message': _('WhatsApp message sent successfully.'),
                    'sticky': False,
                    'type': 'success',
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Message Failed'),
                    'message': result.get('message', _('Failed to send WhatsApp message.')),
                    'sticky': False,
                    'type': 'warning',
                }
            }