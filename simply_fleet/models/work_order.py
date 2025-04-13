from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class VehicleWorkOrder(models.Model):
    _name = 'simply.vehicle.work.order'
    _description = 'Vehicle Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Work Order Reference', required=True, copy=False, 
                      readonly=True, default='New', tracking=True)
    vehicle_id = fields.Many2one('simply.fleet.vehicle', string='Vehicle', 
                                required=True, tracking=True)
    inspection_id = fields.Many2one('simply.fleet.vehicle.inspection', 
                                   string='Related Inspection', tracking=True)
    date = fields.Date(string='Creation Date', default=fields.Date.today, 
                      required=True, tracking=True)
    scheduled_date = fields.Date(string='Scheduled Date', tracking=True)
    completion_date = fields.Date(string='Completion Date', tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Critical')
    ], string='Priority', default='1', tracking=True)
    
    work_order_line_ids = fields.One2many(
        'simply.vehicle.work.order.line',
        'work_order_id',
        string='Work Order Lines',
        copy=True
    )
    
    part_line_ids = fields.One2many(
        'simply.vehicle.work.order.part.line',
        'work_order_id',
        string='Parts Required',
        copy=True
    )
    
    technician_id = fields.Many2one('res.users', string='Assigned Technician', 
                                   tracking=True)
    
    labor_cost = fields.Float(string='Labor Cost', tracking=True)
    parts_cost = fields.Float(compute='_compute_parts_cost', store=True, 
                            string='Parts Cost')
    total_cost = fields.Float(compute='_compute_total_cost', store=True, 
                            string='Total Cost')
    
    location_id = fields.Many2one(
        'stock.location',
        string='Parts Source Location',
        domain=[('usage', '=', 'internal')],
        default=lambda self: self.env.ref('stock.stock_location_stock', raise_if_not_found=False),
        required=True
    )
    
    notes = fields.Text(string='Notes', tracking=True)
    document_ids = fields.Many2many(
        'ir.attachment',
        'vehicle_work_order_attachment_rel',
        'work_order_id',
        'attachment_id',
        string='Documents'
    )

    parts_transferred = fields.Boolean(string='Parts Transferred', default=False, tracking=True)
    parts_transfer_picking_ids = fields.Many2many(
        'stock.picking', 
        'work_order_parts_picking_rel', 
        'work_order_id', 
        'picking_id', 
        string='Parts Transfer Pickings'
    )

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'simply.vehicle.work.order'
            ) or 'New'
        return super(VehicleWorkOrder, self).create(vals)

    @api.depends('part_line_ids.subtotal')
    def _compute_parts_cost(self):
        for order in self:
            order.parts_cost = sum(order.part_line_ids.mapped('subtotal'))

    @api.depends('labor_cost', 'parts_cost')
    def _compute_total_cost(self):
        for order in self:
            order.total_cost = order.labor_cost + order.parts_cost

    def _get_internal_picking_type(self):
        """Find or create an internal transfer picking type"""
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id.company_id', '=', self.env.company.id)
        ], limit=1)
        
        if picking_type:
            return picking_type
        
        try:
            warehouse = self.env['stock.warehouse'].create({
                'name': 'Default Workshop Warehouse',
                'code': 'WS',
                'company_id': self.env.company.id
            })
            
            picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'internal'),
                ('warehouse_id', '=', warehouse.id)
            ], limit=1)
            
            return picking_type
        except Exception as e:
            _logger.error(f"Error creating warehouse or picking type: {e}")
            return False

    def _get_or_create_vehicle_location(self):
        """Create or get a specific stock location for the vehicle"""
        self.ensure_one()
        
        vehicle_location = self.env['stock.location'].search([
            ('name', '=', f'Vehicle - {self.vehicle_id.name}'),
            ('usage', '=', 'internal'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if vehicle_location:
            return vehicle_location
        
        parent_location = self.env.ref('stock.stock_location_locations', raise_if_not_found=False)
        if not parent_location:
            parent_location = self.env['stock.location'].search([
                ('name', '=', 'Physical Locations'),
                ('usage', '=', 'view')
            ], limit=1)
        
        vehicle_location = self.env['stock.location'].create({
            'name': f'Vehicle - {self.vehicle_id.name}',
            'usage': 'internal',
            'location_id': parent_location.id if parent_location else False,
            'company_id': self.env.company.id,
            'comment': f'Parts installed in vehicle {self.vehicle_id.name}'
        })
        
        return vehicle_location

    def action_confirm(self):
        """Confirm work order and transfer parts if available"""
        for order in self:
            if order.part_line_ids and not order.parts_transferred:
                order._transfer_parts()
            
            order.write({
                'state': 'confirmed',
                'parts_transferred': True
            })

    def _transfer_parts(self):
        """Internal method to transfer parts from inventory with proper stock updates"""
        self.ensure_one()
        
        picking_type = self._get_internal_picking_type()
        if not picking_type:
            raise UserError(_('Could not find or create an internal transfer operation type.'))
        
        destination_location = self._get_or_create_vehicle_location()
        if not destination_location:
            raise UserError(_('Could not create vehicle-specific location.'))
        
        picking_vals = {
            'picking_type_id': picking_type.id,
            'location_id': self.location_id.id,
            'location_dest_id': destination_location.id,
            'origin': f'{self.name} - {self.vehicle_id.name}',
            'immediate_transfer': True,
        }
        
        picking = self.env['stock.picking'].create(picking_vals)
        
        for part in self.part_line_ids:
            available_qty = part.product_id.with_context(location=self.location_id.id).qty_available
            
            if available_qty < part.quantity:
                raise UserError(_(
                    "Insufficient stock for part %s. Required: %s, Available: %s" % 
                    (part.product_id.name, part.quantity, available_qty)
                ))
            
            move_vals = {
                'name': f'{part.product_id.name} - {self.vehicle_id.name}',
                'product_id': part.product_id.id,
                'product_uom': part.product_uom.id,
                'product_uom_qty': part.quantity,
                'location_id': self.location_id.id,
                'location_dest_id': destination_location.id,
                'picking_id': picking.id,
                'state': 'draft',
            }
            
            move = self.env['stock.move'].create(move_vals)
            
            move_line_vals = {
                'move_id': move.id,
                'product_id': part.product_id.id,
                'product_uom_id': part.product_uom.id,
                'qty_done': part.quantity,
                'location_id': self.location_id.id,
                'location_dest_id': destination_location.id,
                'picking_id': picking.id,
            }
            
            self.env['stock.move.line'].create(move_line_vals)
        
        picking.action_confirm()
        picking.action_assign()
        
        picking.with_context(skip_backorder=True).button_validate()
        
        self.env['stock.quant']._merge_quants()
        self.env['stock.quant']._unlink_zero_quants()
        
        self.parts_transfer_picking_ids = [(4, picking.id)]
        
        return picking

    def _return_parts_to_inventory(self):
        """Return parts to original inventory location"""
        for order in self:
            if not order.parts_transferred or not order.parts_transfer_picking_ids:
                continue
            
            picking_type = self._get_internal_picking_type()
            
            if not picking_type:
                raise UserError(_('No internal transfer operation type found.'))
            
            vehicle_location = order._get_or_create_vehicle_location()
            
            for original_picking in order.parts_transfer_picking_ids:
                return_picking_vals = {
                    'picking_type_id': picking_type.id,
                    'location_id': vehicle_location.id,
                    'location_dest_id': self.location_id.id,
                    'origin': f'{self.name} - {self.vehicle_id.name} - Parts Return',
                    'immediate_transfer': True,
                }
                
                return_picking = self.env['stock.picking'].create(return_picking_vals)
                
                for move in original_picking.move_lines:
                    return_move_vals = {
                        'name': f'Return {move.product_id.name} from {self.vehicle_id.name}',
                        'product_id': move.product_id.id,
                        'product_uom': move.product_uom.id,
                        'product_uom_qty': move.product_uom_qty,
                        'location_id': vehicle_location.id,
                        'location_dest_id': self.location_id.id,
                        'picking_id': return_picking.id,
                        'state': 'draft',
                    }
                    
                    return_move = self.env['stock.move'].create(return_move_vals)
                    
                    move_line_vals = {
                        'move_id': return_move.id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_uom.id,
                        'qty_done': move.product_uom_qty,
                        'location_id': vehicle_location.id,
                        'location_dest_id': self.location_id.id,
                        'picking_id': return_picking.id,
                    }
                    
                    self.env['stock.move.line'].create(move_line_vals)
                
                return_picking.action_confirm()
                return_picking.action_assign()
                return_picking.with_context(skip_backorder=True).button_validate()

    def action_cancel(self):
        """Cancel work order and return parts to inventory"""
        for order in self:
            order._return_parts_to_inventory()
            
            order.write({
                'state': 'cancelled',
                'parts_transferred': False,
                'parts_transfer_picking_ids': [(5, 0, 0)]
            })

    def action_reset_to_draft(self):
        """Reset work order to draft and return parts to inventory"""
        for order in self:
            order._return_parts_to_inventory()
            
            order.write({
                'state': 'draft',
                'parts_transferred': False,
                'parts_transfer_picking_ids': [(5, 0, 0)]
            })

    def action_start(self):
        """Start the work order"""
        for order in self:
            vals = {
                'state': 'in_progress'
            }
            
            if order.work_order_line_ids:
                for line in order.work_order_line_ids:
                    if line.state == 'pending':
                        line.write({'state': 'in_progress'})
            
            order.write(vals)

    def action_complete(self):
        """Complete the work order and set completion date"""
        for order in self:
            vals = {
                'state': 'done',
                'completion_date': fields.Date.today()
            }
            
            if order.work_order_line_ids:
                for line in order.work_order_line_ids:
                    if line.state != 'cancelled':
                        line.write({
                            'state': 'done',
                            'completion_date': fields.Date.today()
                        })
            
            order.write(vals)

    def action_scan_barcode(self):
        """
        Open the barcode scanning interface for work orders
        This method combines functionality of the two existing barcode methods
        and supports both automatic scanner and manual entry
        """
        self.ensure_one()
        
        # Determine if we should show the automatic scanner or manual entry form
        # You can modify this condition based on your specific requirements
        return {
            'name': _('Scan Barcode'),
            'type': 'ir.actions.act_window',
            'res_model': 'simply.vehicle.work.order.barcode.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_work_order_id': self.id,
                'form_view_initial_mode': 'edit',
            },
        }

    def action_scan_part(self):
        """Open barcode scanning interface"""
        self.ensure_one()
        return {
            'name': _('Add Part by Barcode'),
            'type': 'ir.actions.act_window',
            'res_model': 'simply.vehicle.work.order.part.line',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_work_order_id': self.id,
                'form_view_initial_mode': 'edit',
            },
        }

    def action_manual_barcode_entry(self):
        """Open manual barcode entry wizard"""
        self.ensure_one()
        return {
            'name': _('Enter Part Barcode'),
            'type': 'ir.actions.act_window',
            'res_model': 'simply.vehicle.work.order.part.line',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_work_order_id': self.id,
                'form_view_initial_mode': 'edit',
                'manual_entry': True,
            },
        }

    @api.onchange('inspection_id')
    def _onchange_inspection(self):
        if self.inspection_id:
            self.vehicle_id = self.inspection_id.vehicle_id
            issue_lines = self.inspection_id.inspection_line_ids.filtered(
                lambda x: x.status in ['issue', 'critical']
            )
            if issue_lines:
                max_priority = max(issue_lines.mapped('priority'))
                self.priority = max_priority
            
            lines = []
            for insp_line in issue_lines:
                lines.append((0, 0, {
                    'name': insp_line.component,
                    'description': insp_line.description,
                    'recommended_action': insp_line.recommended_action,
                    'estimated_cost': insp_line.estimated_cost,
                    'priority': insp_line.priority,
                }))
            self.work_order_line_ids = lines


