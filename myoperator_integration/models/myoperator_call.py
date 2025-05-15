import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class MyOperatorCall(models.Model):
    _name = 'myoperator.call'
    _description = 'MyOperator Call Log'
    _order = 'start_time DESC'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Call Reference', compute='_compute_name', store=True)
    myoperator_call_id = fields.Char('MyOperator Call ID', required=True, 
                                    help="Unique identifier of the call in MyOperator system")
    config_id = fields.Many2one('myoperator.config', string='Configuration', required=True, 
                                ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Contact')
    phone = fields.Char('Phone Number')
    call_type = fields.Selection([
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
        ('missed', 'Missed'),
    ], string='Call Type', default='incoming')
    status = fields.Selection([
        ('connected', 'Connected'),
        ('missed', 'Missed'),
        ('rejected', 'Rejected'),
        ('busy', 'Busy'),
        ('voicemail', 'Voicemail'),
        ('failed', 'Failed'),
    ], string='Status')
    duration = fields.Integer('Duration (sec)')
    start_time = fields.Datetime('Start Time')
    end_time = fields.Datetime('End Time')
    recording_url = fields.Char('Recording URL')
    notes = fields.Text('Notes')
    agent = fields.Char('Agent')
    user_id = fields.Many2one('res.users', string='User')
    company_id = fields.Many2one('res.company', string='Company', related='config_id.company_id', 
                                store=True, readonly=True)
    raw_data = fields.Text('Raw Data', help="JSON data received from MyOperator API")
    
    @api.depends('myoperator_call_id', 'phone', 'partner_id')
    def _compute_name(self):
        for call in self:
            if call.partner_id:
                call.name = f"{call.partner_id.name} - {call.start_time}"
            else:
                call.name = f"{call.phone or 'Unknown'} - {call.start_time}"
    
    def action_create_partner(self):
        """Create a new partner from call data"""
        self.ensure_one()
        
        if not self.phone:
            raise UserError(_("Cannot create contact without phone number"))
        
        if self.partner_id:
            raise UserError(_("This call is already linked to a contact"))
        
        # Create a new partner
        partner_vals = {
            'name': self.phone,  # Default name to phone number, can be updated later
            'phone': self.phone,
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
    
    def action_play_recording(self):
        """Open recording URL in a new browser tab"""
        self.ensure_one()
        
        if not self.recording_url:
            raise UserError(_("No recording URL available for this call"))
        
        return {
            'type': 'ir.actions.act_url',
            'url': self.recording_url,
            'target': 'new',
        }
    
    @api.model
    def make_call(self, phone, user_id=None):
        """
        Initiate an outbound call via MyOperator API
        
        Args:
            phone (str): Phone number to call
            user_id (int, optional): User ID initiating the call. Defaults to current user.
        
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
            import requests
            import json
            
            # Build API URL with token
            api_url = config._get_api_url()
            
            # Prepare call data
            call_data = {
                'phone': phone,
                'agent': user.name,
                # Add other parameters as required by MyOperator API
            }
            
            # Make API call to initiate call
            response = requests.post(f"{api_url}/call", data=json.dumps(call_data), 
                                    headers={'Content-Type': 'application/json'})
            result = response.json()
            
            if result.get('status') == 'success':
                # Call initiated successfully
                call_id = result.get('status', {}).get('data', {}).get('id')
                
                # Create call record
                self.create({
                    'myoperator_call_id': call_id,
                    'config_id': config.id,
                    'phone': phone,
                    'call_type': 'outgoing',
                    'status': 'connected',  # Initial status
                    'user_id': user_id,
                    'start_time': fields.Datetime.now(),
                    'raw_data': json.dumps(result),
                    
                    # Try to find partner by phone
                    'partner_id': self.env['res.partner'].search([
                        '|',
                        ('phone', '=', phone),
                        ('mobile', '=', phone),
                    ], limit=1).id or False,
                })
                
                return {
                    'status': 'success',
                    'message': _("Call initiated successfully"),
                    'call_id': call_id,
                }
            else:
                error_message = result.get('status', {}).get('message', 'Unknown error')
                _logger.error("Failed to initiate call via MyOperator: %s", error_message)
                
                return {
                    'status': 'error',
                    'message': _("Failed to initiate call: %s") % error_message,
                }
        except Exception as e:
            _logger.exception("Error while initiating call via MyOperator: %s", str(e))
            
            return {
                'status': 'error',
                'message': _("Error: %s") % str(e),
            }