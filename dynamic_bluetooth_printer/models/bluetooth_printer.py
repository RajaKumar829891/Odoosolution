from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
import json
import base64
import tempfile
from PIL import Image, ImageDraw, ImageFont
import io
import qrcode
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class BluetoothPrinter(models.Model):
    _name = 'bluetooth.printer'
    _description = 'Bluetooth Thermal Printer'

    name = fields.Char('Printer Name', required=True)
    mac_address = fields.Char('MAC Address', required=False)
    bridge_url = fields.Char('Bridge Service URL', required=True, 
                            default='http://localhost:8000',
                            help="URL of the Bluetooth bridge service")
    width_mm = fields.Integer('Width (mm)', default=58)
    last_connected = fields.Datetime('Last Connected', readonly=True)
    is_connected = fields.Boolean('Currently Connected', default=False, readonly=True)
    is_default = fields.Boolean('Default Printer', default=False)
    
    # MAC address constraint method has been removed
    
    @api.model
    def create(self, vals):
        if vals.get('is_default'):
            self.search([('is_default', '=', True)]).write({'is_default': False})
        return super(BluetoothPrinter, self).create(vals)
    
    def write(self, vals):
        if vals.get('is_default'):
            self.search([('is_default', '=', True), ('id', '!=', self.id)]).write({'is_default': False})
        return super(BluetoothPrinter, self).write(vals)
    
    def action_scan_printers(self):
        """Scan for available Bluetooth printers"""
        # Make sure to return the action directly
        return {
            'name': _('Discover Bluetooth Printers'),
            'type': 'ir.actions.act_window',
            'res_model': 'bluetooth.printer.discovery',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_bridge_url': self.bridge_url or self.env['ir.config_parameter'].sudo().get_param('bluetooth_printer.bridge_url', 'http://localhost:8000'),
                'no_mac_validation': True,
            },
        }
    
    @api.model
    def open_discovery_wizard(self):
        """Open the discovery wizard from list view action"""
        bridge_url = self.env['ir.config_parameter'].sudo().get_param('bluetooth_printer.bridge_url', 'http://localhost:8000')
        return {
            'name': _('Discover Bluetooth Printers'),
            'type': 'ir.actions.act_window',
            'res_model': 'bluetooth.printer.discovery',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_bridge_url': bridge_url,
                'no_mac_validation': True,
            },
        }
    
    def action_connect(self):
        """Connect to this printer"""
        try:
            response = requests.post(
                f"{self.bridge_url}/connect",
                json={'address': self.mac_address},
                timeout=5
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'success':
                # Update other printers to show they're not connected
                self.search([('id', '!=', self.id)]).write({'is_connected': False})
                
                # Update this printer's status
                self.write({
                    'is_connected': True,
                    'last_connected': fields.Datetime.now()
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connected'),
                        'message': _(f'Successfully connected to {self.name}'),
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Error'),
                        'message': _(result.get('message', 'Failed to connect to printer')),
                        'type': 'danger',
                    }
                }
        except Exception as e:
            _logger.error("Bluetooth connection error: %s", str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Error'),
                    'message': _(f'Failed to connect: {str(e)}'),
                    'type': 'danger',
                }
            }
    
    def action_disconnect(self):
        """Disconnect from this printer"""
        if not self.is_connected:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Not Connected'),
                    'message': _('This printer is not currently connected'),
                    'type': 'warning',
                }
            }
        
        try:
            response = requests.post(f"{self.bridge_url}/disconnect", timeout=5)
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'success':
                self.write({'is_connected': False})
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Disconnected'),
                        'message': _(f'Disconnected from {self.name}'),
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Error'),
                        'message': _(result.get('message', 'Failed to disconnect')),
                        'type': 'danger',
                    }
                }
        except Exception as e:
            _logger.error("Bluetooth disconnection error: %s", str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _(f'Failed to disconnect: {str(e)}'),
                    'type': 'danger',
                }
            }
    
    def print_test_label(self):
        """Print a test label to verify the printer is working"""
        if not self.is_connected:
            return self.action_connect()
        
        # Generate test label image
        width_px = int(self.width_mm * 8)  # Roughly 8 pixels per mm at 200 DPI
        img = Image.new('1', (width_px, 120), color=255)  # Binary image, white background
        draw = ImageDraw.Draw(img)
        
        # Add test text
        draw.text((10, 10), f"Test: {self.name}", fill=0)  # 0 = black
        draw.text((10, 40), "ODOO 17 Dynamic BT", fill=0)
        draw.text((10, 70), fields.Date.today().strftime('%Y-%m-%d'), fill=0)
        
        # Convert to printer commands for SHREYANS 58mm printer
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_bytes = buffer.getvalue()
        
        # Prepare printer commands
        commands = b'\x1B@'  # Initialize printer
        commands += b'\x1D\x76\x30\x00'  # Start bitmap mode
        commands += bytes([width_px & 0xff, (width_px >> 8) & 0xff])  # Width
        commands += bytes([120 & 0xff, (120 >> 8) & 0xff])  # Height
        commands += img_bytes  # Image data
        commands += b'\x0A\x0A\x0A'  # Line feeds
        commands += b'\x1D\x56\x42\x00'  # Cut paper
        
        # Send commands to printer
        try:
            response = requests.post(
                f"{self.bridge_url}/print",
                json={'data': base64.b64encode(commands).decode('utf-8')},
                timeout=5
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') == 'success':
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Test label sent to printer'),
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Print Error'),
                        'message': _(result.get('message', 'Failed to print test label')),
                        'type': 'danger',
                    }
                }
        except Exception as e:
            _logger.error("Test print error: %s", str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Print Error'),
                    'message': _(f'Failed to print: {str(e)}'),
                    'type': 'danger',
                }
            }