class VehicleWorkOrderLine(models.Model):
    _name = 'simply.vehicle.work.order.line'
    _description = 'Vehicle Work Order Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    work_order_id = fields.Many2one('simply.vehicle.work.order', string='Work Order', 
                                   required=True, ondelete='cascade')
    name = fields.Char(string='Task', required=True)
    description = fields.Text(string='Description')
    recommended_action = fields.Text(string='Recommended Action')
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Critical')
    ], string='Priority', default='1')
    
    estimated_cost = fields.Float(string='Estimated Cost')
    actual_cost = fields.Float(string='Actual Cost')
    
    state = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='pending')
    
    completion_date = fields.Date(string='Completion Date')
    technician_notes = fields.Text(string='Technician Notes')


class VehicleWorkOrderPartLine(models.Model):
    _name = 'simply.vehicle.work.order.part.line'
    _description = 'Vehicle Work Order Part Line'
    
    work_order_id = fields.Many2one('simply.vehicle.work.order', string='Work Order', 
                                   required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Part', 
                                required=True, domain=[('type', '=', 'product')])
    barcode = fields.Char(string='Barcode/Number', 
                         help='Scan product barcode or enter barcode number to add parts')
    description = fields.Text(string='Description')
    quantity = fields.Float(string='Quantity Required', default=1.0, required=True)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', 
                                 related='product_id.uom_id')
    unit_price = fields.Float(related='product_id.standard_price', string='Unit Price')
    subtotal = fields.Float(compute='_compute_subtotal', string='Subtotal', store=True)
    
    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

    def _find_product_by_barcode(self, barcode):
        """Find product using barcode with direct support for last 4 digits"""
        if not barcode:
            return False
        
        barcode = str(barcode).strip()
        _logger.info(f"Searching for product with input: '{barcode}'")
        
        # Special case: If exactly 4 digits are entered, use brute force approach
        if len(barcode) == 4 and barcode.isdigit():
            _logger.info(f"Trying brute force approach for 4-digit input: {barcode}")
            
            # Get all products with non-empty barcodes
            all_products = self.env['product.product'].search([('barcode', '!=', False)])
            _logger.info(f"Checking {len(all_products)} products for last 4 digits match")
            
            # Manual check for barcode ending with our digits
            for product in all_products:
                product_barcode = str(product.barcode).strip()
                if product_barcode.endswith(barcode):
                    _logger.info(f"Found match: Product {product.name} (ID: {product.id}) with barcode {product_barcode}")
                    return product
            
            # Try with default code too
            all_products_with_code = self.env['product.product'].search([('default_code', '!=', False)])
            for product in all_products_with_code:
                if product.default_code and str(product.default_code).strip().endswith(barcode):
                    _logger.info(f"Found match by default_code: {product.name}")
                    return product
                    
            _logger.warning(f"No match found for last 4 digits: {barcode}")
            return False
        
        # Standard searches for non-4-digit inputs
        domain = [
            '|', '|', '|',
            ('barcode', '=', barcode),
            ('default_code', '=', barcode),
            ('barcode', 'ilike', barcode),
            ('default_code', 'ilike', barcode)
        ]
        
        product = self.env['product.product'].search(domain, limit=1)
        if product:
            _logger.info(f"Found product by standard search: {product.name}")
        else:
            _logger.warning(f"No product found with input: {barcode}")
                
        return product

