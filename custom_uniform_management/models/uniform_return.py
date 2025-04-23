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
    line_id = fields.Many2one('uniform.assignment.line', string='Assignment Line',
                            domain="[('assignment_id', '=', assignment_id)]")
    employee_id = fields.Many2one(related='assignment_id.employee_id', store=True, readonly=True)
    
    # Fields for backward compatibility and single item returns
    uniform_item_id = fields.Many2one(related='assignment_id.uniform_item_id', store=True, readonly=True)
    product_variant_id = fields.Many2one(related='assignment_id.product_variant_id', 
                                        string='Product Variant', store=True, readonly=True)
    assigned_quantity = fields.Integer(related='assignment_id.quantity', string='Assigned Quantity')
    
    # Fields for line-based returns
    line_item_id = fields.Many2one(related='line_id.item_id', string='Line Item', store=True, readonly=True)
    line_variant_id = fields.Many2one(related='line_id.product_variant_id', 
                                     string='Line Variant', store=True, readonly=True)
    line_assigned_quantity = fields.Integer(related='line_id.quantity', string='Line Assigned Quantity')
    
    quantity = fields.Integer(string='Return Quantity', default=1, required=True, tracking=True)
    return_date = fields.Date(string='Return Date', default=fields.Date.today, required=True, tracking=True)
    condition = fields.Selection([
        ('good', 'Good'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost')
    ], string='Condition', default='good', required=True, tracking=True)
    reusable = fields.Boolean(string='Reusable', default=True, 
                             help="Whether the item can be reused and returned to inventory")
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    @api.onchange('condition')
    def _onchange_condition(self):
        if self.condition in ['damaged', 'lost']:
            self.reusable = False
        else:
            self.reusable = True
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('uniform.return') or _('New')
        
        # Create the record first
        result = super(UniformReturn, self).create(vals)
        
        # Update inventory only for reusable items
        if result.reusable:
            # Get the picking type for incoming moves
            picking_type_id = self.env['stock.picking.type'].search([
                ('code', '=', 'incoming'), 
                ('warehouse_id.company_id', '=', result.company_id.id)
            ], limit=1).id
            
            if not picking_type_id:
                raise UserError(_("No incoming picking type found for this company."))
            
            # Decide which product to return based on whether it's a line return or main return
            if result.line_id and result.line_variant_id:
                product_id = result.line_variant_id.id
                product_uom = result.line_variant_id.uom_id.id
                product_name = result.line_item_id.name
            elif result.product_variant_id:
                product_id = result.product_variant_id.id
                product_uom = result.product_variant_id.uom_id.id
                product_name = result.uniform_item_id.name
            else:
                raise UserError(_("Cannot determine which product variant to return."))
            
            # Create stock move for return to inventory
            self.env['stock.move'].create({
                'name': result.name + ': Return ' + product_name,
                'product_id': product_id,
                'product_uom_qty': result.quantity,
                'product_uom': product_uom,
                'picking_type_id': picking_type_id,
                'location_id': self.env.ref('stock.stock_location_customers').id,
                'location_dest_id': self.env.ref('stock.stock_location_stock').id,
                'state': 'done',
                'date': result.return_date,
            })
            
        return result
    
    @api.constrains('quantity', 'assignment_id', 'line_id')
    def _check_return_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Return quantity must be greater than zero."))
            
            # Check for line items or direct assignment
            if record.line_id:
                # Calculate how many items have already been returned for this line
                already_returned = sum(self.env['uniform.return'].search([
                    ('assignment_id', '=', record.assignment_id.id),
                    ('line_id', '=', record.line_id.id),
                    ('id', '!=', record.id)
                ]).mapped('quantity') or [0])
                
                if record.quantity + already_returned > record.line_assigned_quantity:
                    raise ValidationError(_("You cannot return more items than were assigned."))
            else:
                # Calculate how many items have already been returned
                already_returned = sum(self.env['uniform.return'].search([
                    ('assignment_id', '=', record.assignment_id.id),
                    ('id', '!=', record.id)
                ]).mapped('quantity') or [0])
                
                if record.quantity + already_returned > record.assigned_quantity:
                    raise ValidationError(_("You cannot return more items than were assigned."))