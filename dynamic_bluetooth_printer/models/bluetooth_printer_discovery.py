# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class BluetoothPrinterDiscovery(models.TransientModel):
    _name = 'bluetooth.printer.discovery'
    _description = 'Bluetooth Printer Discovery Wizard'

    bridge_url = fields.Char('Bridge URL', default=lambda self: self.env['ir.config_parameter'].sudo().get_param('bluetooth_printer.bridge_url', 'http://localhost:8000'))
    scan_message = fields.Text(string='Scan Status', readonly=True)
    discovered_printer_ids = fields.One2many(
        'bluetooth.printer.discovery.line', 'wizard_id', string='Discovered Printers')

    @api.model
    def create(self, vals):
        # Override create to automatically scan when the wizard is created
        record = super(BluetoothPrinterDiscovery, self).create(vals)
        # Perform scan immediately after creation
        record._do_scan()
        return record

    def _do_scan(self):
        """Internal method to perform the actual scan"""
        self.ensure_one()
        
        # Clear existing devices
        self.discovered_printer_ids.unlink()
        
        # Update message
        self.scan_message = _('Scanning for nearby Bluetooth printers...')
        
        # Perform scan
        try:
            response = requests.get(f"{self.bridge_url}/scan", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success' and result.get('devices'):
                    printers = result.get('devices', [])
                    
                    # Add discovered printers
                    for printer in printers:
                        self.env['bluetooth.printer.discovery.line'].create({
                            'wizard_id': self.id,
                            'name': printer.get('name', 'Unknown Device'),
                            'mac_address': printer.get('address'),
                        })
                    
                    self.scan_message = _('Found %s devices. Select a printer to add.') % len(printers)
                else:
                    self.scan_message = _('No printers found. Try scanning again.')
            else:
                self.scan_message = _(f'Error: {response.status_code} - {response.text}')
        except Exception as e:
            self.scan_message = _(f'Error scanning for printers: {str(e)}')
            _logger.error("Bluetooth scan error: %s", str(e))
    
    def action_scan(self):
        """Button handler to perform a new scan"""
        self.ensure_one()
        self._do_scan()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bluetooth.printer.discovery',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }
    
    def action_add_printer(self):
        """Add the selected printer"""
        self.ensure_one()
        
        selected_printers = self.discovered_printer_ids.filtered(lambda p: p.selected)
        if not selected_printers:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Selection'),
                    'message': _('Please select a printer to add.'),
                    'type': 'warning',
                }
            }
        
        # Check if the printer already exists
        existing = self.env['bluetooth.printer'].search([
            ('mac_address', '=', selected_printers[0].mac_address)
        ])
        
        if existing:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Printer Exists'),
                    'message': _(f'Printer {existing.name} with MAC {existing.mac_address} already exists.'),
                    'type': 'warning',
                }
            }
        
        # Create the new printer
        printer_values = {
            'name': selected_printers[0].name,
            'mac_address': selected_printers[0].mac_address,
            'bridge_url': self.bridge_url,
            'width_mm': 58,  # Default for common thermal printers
        }
        
        new_printer = self.env['bluetooth.printer'].create(printer_values)
        
        # Open the newly created printer record
        return {
            'name': _('Bluetooth Printer'),
            'type': 'ir.actions.act_window',
            'res_model': 'bluetooth.printer',
            'res_id': new_printer.id,
            'view_mode': 'form',
            'target': 'current',
        }


class BluetoothPrinterDiscoveryLine(models.TransientModel):
    _name = 'bluetooth.printer.discovery.line'
    _description = 'Discovered Bluetooth Printer'
    
    wizard_id = fields.Many2one('bluetooth.printer.discovery', string='Wizard')
    name = fields.Char('Printer Name')
    mac_address = fields.Char('MAC Address')
    selected = fields.Boolean('Selected', default=False)
