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
    
    @api.depends('return_ids.quantity')
    def _compute_returned_quantity(self):
        for record in self:
            record.returned_quantity = sum(record.return_ids.mapped('quantity') or [0])
            if record.returned_quantity == 0:
                if record.state == 'assigned':
                    pass  # Keep current state
            elif record.returned_quantity < record.quantity:
                record.state = 'partially_returned'
            elif record.returned_quantity >= record.quantity:
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
                            returned = sum(self.env['uniform.return'].search([
                                ('assignment_id', '=', record.id),
                                ('line_id', '=', line.id),
                                ('condition', '=', 'good')
                            ]).mapped('quantity') or [0])
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
