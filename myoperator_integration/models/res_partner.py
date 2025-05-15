from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    myoperator_call_ids = fields.One2many('myoperator.call', 'partner_id', string='MyOperator Calls')
    myoperator_message_ids = fields.One2many('myoperator.message', 'partner_id', 
                                            string='MyOperator Messages')
    myoperator_call_count = fields.Integer('Call Count', compute='_compute_myoperator_counts')
    myoperator_message_count = fields.Integer('Message Count', compute='_compute_myoperator_counts')
    
    @api.depends('myoperator_call_ids', 'myoperator_message_ids')
    def _compute_myoperator_counts(self):
        for partner in self:
            partner.myoperator_call_count = len(partner.myoperator_call_ids)
            partner.myoperator_message_count = len(partner.myoperator_message_ids)
    
    def action_view_myoperator_calls(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("myoperator_integration.action_myoperator_call")
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action
    
    def action_view_myoperator_messages(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("myoperator_integration.action_myoperator_message")
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action
    
    def action_make_myoperator_call(self):
        """Make a call to this partner via MyOperator"""
        self.ensure_one()
        
        if not self.phone and not self.mobile:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Phone Number'),
                    'message': _('Contact does not have a phone number to call.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        # Use mobile number if available, otherwise use phone
        phone = self.mobile or self.phone
        
        # Make the call
        result = self.env['myoperator.call'].make_call(phone)
        
        if result.get('status') == 'success':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Call Initiated'),
                    'message': _('Call to %s has been initiated successfully.') % self.name,
                    'sticky': False,
                    'type': 'success',
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Call Failed'),
                    'message': result.get('message', _('Call initiation failed.')),
                    'sticky': False,
                    'type': 'warning',
                }
            }
    
    def action_send_myoperator_whatsapp(self):
        """Send WhatsApp message to this partner via MyOperator"""
        self.ensure_one()
        
        if not self.phone and not self.mobile:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Phone Number'),
                    'message': _('Contact does not have a phone number to send WhatsApp message.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
        
        # Use mobile number if available, otherwise use phone
        phone = self.mobile or self.phone
        
        # Open wizard to compose WhatsApp message
        return {
            'name': _('Compose WhatsApp Message'),
            'type': 'ir.actions.act_window',
            'res_model': 'myoperator.whatsapp.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_phone': phone,
            }
        }