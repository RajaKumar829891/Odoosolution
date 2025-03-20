from odoo import models, fields, api
import requests
import json
import base64
import tempfile
from PIL import Image, ImageDraw, ImageFont
import io
import qrcode
import logging

_logger = logging.getLogger(__name__)

class PrintLabelWizard(models.TransientModel):
    _name = 'print.label.wizard'
    _description = 'Print Product Labels'
    
    printer_id = fields.Many2one('bluetooth.printer', string='Printer', required=True)
    quantity = fields.Integer('Quantity', default=1)
    include_price = fields.Boolean('Include Price', default=True)
    include_barcode = fields.Boolean('Include Barcode/QR', default=True)
    scan_before_print = fields.Boolean('Scan for Printers', default=False,
                                    help="Scan for available Bluetooth printers before printing")
    
    @api.model
    def default_get(self, fields):
        res = super(PrintLabelWizard, self).default_get(fields)
        default_printer = self.env['bluetooth.printer'].search([('is_default', '=', True)], limit=1)
        if default_printer:
            res['printer_id'] = default_printer.id
        return res
    
    def action_scan_printer(self):
        """Scan for printers before printing"""
        # Trigger scan in printer model
        return self.env['bluetooth.printer'].action_scan_printers()
    
    def action_print_labels(self):
        """Print labels for selected products"""
        # If scan_before_print is enabled, scan for printers first
        if self.scan_before_print:
            return self.action_scan_printer()
        
        # Check if printer is connected, connect if not
        if not self.printer_id.is_connected:
            connect_result = self.printer_id.action_connect()
            # If connection failed, return the error
            if connect_result.get('params', {}).get('type') != 'success':
                return connect_result
        
        active_ids = self.env.context.get('active_ids', [])
        products = self.env['product.product'].browse(active_ids)
        
        success_count = 0
        failed_count = 0
        
        for product in products:
            for _ in range(self.quantity):
                if self._print_product_label(product):
                    success_count += 1
                else:
                    failed_count += 1
        
        if failed_count > 0:
            message = f'Printed {success_count} labels, {failed_count} failed'
            msg_type = 'warning'
        else:
            message = f'Successfully printed {success_count} labels'
            msg_type = 'success'
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Print Results',
                'message': message,
                'type': msg_type,
                'sticky': False,
            }
        }
    
    def _print_product_label(self, product):
        """Generate and print a label for a specific product"""
        printer = self.printer_id
        width_px = int(printer.width_mm * 8)  # Roughly 8 pixels per mm at 200 DPI
        
        # Calculate height based on content
        height_px = 120  # Default height
        if self.include_barcode and product.barcode:
            height_px += 100  # Add space for barcode
            
        # Create the label image
        img = Image.new('1', (width_px, height_px), color=255)  # Binary image, white background
        draw = ImageDraw.Draw(img)
        
        # Add product name
        name = product.name[:20] if len(product.name) > 20 else product.name
        draw.text((10, 10), name, fill=0)
        
        # Add product code/reference
        if product.default_code:
            draw.text((10, 30), f"Ref: {product.default_code}", fill=0)
            
        y_pos = 50
        
        # Add price if requested
        if self.include_price:
            currency = product.currency_id.symbol or '€'
            price_str = f"Price: {currency}{product.list_price:.2f}"
            draw.text((10, y_pos), price_str, fill=0)
            y_pos += 20
        
        # Add barcode if requested
        if self.include_barcode and product.barcode:
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=2, border=1)
            qr.add_data(product.barcode)
            qr.make(fit=True)
            qr_img = qr.make_image(fill='black', back_color='white')
            
            # Resize and paste QR code onto the label
            qr_width = min(80, width_px - 20)
            qr_img = qr_img.resize((qr_width, qr_width))
            img.paste(qr_img, (10, y_pos))
            
            # Add barcode text
            draw.text((10, y_pos + qr_width + 5), product.barcode, fill=0)
        
        # Convert to printer commands for SHREYANS 58mm printer
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_bytes = buffer.getvalue()
        
        # Prepare printer commands
        commands = b'\x1B@'  # Initialize printer
        commands += b'\x1D\x76\x30\x00'  # Start bitmap mode
        commands += bytes([width_px & 0xff, (width_px >> 8) & 0xff])  # Width
        commands += bytes([height_px & 0xff, (height_px >> 8) & 0xff])  # Height
        commands += img_bytes  # Image data
        commands += b'\x0A\x0A\x0A'  # Line feeds
        commands += b'\x1D\x56\x42\x00'  # Cut paper
        
        # Send commands to printer
        try:
            response = requests.post(
                f"{printer.bridge_url}/print",
                json={'data': base64.b64encode(commands).decode('utf-8')},
                timeout=5
            )
            response.raise_for_status()
            result = response.json()
            
            return result.get('status') == 'success'
        except Exception as e:
            _logger.error("Print error: %s", str(e))
            return False