# work_orders.py update for the VehicleWorkOrderPartLine class

    @api.onchange('barcode')
    def _onchange_barcode(self):
        if not self.barcode:
            return
        
        product = self._find_product_by_barcode(self.barcode)
    
        if not product:
            self.barcode = False
            return {
                'warning': {
                    'title': _('Warning'),
                    'message': _('No product found with this barcode/number: %s') % self.barcode
                }
            }
    
    # Check if product is already in the work order
        existing_line = self.work_order_id.part_line_ids.filtered(
            lambda l: l.product_id.id == product.id and l.id != self._origin.id
        )
    
        if existing_line:
        # Increment quantity of existing line
            existing_line.quantity += 1
        # Clear current line for the next scan
            self.product_id = False
        else:
        # Set product in this line
            self.product_id = product.id
        
        # If this is a new entry (not editing an existing one),
        # we'll try to add another line to the parent work order
            if not self._origin.id and self.env.context.get('scan_mode', False):
            # Try to add a new line to the parent work order
                try:
                    self.work_order_id.write({
                        'part_line_ids': [(0, 0, {
                        'work_order_id': self.work_order_id.id,
                        })]
                    })
                except Exception as e:
                    _logger.error("Error creating new line: %s", e)
    
    # Clear barcode field for next scan
        self.barcode = False
    
    # Return a context to the client indicating we need to refresh the view
        return {
            'context': {'scan_mode': True}
        }
            
    @api.model
    def create(self, vals):
        """Override create to handle barcode entry during creation"""
        if vals.get('barcode') and not vals.get('product_id'):
            product = self._find_product_by_barcode(vals['barcode'])
            if product:
                vals['product_id'] = product.id
                vals['barcode'] = False  # Clear barcode after finding product
        return super(VehicleWorkOrderPartLine, self).create(vals)
    
    @api.model
    def test_barcode_search(self, barcode_input):
        """Test method to verify barcode search functionality
        Usage from developer console:
        self.env['simply.vehicle.work.order.part.line'].test_barcode_search('1234')
        """
        product = self._find_product_by_barcode(barcode_input)
        if product:
            return {
                'success': True,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'barcode': product.barcode,
                    'default_code': product.default_code,
                }
            }
        return {'success': False, 'input': barcode_input}
    
    @api.model
    def debug_barcode_data(self):
        """Debug method to inspect barcode data in products
        Usage: self.env['simply.vehicle.work.order.part.line'].debug_barcode_data()
        """
        products = self.env['product.product'].search([('barcode', '!=', False)], limit=100)
        results = []
        
        for product in products:
            results.append({
                'id': product.id,
                'name': product.name,
                'barcode': product.barcode,
                'barcode_type': type(product.barcode).__name__,
                'default_code': product.default_code,
                'last_4_digits': product.barcode[-4:] if product.barcode and len(product.barcode) >= 4 else None
            })
        
        _logger.info(f"Found {len(results)} products with barcodes")
        _logger.info(f"Sample barcodes: {results[:5] if results else 'None'}")
        
        return results


