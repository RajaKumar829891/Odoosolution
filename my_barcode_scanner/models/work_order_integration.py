from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VehicleWorkOrderInherit(models.Model):
    _inherit = 'simply.vehicle.work.order'
    
    # Optional: Add a field to track recent barcodes if needed
    recent_barcode = fields.Char(string='Recent Barcode', store=False)
    
    def _find_product_by_barcode(self, barcode):
        """
        Find product by barcode with multiple lookup strategies
        """
        # Try exact barcode match
        product = self.env['product.product'].search([
            '|', 
            ('barcode', '=', barcode),
            ('default_code', '=', barcode)
        ], limit=1)
        
        # If no exact match, try partial match (last 4 digits)
        if not product and len(barcode) >= 4:
            product = self.env['product.product'].search([
                '|',
                ('barcode', 'like', '%' + barcode[-4:]),
                ('default_code', 'like', '%' + barcode[-4:])
            ], limit=1)
        
        return product
    
    def _process_barcode(self, barcode):
        """
        Process barcode and add product to parts required
        """
        self.ensure_one()
        
        if not barcode:
            raise UserError(_("No barcode provided to process"))
            
        # Find product by barcode
        product = self._find_product_by_barcode(barcode)
        
        if not product:
            raise UserError(_(f"No product found with barcode {barcode}"))
        
        # Check if work order is in a state that allows adding parts
        if self.state in ['done', 'cancelled']:
            raise UserError(_("Cannot add parts to a completed or cancelled work order"))
            
        # Get the part line model based on your existing structure
        # Make sure this matches your actual model name!
        part_line_model = self.env['simply.vehicle.work.order.part.line']
        
        # Check for existing part line
        existing_line = part_line_model.search([
            ('work_order_id', '=', self.id),
            ('product_id', '=', product.id)
        ], limit=1)
        
        try:
            if existing_line:
                # Update existing line - increment quantity
                existing_line.write({
                    'quantity': existing_line.quantity + 1
                })
                _logger.info(f"Updated quantity for product {product.name} in work order {self.id}")
            else:
                # Create new part line
                vals = {
                    'work_order_id': self.id,
                    'product_id': product.id,
                    'name': product.name or product.display_name,
                    'quantity': 1,
                    'barcode': barcode,
                }
                
                # Add additional fields if they exist in your model
                if hasattr(product, 'uom_id') and product.uom_id:
                    vals['uom_id'] = product.uom_id.id
                
                if hasattr(product, 'lst_price'):
                    vals['price_unit'] = product.lst_price
                
                new_line = part_line_model.create(vals)
                _logger.info(f"Added product {product.name} to work order {self.id}")
            
            # Update recent barcode (optional)
            self.recent_barcode = barcode
            
            return True
        
        except Exception as e:
            # Log the error and raise a user-friendly message
            _logger.error(f"Error processing barcode: {str(e)}")
            self.env.cr.rollback()
            raise UserError(_(f"Error processing barcode: {str(e)}"))
    
    @api.model
    def create(self, vals):
        """
        Override create to handle barcode parameter
        """
        # Create the record first
        res = super(VehicleWorkOrderInherit, self).create(vals)
        
        # Check if barcode is passed in context
        context = self.env.context
        if context.get('barcode'):
            try:
                res.with_context(barcode=context.get('barcode'))._process_barcode(context.get('barcode'))
            except Exception as e:
                # Log the error but don't prevent record creation
                _logger.error(f"Error processing barcode during work order creation: {str(e)}")
        
        return res
    
    def write(self, vals):
        """
        Override write to handle barcode parameter
        """
        # Perform the write operation
        res = super(VehicleWorkOrderInherit, self).write(vals)
        
        # Check if barcode is passed in context
        context = self.env.context
        if context.get('barcode'):
            for record in self:
                try:
                    record.with_context(barcode=context.get('barcode'))._process_barcode(context.get('barcode'))
                except Exception as e:
                    # Log the error but don't prevent write operation
                    _logger.error(f"Error processing barcode during work order update: {str(e)}")
        
        return res
    
    def action_process_barcode(self, barcode):
        """
        Public method to process barcode from UI
        """
        self.ensure_one()
        try:
            result = self._process_barcode(barcode)
            # Force refresh the view
            self.env.cr.commit()
            return result
        except Exception as e:
            _logger.error(f"Error in action_process_barcode: {str(e)}")
            return False
    
    def action_open_mobile_scanner(self):
        """
        Open the mobile barcode scanner interface
        """
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/barcode/scanner?work_order_id={self.id}',
            'target': 'self',
        }
    
    @api.constrains('part_line_ids')
    def _check_part_line_quantity(self):
        """
        Optional: Add constraints to part line quantities
        """
        for order in self:
            for line in order.part_line_ids:
                if line.quantity <= 0:
                    raise ValidationError(_("Part line quantity must be positive"))
                    
class VehicleWorkOrderPartLine(models.Model):
    _name = 'simply.vehicle.work.order.part.line'
    _description = 'Vehicle Work Order Part Line'
    
    work_order_id = fields.Many2one('simply.vehicle.work.order', string='Work Order', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    name = fields.Char(string='Description', required=True)
    barcode = fields.Char(string='Barcode/Number')
    quantity = fields.Float(string='Quantity', default=1.0)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    price_unit = fields.Float(string='Unit Price', default=0.0)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    
    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit
