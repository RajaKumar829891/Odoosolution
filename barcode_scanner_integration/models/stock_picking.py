from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def process_barcode_from_ui(self, barcode):
        """Process barcode scanned from the UI"""
        try:
            if not barcode:
                return {'success': False, 'message': 'Empty barcode received'}

            # Search for product using barcode
            product = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)
            
            if not product:
                return {
                    'success': False,
                    'message': f'No product found with barcode {barcode}'
                }

            # Get active picking if in picking context
            active_picking = self.env.context.get('active_id')
            if active_picking:
                picking = self.browse(active_picking)
                
                # Find matching move line
                move_line = picking.move_line_ids.filtered(
                    lambda l: l.product_id.id == product.id and l.qty_done < l.product_uom_qty
                )

                if move_line:
                    # Update quantity done
                    move_line.write({
                        'qty_done': move_line.qty_done + 1
                    })
                    
                    return {
                        'success': True,
                        'message': f'Scanned {product.name} - Updated quantity'
                    }
                else:
                    return {
                        'success': False,
                        'message': f'No pending moves for product {product.name}'
                    }

            # If not in picking context, create inventory adjustment
            else:
                # Create inventory adjustment
                adjustment = self.env['stock.inventory'].create({
                    'name': f'Scan Adjustment - {fields.Datetime.now()}',
                    'product_ids': [(4, product.id)],
                    'location_ids': [(4, self.env.ref('stock.stock_location_stock').id)]
                })
                
                return {
                    'success': True,
                    'message': f'Created inventory adjustment for {product.name}',
                    'adjustment_id': adjustment.id
                }

        except Exception as e:
            _logger.error('Error processing barcode: %s', str(e))
            return {
                'success': False,
                'message': f'Error processing barcode: {str(e)}'
            }
