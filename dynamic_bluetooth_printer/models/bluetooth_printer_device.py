from odoo import models, fields, api

class BluetoothPrinterDevice(models.TransientModel):
    _name = 'bluetooth.printer.device'
    _description = 'Discovered Bluetooth Device'
    
    wizard_id = fields.Many2one('bluetooth.printer.scan.wizard', string='Scan Wizard')
    name = fields.Char('Device Name', required=True)
    mac_address = fields.Char('MAC Address', required=True)
    selected = fields.Boolean('Select')