class VehicleInspection(models.Model):
    _inherit = 'simply.fleet.vehicle.inspection'

    work_order_ids = fields.One2many('simply.vehicle.work.order', 'inspection_id', 
                                    string='Work Orders')
    work_order_count = fields.Integer(compute='_compute_work_order_count')

    @api.depends('work_order_ids')
    def _compute_work_order_count(self):
        for record in self:
            record.work_order_count = len(record.work_order_ids)

    def action_create_work_order(self):
        """Create a work order from inspection"""
        self.ensure_one()
        
        if not self.inspection_line_ids.filtered(lambda x: x.status in ['issue', 'critical']):
            raise UserError(_('No issues found that require a work order.'))

        work_order = self.env['simply.vehicle.work.order'].create({
            'vehicle_id': self.vehicle_id.id,
            'inspection_id': self.id,
            'date': fields.Date.today(),
        })
        
        work_order._onchange_inspection()
        
        return {
            'name': _('Work Order'),
            'view_mode': 'form',
            'res_model': 'simply.vehicle.work.order',
            'res_id': work_order.id,
            'type': 'ir.actions.act_window',
        }

    def action_view_work_orders(self):
        """Smart button action to view related work orders"""
        self.ensure_one()
        return {
            'name': _('Work Orders'),
            'view_mode': 'tree,form',
            'res_model': 'simply.vehicle.work.order',
            'domain': [('inspection_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_inspection_id': self.id, 
                       'default_vehicle_id': self.vehicle_id.id}
        }
