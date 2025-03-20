from odoo import models, fields, api

class BluetoothPrinterScanWizard(models.TransientModel):
    _name = 'bluetooth.printer.scan.wizard'
    _description = 'Scan for Bluetooth Printers'
    
    bridge_url = fields.Char('Bridge URL', required=True)
    device_count = fields.Integer('Devices Found', readonly=True)
    device_ids = fields.One2many('bluetooth.printer.device', 'wizard_id', string='Discovered Devices')
    
    def action_rescan(self):
        """Rescan for Bluetooth devices"""
        # Clear existing devices
        self.device_ids.unlink()
        
        # Trigger scan in parent model
        return self.env['bluetooth.printer'].action_scan_printers()
    
    def action_add_selected(self):
        """Add selected devices as printers"""
        selected_devices = self.device_ids.filtered(lambda d: d.selected)
        
        if not selected_devices:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Selection',
                    'message': 'Please select at least one printer device',
                    'type': 'warning',
                }
            }
        
        for device in selected_devices:
            # Check if printer already exists with this MAC address
            existing = self.env['bluetooth.printer'].search([('mac_address', '=', device.mac_address)], limit=1)
            
            if existing:
                # Update existing record
                existing.write({
                    'name': device.name,
                    'bridge_url': self.bridge_url
                })
            else:
                # Create new printer record
                self.env['bluetooth.printer'].create({
                    'name': device.name,
                    'mac_address': device.mac_address,
                    'bridge_url': self.bridge_url,
                    'width_mm': 58,  # Default for SHREYANS printer
                    'is_default': self.device_count == 1  # Set as default if it's the only device
                })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Printers Added',
                'message': f'Added {len(selected_devices)} printer(s) successfully',
                'type': 'success',
            }
        }
