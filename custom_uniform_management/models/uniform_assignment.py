from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class UniformAssignmentLine(models.Model):
    _name = 'uniform.assignment.line'
    _description = 'Uniform Assignment Line'
    
    assignment_id = fields.Many2one('uniform.assignment', string='Assignment', required=True, ondelete='cascade')
    item_id = fields.Many2one('product.template', string='Uniform Item', required=True, 
                             domain=[('is_uniform', '=', True)])
    product_variant_id = fields.Many2one('product.product', string='Variant', required=True,
                                        domain="[('product_tmpl_id', '=', item_id)]")
    quantity = fields.Integer(string='Quantity', default=1, required=True)
    assignment_date = fields.Date(string='Assignment Date', default=fields.Date.today, required=True)
    return_date = fields.Date(string='Return Date')
    
    # Display attribute values for clarity in UI
    attribute_value_ids = fields.Many2many(related='product_variant_id.product_template_attribute_value_ids', 
                                           string='Attributes')
    
    @api.onchange('item_id')
    def _onchange_item_id(self):
        self.product_variant_id = False

class UniformAssignment(models.Model):
    _name = 'uniform.assignment'
    _description = 'Uniform Assignment'
    _order = 'assignment_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Reference', required=True, copy=False, 
                      readonly=True, default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    
    # For backward compatibility with the view
    uniform_item_id = fields.Many2one('product.template', string='Uniform Item', domain=[('is_uniform', '=', True)])
    uniform_type = fields.Selection(related='uniform_item_id.uniform_type', readonly=True)
    product_variant_id = fields.Many2one('product.product', string='Variant', 
                                         domain="[('product_tmpl_id', '=', uniform_item_id)]")
    quantity = fields.Integer(string='Quantity', default=1)
    
    # New fields for line items
    uniform_line_ids = fields.One2many('uniform.assignment.line', 'assignment_id', string='Uniform Items')
    
    assignment_date = fields.Date(string='Assignment Date', default=fields.Date.today, required=True, tracking=True)
    expected_return_date = fields.Date(string='Return Date', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assigned', 'Assigned'),
        ('partially_returned', 'Partially Returned'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    return_ids = fields.One2many('uniform.return', 'assignment_id', string='Returns')
    returned_quantity = fields.Integer(string='Returned Quantity', compute='_compute_returned_quantity', store=True)
    
    # Alias field for compatibility with the view
    returned_qty = fields.Integer(related='returned_quantity', string='Returned Qty')
    
    @api.depends('return_ids.return_line_ids.quantity')
    def _compute_returned_quantity(self):
        for record in self:
            # Calculate the total returned quantity from all return lines
            total_returned = 0
            for return_record in record.return_ids:
                if hasattr(return_record, 'return_line_ids'):
                    for line in return_record.return_line_ids:
                        total_returned += line.quantity
                else:
                    # For backwards compatibility with old returns that have direct quantity
                    total_returned += return_record.quantity if hasattr(return_record, 'quantity') else 0
            
            record.returned_quantity = total_returned
            
            # Update state based on returned quantity
            if record.returned_quantity == 0:
                if record.state == 'assigned':
                    pass  # Keep current state
            else:
                # Calculate total assigned quantity
                total_assigned = 0
                if record.uniform_line_ids:
                    total_assigned = sum(record.uniform_line_ids.mapped('quantity'))
                else:
                    total_assigned = record.quantity
                    
                if record.returned_quantity < total_assigned:
                    record.state = 'partially_returned'
                else:
                    record.state = 'returned'
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('uniform.assignment') or _('New')
        return super(UniformAssignment, self).create(vals)
    
    @api.constrains('quantity', 'product_variant_id')
    def _check_quantity_available(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than zero."))
            
            if record.state == 'draft' and record.product_variant_id:
                # Check available quantity from stock
                available = sum(self.env['stock.quant'].search([
                    ('product_id', '=', record.product_variant_id.id),
                    ('location_id.usage', '=', 'internal')
                ]).mapped('quantity'))
                
                if record.quantity > available:
                    raise ValidationError(_(
                        "Not enough quantity available for %s (%s). Only %s available."
                    ) % (record.uniform_item_id.name, record.product_variant_id.display_name, available))
    
    @api.onchange('uniform_item_id')
    def _onchange_uniform_item(self):
        self.product_variant_id = False
    
    def action_assign(self):
        for record in self:
            if record.state != 'draft':
                continue
                
            # Simple approach: directly update the stock quant quantities
            stock_location = self.env.ref('stock.stock_location_stock')
            
            # Handle line items
            if record.uniform_line_ids:
                for line in record.uniform_line_ids:
                    # Find quants for this product in stock location
                    quants = self.env['stock.quant'].search([
                        ('product_id', '=', line.product_variant_id.id),
                        ('location_id', '=', stock_location.id)
                    ])
                    
                    available = sum(quants.mapped('quantity'))
                    if available < line.quantity:
                        raise UserError(_("Not enough quantity available for %s (%s).") % 
                                        (line.item_id.name, line.product_variant_id.display_name))
                    
                    # Update quantities
                    qty_to_remove = line.quantity
                    for quant in quants:
                        if qty_to_remove <= 0:
                            break
                        
                        take_qty = min(quant.quantity, qty_to_remove)
                        if take_qty > 0:
                            quant.quantity -= take_qty
                            qty_to_remove -= take_qty
                    
            # Handle single item (old way)
            elif record.product_variant_id and record.quantity > 0:
                # Find quants for this product in stock location
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', record.product_variant_id.id),
                    ('location_id', '=', stock_location.id)
                ])
                
                available = sum(quants.mapped('quantity'))
                if available < record.quantity:
                    raise UserError(_("Not enough quantity available for %s (%s).") % 
                                   (record.uniform_item_id.name, record.product_variant_id.display_name))
                
                # Update quantities
                qty_to_remove = record.quantity
                for quant in quants:
                    if qty_to_remove <= 0:
                        break
                    
                    take_qty = min(quant.quantity, qty_to_remove)
                    if take_qty > 0:
                        quant.quantity -= take_qty
                        qty_to_remove -= take_qty
            
            # Update assignment state
            record.state = 'assigned'
    
    def action_cancel(self):
        for record in self:
            if record.state in ['draft', 'assigned', 'partially_returned']:
                # If already assigned, return to inventory
                if record.state in ['assigned', 'partially_returned']:
                    stock_location = self.env.ref('stock.stock_location_stock')
                    
                    if record.uniform_line_ids:
                        for line in record.uniform_line_ids:
                            # Calculate how many to return to inventory
                            returned = 0
                            for return_record in record.return_ids:
                                if hasattr(return_record, 'return_line_ids'):
                                    for return_line in return_record.return_line_ids:
                                        if (return_line.assignment_line_id and 
                                            return_line.assignment_line_id.id == line.id and
                                            return_line.condition == 'good'):
                                            returned += return_line.quantity
                                elif hasattr(return_record, 'line_id') and hasattr(return_record, 'condition'):
                                    if return_record.line_id.id == line.id and return_record.condition == 'good':
                                        returned += return_record.quantity
                            
                            to_return = line.quantity - returned
                            
                            if to_return > 0:
                                # Find or create a quant for this product
                                quant = self.env['stock.quant'].search([
                                    ('product_id', '=', line.product_variant_id.id),
                                    ('location_id', '=', stock_location.id)
                                ], limit=1)
                                
                                if quant:
                                    quant.quantity += to_return
                                else:
                                    self.env['stock.quant'].create({
                                        'product_id': line.product_variant_id.id,
                                        'location_id': stock_location.id,
                                        'quantity': to_return
                                    })
                    elif record.product_variant_id:
                        to_return = record.quantity - record.returned_quantity
                        
                        if to_return > 0:
                            # Find or create a quant for this product
                            quant = self.env['stock.quant'].search([
                                ('product_id', '=', record.product_variant_id.id),
                                ('location_id', '=', stock_location.id)
                            ], limit=1)
                            
                            if quant:
                                quant.quantity += to_return
                            else:
                                self.env['stock.quant'].create({
                                    'product_id': record.product_variant_id.id,
                                    'location_id': stock_location.id,
                                    'quantity': to_return
                                })
                        
                record.state = 'cancelled'
                
    def action_return(self):
        """
        Open a return wizard for this assignment
        """
        self.ensure_one()
        # Create a context with the current assignment
        ctx = {
            'default_assignment_id': self.id,
            'default_employee_id': self.employee_id.id,
        }
        
        # Return an action to open the uniform return form
        return {
            'name': _('Return Uniform'),
            'type': 'ir.actions.act_window',
            'res_model': 'uniform.return',
            'view_mode': 'form',
            'target': 'new',
            'context': ctx,
        }