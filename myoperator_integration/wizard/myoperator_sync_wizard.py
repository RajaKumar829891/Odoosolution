from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MyOperatorSyncWizard(models.TransientModel):
    _name = 'myoperator.sync.wizard'
    _description = 'MyOperator Sync Wizard'

    config_id = fields.Many2one('myoperator.config', string='Configuration', required=True,
                              domain=[('is_active', '=', True)])
    sync_calls = fields.Boolean('Sync Calls', default=True)
    sync_messages = fields.Boolean('Sync WhatsApp Messages', default=True)
    date_from = fields.Datetime('Date From')
    date_to = fields.Datetime('Date To', default=fields.Datetime.now)
    
    def action_sync(self):
        """Synchronize data from MyOperator"""
        self.ensure_one()
        
        if not self.sync_calls and not self.sync_messages:
            raise UserError(_("Please select at least one type of data to synchronize"))
        
        # Prepare result message
        result_message = ""
        
        # Sync calls if selected
        if self.sync_calls:
            call_count = self.config_id.sync_calls()
            if call_count:
                result_message += _("%s calls synchronized successfully.\n") % call_count
            else:
                result_message += _("Failed to synchronize calls.\n")
        
        # Sync messages if selected
        if self.sync_messages:
            message_count = self.config_id.sync_messages()
            if message_count:
                result_message += _("%s messages synchronized successfully.") % message_count
            else:
                result_message += _("Failed to synchronize messages.")
        
        # Show result notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Synchronization Result'),
                'message': result_message,
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }