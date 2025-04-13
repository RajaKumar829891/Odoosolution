from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class BarcodeController(http.Controller):
    
    @http.route('/barcode/scanner', type='http', auth='user', website=True)
    def barcode_scanner_page(self, work_order_id=None, **kwargs):
        """
        Render the barcode scanner page
        """
        return request.render('my_barcode_scanner.scanner_template', {
            'work_order_id': work_order_id,
        })
    
    @http.route('/barcode/redirect', type='http', auth="user")
    def redirect_after_scan(self, work_order_id=None, barcode=None, **kw):
        """
        Process barcode and redirect to work order form
        """
        if not work_order_id or not barcode:
            return request.redirect('/web')
        
        try:
            # Convert to integer
            work_order_id = int(work_order_id)
            
            # Find the work order
            work_order = request.env['simply.vehicle.work.order'].sudo().browse(work_order_id)
            
            if not work_order.exists():
                _logger.error(f"Work order {work_order_id} not found")
                return request.redirect('/web')
            
            # Process barcode with the work order method
            success = work_order.with_context(barcode=barcode).action_process_barcode(barcode)
            _logger.info(f"Barcode processing result: {success}")
            
            # Redirect directly to the work order form view
            # We'll add a timestamp parameter to force page refresh
            import time
            timestamp = int(time.time())
            return request.redirect(f'/web#id={work_order_id}&model=simply.vehicle.work.order&view_type=form&t={timestamp}')
        
        except Exception as e:
            _logger.error(f"Error in barcode redirect: {str(e)}")
            return request.redirect('/web')
    
    @http.route('/barcode/scan', type='json', auth='user')
    def scan_barcode(self, barcode_data, work_order_id=None):
        """
        Process barcode scan from mobile device
        """
        try:
            # Find product
            product = request.env['product.product'].sudo().search([
                '|', 
                ('barcode', '=', barcode_data),
                ('default_code', '=', barcode_data)
            ], limit=1)
            
            result = {
                'barcode': barcode_data,
                'product_name': product.name if product else 'Not Found',
                'product_id': product.id if product else False,
                'work_order_updated': False
            }
            
            # If work order ID is provided, process barcode
            if work_order_id and product:
                try:
                    work_order = request.env['simply.vehicle.work.order'].sudo().browse(int(work_order_id))
                    
                    if work_order.exists():
                        # Process barcode with the work order method
                        work_order.with_context(barcode=barcode_data).action_process_barcode(barcode_data)
                        request.env.cr.commit()  # Commit the transaction to make changes visible
                        result['work_order_updated'] = True
                except Exception as e:
                    _logger.error(f"Error processing work order update: {str(e)}")
                    result['error'] = str(e)
            
            return result
        
        except Exception as e:
            _logger.error(f"Barcode scan error: {str(e)}")
            return {
                'error': str(e),
                'barcode': barcode_data
            }
