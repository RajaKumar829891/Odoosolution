from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class BarcodeScanner(models.Model):
   _name = 'barcode.scanner'
   _description = 'Barcode Scanner'

   name = fields.Char('Name', required=True)
   barcode = fields.Char('Barcode', required=True)
   product_id = fields.Many2one('product.product', string='Product')
   timestamp = fields.Datetime('Scanned At', default=fields.Datetime.now)
   user_id = fields.Many2one('res.users', string='Scanned By', default=lambda self: self.env.user)
   
   @api.model
   def create_from_scan(self, barcode_data, work_order_id=None):
       """
       Create a new record from barcode scan
       If work_order_id is provided, add the product to the work order
       """
       try:
           # Handle the work_order_id type conversion safely
           if work_order_id and isinstance(work_order_id, str):
               try:
                   work_order_id = int(work_order_id)
               except ValueError:
                   _logger.error("Invalid work_order_id format: %s", work_order_id)
                   work_order_id = None
           
           # Search for product with exact barcode match
           product = self.env['product.product'].search([('barcode', '=', barcode_data)], limit=1)
           
           # If no product found with exact barcode, try last 4 digits
           if not product and barcode_data and len(barcode_data) == 4 and barcode_data.isdigit():
               _logger.info("Searching for product with last 4 digits: %s", barcode_data)
               all_products = self.env['product.product'].search([('barcode', '!=', False)])
               for prod in all_products:
                   if prod.barcode and str(prod.barcode).endswith(barcode_data):
                       product = prod
                       _logger.info("Found product by last 4 digits: %s (ID: %s)", prod.name, prod.id)
                       break
           
           # Create barcode scan record
           vals = {
               'name': product.name if product else f'Unknown ({barcode_data})',
               'barcode': barcode_data,
               'product_id': product.id if product else False,
           }
           record = self.create(vals)
           
           work_order_updated = False
           
           # If work_order_id is provided and valid, add the product to the work order
           if work_order_id and product:
               try:
                   work_order = self.env['simply.vehicle.work.order'].browse(work_order_id)
                   
                   if work_order.exists():
                       # Check if product already exists in the work order
                       existing_line = work_order.part_line_ids.filtered(
                           lambda l: l.product_id.id == product.id
                       )
                       
                       if existing_line:
                           # Update existing line
                           existing_line.write({
                               'quantity': existing_line.quantity + 1,
                           })
                           _logger.info("Updated existing line for product %s in work order %s", 
                                        product.name, work_order.name)
                       else:
                           # Create new line with all required fields
                           new_line = self.env['simply.vehicle.work.order.part.line'].create({
                               'work_order_id': work_order.id,
                               'product_id': product.id,
                               'barcode': barcode_data,  # Add barcode field
                               'quantity': 1,
                           })
                           _logger.info("Created new line for product %s in work order %s", 
                                        product.name, work_order.name)
                       
                       work_order_updated = True
                   else:
                       _logger.warning("Work order with ID %s does not exist", work_order_id)
               except Exception as e:
                   _logger.error("Error adding product to work order: %s", e)
           
           return {
               'id': record.id,
               'name': record.name,
               'barcode': record.barcode,
               'product_id': record.product_id.id if record.product_id else False,
               'product_name': record.product_id.name if record.product_id else False,
               'work_order_updated': work_order_updated,
           }
       
       except Exception as e:
           _logger.error("Error in create_from_scan: %s", e)
           # Return a minimal response instead of crashing
           return {
               'error': str(e),
               'barcode': barcode_data,
           }
