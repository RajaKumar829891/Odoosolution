from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class VehicleWorkOrderBarcodeWizard(models.TransientModel):
    _name = 'simply.vehicle.work.order.barcode.wizard'
    _description = 'Work Order Barcode Scanning Wizard'

    work_order_id = fields.Many2one('simply.vehicle.work.order', string='Work Order', required=True)
    barcode = fields.Char(string='Scan Barcode', help='Scan product barcode or enter last 4 digits')
    use_camera = fields.Boolean(string='Use Camera', default=True)
    
    scanned_parts_ids = fields.One2many('simply.vehicle.work.order.barcode.wizard.line', 
                                       'wizard_id', string='Scanned Parts')
    
    def _add_product_by_barcode(self, barcode):
        """Add a product by barcode to the work order"""
        PartLine = self.env['simply.vehicle.work.order.part.line']
        product = PartLine._find_product_by_barcode(barcode)
        
        if not product:
            return False
            
        # Check if product is already in the work order
        existing_line = self.work_order_id.part_line_ids.filtered(
            lambda l: l.product_id.id == product.id
        )
        
        if existing_line:
            # Increment quantity of existing line
            existing_line.write({'quantity': existing_line.quantity + 1})
            return existing_line
        else:
            # Create new part line in work order
            new_line = PartLine.create({
                'work_order_id': self.work_order_id.id,
                'product_id': product.id,
                'quantity': 1.0,
            })
            return new_line
    
    @api.onchange('barcode')
    def _onchange_barcode(self):
        if not self.barcode:
            return
            
        barcode = self.barcode.strip()
        result = self._add_product_by_barcode(barcode)
        
        if result:
            # Add to scanned parts list in wizard
            self.env['simply.vehicle.work.order.barcode.wizard.line'].create({
                'wizard_id': self.id,
                'product_id': result.product_id.id,
                'quantity': 1.0,
            })
            
            # Clear barcode field for next scan
            self.barcode = False
        else:
            return {
                'warning': {
                    'title': _('Warning'),
                    'message': _('No product found with this barcode/number: %s') % barcode
                }
            }
    
    def action_done(self):
        """Close wizard and return to work order"""
        return {'type': 'ir.actions.act_window_close'}
    
    def action_scan_more(self):
        """Refresh the wizard to scan more items"""
        return {
            'name': _('Scan Barcode'),
            'type': 'ir.actions.act_window',
            'res_model': 'simply.vehicle.work.order.barcode.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_work_order_id': self.work_order_id.id,
            },
        }

    
    def action_done(self):
        """Close wizard and return to work order"""
        return {'type': 'ir.actions.act_window_close'}
    
    def action_scan_more(self):
        """Refresh the wizard to scan more items"""
        return {
            'name': _('Scan Barcode'),
            'type': 'ir.actions.act_window',
            'res_model': 'simply.vehicle.work.order.barcode.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_work_order_id': self.work_order_id.id,
            },
        }


class VehicleWorkOrderBarcodeWizardLine(models.TransientModel):
    _name = 'simply.vehicle.work.order.barcode.wizard.line'
    _description = 'Work Order Barcode Wizard Line'
    
    wizard_id = fields.Many2one('simply.vehicle.work.order.barcode.wizard', 
                              string='Wizard', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    product_uom = fields.Many2one('uom.uom', related='product_id.uom_id', 
                                string='Unit of Measure')
