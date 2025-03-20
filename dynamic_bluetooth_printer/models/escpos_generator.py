from odoo import models
import io

class ESCPOSGenerator:
    """Helper class to generate ESC/POS commands for thermal printers"""
    
    @staticmethod
    def initialize():
        """Initialize printer"""
        return b'\x1B@'
    
    @staticmethod
    def text(text, align='left'):
        """Add text with alignment"""
        # Set alignment
        if align == 'center':
            cmd = b'\x1B\x61\x01'
        elif align == 'right':
            cmd = b'\x1B\x61\x02'
        else:  # left
            cmd = b'\x1B\x61\x00'
            
        # Add text
        cmd += text.encode('utf-8')
        cmd += b'\x0A'  # Line feed
        return cmd
    
    @staticmethod
    def bold_on():
        """Enable bold text"""
        return b'\x1B\x45\x01'
    
    @staticmethod
    def bold_off():
        """Disable bold text"""
        return b'\x1B\x45\x00'
    
    @staticmethod
    def text_size(width_multiplier=1, height_multiplier=1):
        """Set text size"""
        # Size range is 1-8 for width and height
        width = max(1, min(8, width_multiplier))
        height = max(1, min(8, height_multiplier))
        
        # Calculate size byte
        size_byte = ((width - 1) << 4) | (height - 1)
        return b'\x1D\x21' + bytes([size_byte])
    
    @staticmethod
    def image(img, high_density=True):
        """Convert image to printer commands"""
        if img.mode != '1':
            img = img.convert('1')  # Convert to 1-bit black and white
            
        width, height = img.size
        
        # Start bitmap mode
        if high_density:
            mode = 0  # 8-dot high density
        else:
            mode = 1  # 8-dot double width
            
        cmd = b'\x1D\x76\x30' + bytes([mode])
        
        # Width bytes (width / 8 rounded up)
        width_bytes = (width + 7) // 8
        cmd += bytes([width_bytes & 0xff, (width_bytes >> 8) & 0xff])
        
        # Height
        cmd += bytes([height & 0xff, (height >> 8) & 0xff])
        
        # Image data
        for y in range(height):
            for x in range(0, width, 8):
                byte = 0
                for b in range(8):
                    if x + b < width:
                        # If pixel is black (0 in PIL but 1 in ESC/POS), set bit
                        if img.getpixel((x + b, y)) == 0:
                            byte |= (1 << (7 - b))
                cmd += bytes([byte])
                
        return cmd
    
    @staticmethod
    def barcode(data, type='CODE128', height=50, width=2, text_position='below'):
        """Print barcode"""
        # Barcode type selection
        barcode_types = {
            'UPC-A': 0,
            'UPC-E': 1,
            'EAN13': 2,
            'EAN8': 3,
            'CODE39': 4,
            'ITF': 5,
            'CODABAR': 6,
            'CODE128': 7
        }
        
        type_code = barcode_types.get(type, 7)  # Default to CODE128
        
        # Text position (0=none, 1=above, 2=below, 3=both)
        position_codes = {'none': 0, 'above': 1, 'below': 2, 'both': 3}
        position = position_codes.get(text_position, 2)
        
        # Create command
        cmd = b'\x1D\x68' + bytes([height])  # Set height
        cmd += b'\x1D\x77' + bytes([width])  # Set width (1-6)
        cmd += b'\x1D\x48' + bytes([position])  # Set text position
        cmd += b'\x1D\x6B' + bytes([type_code])  # Set barcode type
        
        # Add data and terminator if needed
        if type_code >= 0 and type_code <= 6:
            cmd += bytes([len(data)])
        
        cmd += data.encode('utf-8')
        
        if type_code >= 7:
            cmd += b'\x00'  # Data terminator for these types
            
        return cmd
    
    @staticmethod
    def qr_code(data, size=5):
        """Print QR code (for printers that support it)"""
        # QR code model (model 2)
        cmd = b'\x1D\x28\x6B\x04\x00\x31\x41\x32\x00'
        
        # QR code size (1-16)
        size = max(1, min(16, size))
        cmd += b'\x1D\x28\x6B\x03\x00\x31\x43' + bytes([size])
        
        # Error correction level (L=0, M=1, Q=2, H=3)
        cmd += b'\x1D\x28\x6B\x03\x00\x31\x45\x31'
        
        # Data length
        data_bytes = data.encode('utf-8')
        length = len(data_bytes) + 3
        cmd += b'\x1D\x28\x6B' + bytes([length & 0xff, (length >> 8) & 0xff, 0x31, 0x50, 0x30])
        
        # Data
        cmd += data_bytes
        
        # Print QR code
        cmd += b'\x1D\x28\x6B\x03\x00\x31\x51\x30'
        
        return cmd
    
    @staticmethod
    def cut(partial=False):
        """Cut paper"""
        if partial:
            return b'\x1D\x56\x01'  # Partial cut
        else:
            return b'\x1D\x56\x00'  # Full cut
    
    @staticmethod
    def paper_feed(lines=1):
        """Feed paper by lines"""
        return b'\x1B\x64' + bytes([lines])
    
    @staticmethod
    def status_check():
        """Request printer status"""
        return b'\x10\x04\x01'
    
    @staticmethod
    def open_cash_drawer():
        """Open cash drawer (if supported)"""
        return b'\x1B\x70\x00\x19\x19'
