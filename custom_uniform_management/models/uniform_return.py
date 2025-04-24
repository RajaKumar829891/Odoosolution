from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class UniformReturn(models.Model):
    _name = 'uniform.return'
    _description = 'Uniform Return'
    _order = 'return_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Reference', required=True, copy=False, 
                      readonly=True, default=lambda self: _('New'))
    assignment_id = fields.Many2one('uniform.assignment', string='Assignment Reference', 
                                   required=True, tracking=True)
    return_line_ids = fields.One2many('uniform.return.line', 'return_id', string='Return Lines')
    employee_id = fields.Many2one(related='assignment_id.employee_id', store=True, readonly=True)
    return_date = fields.Date(string='Return Date', default=fields.Date.today, required=True, tracking=True)
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('uniform.return') or _('New')
        
        # Create the record first
        result = super(UniformReturn, self).create(vals)
        
        # Process the return lines to update assignment state
        assignment = result.assignment_id
        assignment_lines = assignment.uniform_line_ids
        
        # Calculate how many items of each variant have been returned in total
        returned_items = {}
        for return_record in assignment.return_ids:
            for return_line in return_record.return_line_ids:
                key = (return_line.assignment_line_id.id if return_line.assignment_line_id else 0, 
                       return_line.product_variant_id.id)
                returned_items[key] = returned_items.get(key, 0) + return_line.quantity
        
        # Check if all assigned items have been returned
        all_returned = True
        if assignment_lines:
            for line in assignment_lines:
                key = (line.id, line.product_variant_id.id)
                returned_qty = returned_items.get(key, 0)
                if returned_qty < line.quantity:
                    all_returned = False
                    break
        else:
            # Check the main assignment (old way)
            key = (0, assignment.product_variant_id.id)
            returned_qty = returned_items.get(key, 0)
            if returned_qty < assignment.quantity:
                all_returned = False
        
        # Update the assignment state
        if all_returned:
            assignment.state = 'returned'
        else:
            assignment.state = 'partially_returned'
        
        # Update inventory for reusable items
        for return_line in result.return_line_ids:
            if return_line.reusable:
                # Get the stock location
                stock_location = self.env.ref('stock.stock_location_stock')
                
                # Find or create quant for this product
                quant = self.env['stock.quant'].search([
                    ('product_id', '=', return_line.product_variant_id.id),
                    ('location_id', '=', stock_location.id)
                ], limit=1)
                
                if quant:
                    quant.quantity += return_line.quantity
                else:
                    self.env['stock.quant'].create({
                        'product_id': return_line.product_variant_id.id,
                        'location_id': stock_location.id,
                        'quantity': return_line.quantity
                    })
        
        return result


class UniformReturnLine(models.Model):
    _name = 'uniform.return.line'
    _description = 'Uniform Return Line'
    
    return_id = fields.Many2one('uniform.return', string='Return', required=True, ondelete='cascade')
    assignment_line_id = fields.Many2one('uniform.assignment.line', string='Assignment Line',
                                      domain="[('assignment_id', '=', parent.assignment_id)]")
    product_variant_id = fields.Many2one('product.product', string='Product Variant', required=True)
    quantity = fields.Integer(string='Return Quantity', default=1, required=True)
    condition = fields.Selection([
        ('good', 'Good'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost')
    ], string='Condition', default='good', required=True)
    reusable = fields.Boolean(string='Reusable', default=True, 
                             help="Whether the item can be reused and returned to inventory")
    notes = fields.Text(string='Notes')
    
    @api.onchange('condition')
    def _onchange_condition(self):
        if self.condition in ['damaged', 'lost']:
            self.reusable = False
        else:
            self.reusable = True
    
    @api.onchange('assignment_line_id')
    def _onchange_assignment_line_id(self):
        if self.assignment_line_id:
            self.product_variant_id = self.assignment_line_id.product_variant_id
    
    @api.constrains('quantity', 'assignment_line_id', 'product_variant_id')
    def _check_return_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Return quantity must be greater than zero."))
            
            # Get assignment and calculate already returned quantities
            assignment = record.return_id.assignment_id
            
            # Calculate how many items have already been returned
            returned_qty = 0
            domain = [
                ('return_id.assignment_id', '=', assignment.id),
                ('product_variant_id', '=', record.product_variant_id.id),
                ('id', '!=', record.id)
            ]
            
            if record.assignment_line_id:
                domain.append(('assignment_line_id', '=', record.assignment_line_id.id))
                assigned_qty = record.assignment_line_id.quantity
            else:
                # This is for the main assignment record (old way)
                assigned_qty = assignment.quantity
                
            returned_lines = self.search(domain)
            for r_line in returned_lines:
                returned_qty += r_line.quantity
            
            # Check if returning more than assigned
            if record.quantity + returned_qty > assigned_qty:
                if record.assignment_line_id:
                    item_name = record.assignment_line_id.item_id.name
                else:
                    item_name = assignment.uniform_item_id.name
                
                raise ValidationError(_(
                    "You cannot return more than what was assigned for %(item)s. "
                    "Assigned: %(assigned)s, Already returned: %(returned)s, Attempting to return: %(returning)s",
                    item=item_name,
                    assigned=assigned_qty,
                    returned=returned_qty,
                    returning=record.quantity
                ))
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